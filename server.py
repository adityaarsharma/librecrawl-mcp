#!/usr/bin/env python3
"""
LibreCrawl MCP Server
Wraps LibreCrawl REST API as Claude MCP tools for full-site SEO auditing.
Source: https://github.com/adityaarsharma/librecrawl-mcp
"""

import os
import json
import time
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("librecrawl-mcp")

BASE            = f"http://127.0.0.1:{os.getenv('LIBRECRAWL_PORT', '5080')}"
MCP_PORT        = int(os.getenv('MCP_PORT', '5081'))
REPORTS_DIR     = Path(os.getenv('REPORTS_DIR', Path.home() / 'librecrawl-reports'))
PSI_API_KEY     = os.getenv('PAGESPEED_API_KEY', '')   # Google PageSpeed Insights
PSI_API_BASE    = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

# Fields we request on every export — links_detailed enables broken-link-source tracking
EXPORT_FIELDS = [
    "url", "status_code", "title", "meta_description", "h1",
    "word_count", "canonical_url", "depth", "issues_detected",
    "response_time_ms", "links_detailed",
]

_client = None


# ── HTTP client ───────────────────────────────────────────────────────────────

def get_client():
    """Return authenticated httpx.Client. Re-auths automatically on 401."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.Client(timeout=30, follow_redirects=True)
        _client.post(f"{BASE}/api/login", json={"username": "mcp-user"}).raise_for_status()
    return _client


def call(method, path, **kwargs):
    global _client
    r = get_client().request(method, f"{BASE}{path}", **kwargs)
    if r.status_code == 401:
        _client = None
        r = get_client().request(method, f"{BASE}{path}", **kwargs)
    r.raise_for_status()
    return r.json()


# ── Site-level checks (robots, sitemap, HTTPS, www) ──────────────────────────

def _site_check(base_url: str) -> dict:
    """Fetch robots.txt, sitemap.xml, and check redirect behaviour."""
    parsed   = urlparse(base_url)
    scheme   = parsed.scheme or "https"
    host     = parsed.netloc or parsed.path.rstrip("/")
    root     = f"{scheme}://{host}"
    results  = {}

    # ── robots.txt ────────────────────────────────────────────────────────────
    try:
        r = httpx.get(f"{root}/robots.txt", timeout=10, follow_redirects=True)
        if r.status_code == 200:
            txt      = r.text
            lines    = txt.splitlines()
            disallow = [l.split(":",1)[1].strip() for l in lines
                        if l.lower().startswith("disallow:") and l.split(":",1)[1].strip()]
            sitemaps = [l.split(":",1)[1].strip() for l in lines
                        if l.lower().startswith("sitemap:")]
            crawl_delay = next(
                (l.split(":",1)[1].strip() for l in lines if l.lower().startswith("crawl-delay:")),
                None
            )
            # Check if important paths are blocked
            important_blocked = [d for d in disallow if d in ("/", "/wp-admin", "/wp-login.php")
                                  or not d.startswith("/wp-")]
            results["robots_txt"] = {
                "found": True,
                "disallow_count": len(disallow),
                "disallow_rules": disallow[:20],
                "important_blocked": important_blocked,
                "sitemap_declared": sitemaps,
                "crawl_delay": crawl_delay,
                "raw_preview": txt[:500],
            }
        else:
            results["robots_txt"] = {"found": False, "status": r.status_code,
                                      "warning": "robots.txt missing — Googlebot has no crawl guidance."}
    except Exception as e:
        results["robots_txt"] = {"error": str(e)}

    # ── sitemap.xml ───────────────────────────────────────────────────────────
    sitemap_urls_to_try = [f"{root}/sitemap.xml", f"{root}/sitemap_index.xml",
                            f"{root}/sitemap-index.xml"]
    # also try any declared in robots
    sitemap_urls_to_try += results.get("robots_txt", {}).get("sitemap_declared", [])

    sitemap_found = False
    for sm_url in sitemap_urls_to_try:
        try:
            r = httpx.get(sm_url, timeout=15, follow_redirects=True)
            if r.status_code == 200 and ("<urlset" in r.text or "<sitemapindex" in r.text):
                url_count = r.text.count("<loc>")
                is_index  = "<sitemapindex" in r.text
                child_sitemaps = re.findall(r"<loc>(.*?)</loc>", r.text) if is_index else []
                results["sitemap"] = {
                    "found": True,
                    "url": sm_url,
                    "is_index": is_index,
                    "url_count": url_count,
                    "child_sitemaps": child_sitemaps[:10],
                }
                sitemap_found = True
                break
        except Exception:
            pass
    if not sitemap_found:
        results["sitemap"] = {
            "found": False,
            "warning": "No sitemap.xml found. Submit one to GSC to improve indexing.",
        }

    # ── HTTPS redirect ────────────────────────────────────────────────────────
    if scheme == "https":
        try:
            http_url = f"http://{host}/"
            r = httpx.get(http_url, timeout=10, follow_redirects=False)
            if r.status_code in (301, 302, 307, 308):
                loc = r.headers.get("location", "")
                results["https_redirect"] = {
                    "http_redirects_to_https": loc.startswith("https://"),
                    "redirect_code": r.status_code,
                    "location": loc,
                    "permanent": r.status_code in (301, 308),
                }
            else:
                results["https_redirect"] = {
                    "http_redirects_to_https": False,
                    "warning": f"http:// returns {r.status_code} without redirect — mixed content risk.",
                }
        except Exception as e:
            results["https_redirect"] = {"error": str(e)}

    # ── www vs non-www ────────────────────────────────────────────────────────
    try:
        is_www = host.startswith("www.")
        alt_host = host[4:] if is_www else f"www.{host}"
        r = httpx.get(f"{scheme}://{alt_host}/", timeout=10, follow_redirects=False)
        redirects_to_canonical = r.status_code in (301, 302, 307, 308)
        results["www_redirect"] = {
            "canonical_host": host,
            "alt_host": alt_host,
            "alt_redirects_properly": redirects_to_canonical,
            "alt_status": r.status_code,
            "warning": None if redirects_to_canonical else
                f"{scheme}://{alt_host}/ does not redirect to canonical host — duplicate content risk.",
        }
    except Exception as e:
        results["www_redirect"] = {"note": str(e)}

    return results


# ── Report generator ──────────────────────────────────────────────────────────

def _build_report(pages: list, base_url: str, crawl_id: int,
                  site_data: dict = None) -> str:
    """Generate a structured Markdown SEO audit report from crawl export data."""

    domain = base_url.replace("https://", "").replace("http://", "").rstrip("/")
    now    = datetime.now().strftime("%Y-%m-%d %H:%M")
    total  = len(pages)

    parsed_base = urlparse(base_url)
    base_host   = parsed_base.netloc or domain

    # ── Build reverse link map (source of broken links) ──────────────────────
    # links_detailed: list of {url, anchor_text, is_internal, ...} per page
    inbound = defaultdict(list)   # target_url → [source_urls]
    for p in pages:
        src   = p.get("url", "")
        links = p.get("links_detailed") or []
        if isinstance(links, list):
            for lk in links:
                tgt = lk.get("url") or lk.get("href") or ""
                if tgt:
                    inbound[tgt].append(src)

    # ── Categorise pages ──────────────────────────────────────────────────────
    status_buckets   = defaultdict(list)
    missing_title    = []
    missing_meta     = []
    missing_h1       = []
    long_title       = []
    short_title      = []
    long_meta        = []      # >160 chars
    short_meta       = []      # 1–70 chars
    thin_content     = []
    dup_titles       = defaultdict(list)
    dup_metas        = defaultdict(list)
    slow_pages       = []
    no_canonical     = []      # missing canonical tag
    self_canonical   = []      # canonical == self (good, just counted)
    non_self_canonical = []    # canonical points elsewhere
    bad_canonical    = []      # canonical points to broken URL
    uppercase_urls   = []
    long_urls        = []      # >115 chars
    deep_pages       = []      # depth > 4
    h1_title_mismatch = []     # H1 and title share 0 words
    url_params_heavy = []      # >3 query params
    issues_type_count = defaultdict(int)

    for p in pages:
        url       = p.get("url", "")
        status    = p.get("status_code", 0)
        title     = (p.get("title") or "").strip()
        meta      = (p.get("meta_description") or "").strip()
        h1        = (p.get("h1") or "").strip()
        words     = p.get("word_count", 0) or 0
        rt        = p.get("response_time_ms", 0) or 0
        canonical = (p.get("canonical_url") or "").strip()
        depth     = p.get("depth") or 0
        issues    = p.get("issues_detected") or []

        status_str = str(status)
        status_buckets[status_str[:1] + "xx"].append(url)

        # On-page checks (only for 2xx pages)
        if status_str.startswith("2"):
            if not title:             missing_title.append(url)
            if not meta:              missing_meta.append(url)
            if not h1:                missing_h1.append(url)
            if title and len(title) > 60:   long_title.append((url, title))
            if title and len(title) < 30:   short_title.append((url, title))
            if meta and len(meta) > 160:    long_meta.append((url, meta))
            if meta and 0 < len(meta) < 70: short_meta.append((url, meta))
            if 0 < words < 300:             thin_content.append((url, words))
            if rt > 3000:                   slow_pages.append((url, rt))

            if title:  dup_titles[title].append(url)
            if meta:   dup_metas[meta].append(url)

            # Canonical
            if not canonical:
                no_canonical.append(url)
            elif canonical == url:
                self_canonical.append(url)
            else:
                non_self_canonical.append((url, canonical))

            # H1 vs title mismatch (no shared content words)
            if title and h1:
                title_words = set(re.sub(r'[^a-z0-9 ]', '', title.lower()).split())
                h1_words    = set(re.sub(r'[^a-z0-9 ]', '', h1.lower()).split())
                stopwords   = {'the','a','an','and','or','for','in','on','at','to','of','is','are'}
                title_kw    = title_words - stopwords
                h1_kw       = h1_words - stopwords
                if title_kw and h1_kw and not title_kw.intersection(h1_kw):
                    h1_title_mismatch.append((url, title[:60], h1[:60]))

            # Depth
            if depth > 4:
                deep_pages.append((url, depth))

        # URL quality (all pages)
        parsed_url = urlparse(url)
        path       = parsed_url.path
        query      = parsed_url.query
        if path != path.lower():
            uppercase_urls.append(url)
        if len(url) > 115:
            long_urls.append((url, len(url)))
        if query.count("=") > 3:
            url_params_heavy.append(url)

        # Issues breakdown
        if isinstance(issues, list):
            for iss in issues:
                if isinstance(iss, str):
                    issues_type_count[iss] += 1
                elif isinstance(iss, dict):
                    issues_type_count[iss.get("type", "unknown")] += 1
        elif isinstance(issues, str) and issues:
            issues_type_count[issues] += 1

    # Filter duplicates (2+ pages with same value)
    dup_titles = {t: urls for t, urls in dup_titles.items() if len(urls) > 1}
    dup_metas  = {m: urls for m, urls in dup_metas.items()  if len(urls) > 1}

    # Cross-check: canonical pointing to broken URL
    broken_urls = set(status_buckets.get("4xx", []) + status_buckets.get("5xx", []))
    for url, canonical in non_self_canonical:
        if canonical in broken_urls:
            bad_canonical.append((url, canonical))

    broken   = status_buckets.get("4xx", []) + status_buckets.get("5xx", [])
    redirect = status_buckets.get("3xx", [])
    ok       = status_buckets.get("2xx", [])

    # ── Build Markdown ────────────────────────────────────────────────────────
    lines = []
    def h(level, text): lines.append(f"\n{'#' * level} {text}\n")
    def li(text):       lines.append(f"- {text}")
    def sep():          lines.append("\n---\n")

    # Header
    lines.append(f"# SEO Audit Report — {domain}")
    lines.append(f"**Generated:** {now}  |  **Crawl ID:** {crawl_id}  |  **Pages:** {total}\n")
    sep()

    # ── Summary scorecard ─────────────────────────────────────────────────────
    h(2, "📊 Summary")
    lines.append(f"| Metric | Count | Status |")
    lines.append(f"|--------|-------|--------|")
    lines.append(f"| Pages crawled | {total} | |")
    lines.append(f"| 200 OK | {len(ok)} | {'✅' if len(ok) == total else '⚠️'} |")
    lines.append(f"| Broken (4xx/5xx) | {len(broken)} | {'✅' if not broken else '🔴'} |")
    lines.append(f"| Redirects (3xx) | {len(redirect)} | {'✅' if not redirect else '⚠️'} |")
    lines.append(f"| Missing title | {len(missing_title)} | {'✅' if not missing_title else '🔴'} |")
    lines.append(f"| Missing meta desc | {len(missing_meta)} | {'✅' if not missing_meta else '🔴'} |")
    lines.append(f"| Missing H1 | {len(missing_h1)} | {'✅' if not missing_h1 else '🔴'} |")
    lines.append(f"| Duplicate titles | {len(dup_titles)} | {'✅' if not dup_titles else '🔴'} |")
    lines.append(f"| Duplicate meta desc | {len(dup_metas)} | {'✅' if not dup_metas else '🔴'} |")
    lines.append(f"| Title too long (>60) | {len(long_title)} | {'✅' if not long_title else '⚠️'} |")
    lines.append(f"| Title too short (<30) | {len(short_title)} | {'✅' if not short_title else '⚠️'} |")
    lines.append(f"| Meta too long (>160) | {len(long_meta)} | {'✅' if not long_meta else '⚠️'} |")
    lines.append(f"| Meta too short (<70) | {len(short_meta)} | {'✅' if not short_meta else '⚠️'} |")
    lines.append(f"| Missing canonical | {len(no_canonical)} | {'✅' if not no_canonical else '⚠️'} |")
    lines.append(f"| Non-self canonical | {len(non_self_canonical)} | {'✅' if not non_self_canonical else '⚠️'} |")
    lines.append(f"| Bad canonical (→ 4xx) | {len(bad_canonical)} | {'✅' if not bad_canonical else '🔴'} |")
    lines.append(f"| Thin content (<300w) | {len(thin_content)} | {'✅' if not thin_content else '⚠️'} |")
    lines.append(f"| Slow pages (>3s) | {len(slow_pages)} | {'✅' if not slow_pages else '⚠️'} |")
    lines.append(f"| H1 ↔ Title mismatch | {len(h1_title_mismatch)} | {'✅' if not h1_title_mismatch else '⚠️'} |")
    lines.append(f"| Deep pages (depth >4) | {len(deep_pages)} | {'✅' if not deep_pages else '⚠️'} |")
    lines.append(f"| Uppercase in URL | {len(uppercase_urls)} | {'✅' if not uppercase_urls else '⚠️'} |")
    lines.append(f"| URL too long (>115c) | {len(long_urls)} | {'✅' if not long_urls else '⚠️'} |")
    lines.append("")
    sep()

    # ── CRITICAL ──────────────────────────────────────────────────────────────
    h(2, "🔴 Critical — Fix First")

    # Broken pages with source
    if broken:
        h(3, f"Broken Pages ({len(broken)})")
        lines.append("> **Fix:** 301 to the correct URL, or remove internal links pointing here.\n")
        lines.append("| URL | Status | Linked From |")
        lines.append("|-----|--------|-------------|")
        for url in broken:
            s = next((p.get("status_code","?") for p in pages if p.get("url") == url), "?")
            sources = inbound.get(url, [])
            src_str = ", ".join(f"`{s}`" for s in sources[:3])
            if len(sources) > 3:
                src_str += f" +{len(sources)-3} more"
            lines.append(f"| `{url}` | {s} | {src_str or '—'} |")
        lines.append("")

    # Bad canonical (pointing to 4xx/5xx)
    if bad_canonical:
        h(3, f"Canonical Points to Broken URL ({len(bad_canonical)})")
        lines.append("> **Fix:** Update canonical to point to a live 200 page. A canonical to a 4xx = Google ignores it.\n")
        lines.append("| Page | Broken Canonical Target |")
        lines.append("|------|------------------------|")
        for url, canonical in bad_canonical[:20]:
            lines.append(f"| `{url}` | `{canonical}` |")
        lines.append("")

    # Duplicate titles
    if dup_titles:
        h(3, f"Duplicate Titles ({len(dup_titles)} groups)")
        lines.append("> **Fix:** Every page needs a unique title. Redirect or merge pages if they cover the same topic.\n")
        for title, urls in list(dup_titles.items())[:10]:
            lines.append(f"**\"{title[:70]}\"**")
            for u in urls:
                li(f"`{u}`")
            lines.append("")

    # Missing titles
    if missing_title:
        h(3, f"Missing Title Tag ({len(missing_title)} pages)")
        lines.append("> **Fix:** Add a unique `<title>` tag (50–60 chars) to each page.\n")
        for url in missing_title[:20]:
            li(f"`{url}`")
        if len(missing_title) > 20:
            lines.append(f"… and {len(missing_title)-20} more")
        lines.append("")

    if not broken and not bad_canonical and not dup_titles and not missing_title:
        lines.append("✅ No critical issues found.\n")

    sep()

    # ── WARNINGS ──────────────────────────────────────────────────────────────
    h(2, "⚠️ Warnings — High Impact")

    # Missing meta descriptions
    if missing_meta:
        h(3, f"Missing Meta Description ({len(missing_meta)} pages)")
        lines.append("> **Fix:** Add a unique meta description (120–155 chars). Directly improves click-through rate.\n")
        for url in missing_meta[:30]:
            li(f"`{url}`")
        if len(missing_meta) > 30:
            lines.append(f"… and {len(missing_meta)-30} more")
        lines.append("")

    # Duplicate meta descriptions
    if dup_metas:
        h(3, f"Duplicate Meta Descriptions ({len(dup_metas)} groups)")
        lines.append("> **Fix:** Write unique meta descriptions for each page. Duplicates waste click-through potential.\n")
        for meta, urls in list(dup_metas.items())[:8]:
            lines.append(f"**\"{meta[:80]}\"**")
            for u in urls[:5]:
                li(f"`{u}`")
            lines.append("")

    # Meta too long
    if long_meta:
        h(3, f"Meta Description Too Long — over 160 chars ({len(long_meta)} pages)")
        lines.append("> **Fix:** Shorten to 120–155 chars. Google truncates longer descriptions with '…'\n")
        lines.append("| URL | Length | Preview |")
        lines.append("|-----|--------|---------|")
        for url, meta in long_meta[:20]:
            lines.append(f"| `{url}` | {len(meta)} | {meta[:80]}… |")
        lines.append("")

    # Meta too short
    if short_meta:
        h(3, f"Meta Description Too Short — under 70 chars ({len(short_meta)} pages)")
        lines.append("> **Fix:** Expand to 120–155 chars. Short descriptions leave SERP real estate empty.\n")
        lines.append("| URL | Length | Current |")
        lines.append("|-----|--------|---------|")
        for url, meta in short_meta[:15]:
            lines.append(f"| `{url}` | {len(meta)} | {meta} |")
        lines.append("")

    # Missing H1
    if missing_h1:
        h(3, f"Missing H1 ({len(missing_h1)} pages)")
        lines.append("> **Fix:** Add exactly one `<h1>` per page matching the primary keyword.\n")
        for url in missing_h1[:20]:
            li(f"`{url}`")
        if len(missing_h1) > 20:
            lines.append(f"… and {len(missing_h1)-20} more")
        lines.append("")

    # Long titles
    if long_title:
        h(3, f"Title Too Long — over 60 chars ({len(long_title)} pages)")
        lines.append("> **Fix:** Shorten to 50–60 chars. Google truncates anything longer.\n")
        lines.append("| URL | Title (truncated) | Length |")
        lines.append("|-----|-------------------|--------|")
        for url, title in long_title[:20]:
            lines.append(f"| `{url}` | {title[:60]}… | {len(title)} |")
        if len(long_title) > 20:
            lines.append(f"| … | {len(long_title)-20} more | |")
        lines.append("")

    # Short titles
    if short_title:
        h(3, f"Title Too Short — under 30 chars ({len(short_title)} pages)")
        lines.append("> **Fix:** Expand to 50–60 chars. Include the primary keyword.\n")
        lines.append("| URL | Title | Length |")
        lines.append("|-----|-------|--------|")
        for url, title in short_title[:15]:
            lines.append(f"| `{url}` | {title} | {len(title)} |")
        lines.append("")

    # H1 ↔ Title mismatch
    if h1_title_mismatch:
        h(3, f"H1 and Title Share No Keywords ({len(h1_title_mismatch)} pages)")
        lines.append("> **Fix:** Align H1 and `<title>` on the same primary keyword. Google expects them to be consistent.\n")
        lines.append("| URL | Title | H1 |")
        lines.append("|-----|-------|----|")
        for url, title, h1 in h1_title_mismatch[:15]:
            lines.append(f"| `{url}` | {title} | {h1} |")
        lines.append("")

    # Thin content
    if thin_content:
        h(3, f"Thin Content — under 300 words ({len(thin_content)} pages)")
        lines.append("> **Fix:** Expand with useful content, or add `noindex` if it's a utility/pagination page.\n")
        lines.append("| URL | Words |")
        lines.append("|-----|-------|")
        for url, words in sorted(thin_content, key=lambda x: x[1])[:20]:
            lines.append(f"| `{url}` | {words} |")
        lines.append("")

    # Slow pages
    if slow_pages:
        h(3, f"Slow Server Response — over 3s ({len(slow_pages)} pages)")
        lines.append("> **Fix:** Check server caching, image optimisation, and plugin bloat. Target <1s TTFB.\n")
        lines.append("| URL | Response Time |")
        lines.append("|-----|--------------|")
        for url, rt in sorted(slow_pages, key=lambda x: -x[1])[:20]:
            lines.append(f"| `{url}` | {rt:,}ms |")
        lines.append("")

    sep()

    # ── CANONICAL ─────────────────────────────────────────────────────────────
    h(2, "🔗 Canonical Analysis")

    # Summary line
    self_can_count = len(self_canonical)
    lines.append(f"| Type | Count | Notes |")
    lines.append(f"|------|-------|-------|")
    lines.append(f"| Self-referencing (correct) | {self_can_count} | ✅ Standard best practice |")
    lines.append(f"| Missing canonical | {len(no_canonical)} | {'✅' if not no_canonical else '⚠️ Duplicate content risk'} |")
    lines.append(f"| Non-self canonical | {len(non_self_canonical)} | {'✅' if not non_self_canonical else '⚠️ These pages are canonicalized away'} |")
    lines.append(f"| Canonical → broken URL | {len(bad_canonical)} | {'✅' if not bad_canonical else '🔴 Fix immediately'} |")
    lines.append("")

    if no_canonical:
        h(3, f"Missing Canonical Tag ({len(no_canonical)} pages)")
        lines.append("> **Fix:** Add `<link rel=\"canonical\" href=\"{page_url}\">` to each page.\n")
        for url in no_canonical[:20]:
            li(f"`{url}`")
        if len(no_canonical) > 20:
            lines.append(f"… and {len(no_canonical)-20} more")
        lines.append("")

    if non_self_canonical:
        h(3, f"Pages Canonicalized to Other URLs ({len(non_self_canonical)})")
        lines.append("> These pages signal to Google: 'don't index me, index this other URL instead.' "
                     "Verify this is intentional — if not, update the canonical.\n")
        lines.append("| Page | Canonical Points To |")
        lines.append("|------|---------------------|")
        for url, canonical in non_self_canonical[:20]:
            lines.append(f"| `{url}` | `{canonical}` |")
        if len(non_self_canonical) > 20:
            lines.append(f"| … | {len(non_self_canonical)-20} more |")
        lines.append("")

    sep()

    # ── TECHNICAL / URL QUALITY ───────────────────────────────────────────────
    h(2, "🔧 Technical SEO")

    if uppercase_urls:
        h(3, f"Uppercase Letters in URL ({len(uppercase_urls)} pages)")
        lines.append("> **Fix:** Redirect uppercase URLs to lowercase equivalents. `URL` and `url` are treated as different pages.\n")
        for url in uppercase_urls[:15]:
            li(f"`{url}`")
        lines.append("")

    if long_urls:
        h(3, f"URL Too Long — over 115 chars ({len(long_urls)} pages)")
        lines.append("> **Fix:** Shorten slugs. Long URLs are harder to share and may signal keyword stuffing.\n")
        lines.append("| URL | Length |")
        lines.append("|-----|--------|")
        for url, length in sorted(long_urls, key=lambda x: -x[1])[:15]:
            lines.append(f"| `{url[:100]}…` | {length} |")
        lines.append("")

    if url_params_heavy:
        h(3, f"URLs with Excessive Query Parameters ({len(url_params_heavy)} pages)")
        lines.append("> **Fix:** Use canonical tags or robots.txt to prevent Googlebot wasting crawl budget on param variants.\n")
        for url in url_params_heavy[:10]:
            li(f"`{url}`")
        lines.append("")

    if deep_pages:
        h(3, f"Pages Too Deep — depth > 4 ({len(deep_pages)} pages)")
        lines.append("> **Fix:** Restructure navigation so important pages are reachable in ≤3 clicks from homepage.\n")
        lines.append("| URL | Depth |")
        lines.append("|-----|-------|")
        for url, depth in sorted(deep_pages, key=lambda x: -x[1])[:20]:
            lines.append(f"| `{url}` | {depth} |")
        lines.append("")

    if not uppercase_urls and not long_urls and not url_params_heavy and not deep_pages:
        lines.append("✅ No URL quality issues found.\n")

    # Site-level checks
    if site_data:
        h(3, "Site-Level Checks")

        robots = site_data.get("robots_txt", {})
        sitemap = site_data.get("sitemap", {})
        https_r = site_data.get("https_redirect", {})
        www_r   = site_data.get("www_redirect", {})

        lines.append("| Check | Result |")
        lines.append("|-------|--------|")
        lines.append(f"| robots.txt | {'✅ Found' if robots.get('found') else '⚠️ Missing'} |")
        if robots.get("found"):
            lines.append(f"| Disallow rules | {robots.get('disallow_count', 0)} rules |")
            lines.append(f"| Sitemap in robots.txt | {'✅ Yes' if robots.get('sitemap_declared') else '⚠️ Not declared'} |")
        lines.append(f"| sitemap.xml | {'✅ Found' if sitemap.get('found') else '⚠️ Missing'} |")
        if sitemap.get("found"):
            lines.append(f"| Sitemap URLs | {sitemap.get('url_count', '?')} |")
        lines.append(f"| HTTPS redirect | {'✅ Correct' if https_r.get('http_redirects_to_https') else ('⚠️ Missing/broken' if not https_r.get('error') else '—')} |")
        lines.append(f"| www redirect | {'✅ Correct' if www_r.get('alt_redirects_properly') else '⚠️ Not set up'} |")
        lines.append("")

        if robots.get("important_blocked"):
            lines.append("> ⚠️ **Potential over-blocking in robots.txt:**")
            for rule in robots["important_blocked"][:5]:
                li(f"`Disallow: {rule}`")
            lines.append("")

        if not sitemap.get("found"):
            lines.append(f"> ⚠️ **No sitemap found** — submit one to GSC at {base_url}/sitemap.xml\n")

        www_warning = www_r.get("warning")
        if www_warning:
            lines.append(f"> ⚠️ {www_warning}\n")

        https_warning = https_r.get("warning")
        if https_warning:
            lines.append(f"> ⚠️ {https_warning}\n")

    sep()

    # ── Redirects ─────────────────────────────────────────────────────────────
    if redirect:
        h(2, f"↪️ Redirects ({len(redirect)} pages)")
        lines.append("> **Fix:** Update internal links to point to the final destination URL. "
                     "Each redirect wastes crawl budget and loses a fraction of link equity.\n")
        for url in redirect[:20]:
            li(f"`{url}`")
        if len(redirect) > 20:
            lines.append(f"… and {len(redirect)-20} more")
        lines.append("")
        sep()

    # ── Issues breakdown (LibreCrawl's own detector) ──────────────────────────
    if issues_type_count:
        h(2, "🐛 Issue Type Breakdown (LibreCrawl detector)")
        lines.append("| Issue Type | Count |")
        lines.append("|------------|-------|")
        for issue_type, count in sorted(issues_type_count.items(), key=lambda x: -x[1])[:30]:
            lines.append(f"| {issue_type} | {count} |")
        lines.append("")
        sep()

    # ── All Pages ─────────────────────────────────────────────────────────────
    h(2, "📋 All Pages")
    lines.append("| Status | Depth | URL | Title | Words | Canon |")
    lines.append("|--------|-------|-----|-------|-------|-------|")

    sorted_pages = sorted(pages, key=lambda p: (
        0 if str(p.get("status_code","")).startswith("4") else
        1 if str(p.get("status_code","")).startswith("5") else
        2 if str(p.get("status_code","")).startswith("3") else 3,
        p.get("depth", 99)
    ))

    for p in sorted_pages[:300]:
        url    = p.get("url", "")
        status = p.get("status_code", "?")
        title  = (p.get("title") or "")[:45] or "—"
        words  = p.get("word_count", 0) or 0
        depth  = p.get("depth", "?")
        canonical = (p.get("canonical_url") or "").strip()
        canon_icon = "✅" if canonical == url else ("—" if not canonical else "↪️")
        status_icon = "🔴" if str(status).startswith(("4","5")) else "↪️" if str(status).startswith("3") else "✅"
        lines.append(f"| {status_icon} {status} | {depth} | `{url}` | {title} | {words} | {canon_icon} |")

    if len(pages) > 300:
        lines.append(f"| … | | {len(pages)-300} more pages not shown | | | |")

    lines.append("")
    sep()

    # ── Fix Priority Checklist ────────────────────────────────────────────────
    h(2, "✅ Fix Priority Checklist")
    lines.append("Copy this into your task tracker:\n")

    priority = 1
    checks = [
        (broken,           f"Fix {len(broken)} broken pages (4xx/5xx)"),
        (bad_canonical,    f"Fix {len(bad_canonical)} canonical tags pointing to broken URLs"),
        (dup_titles,       f"Resolve {len(dup_titles)} duplicate title groups"),
        (missing_title,    f"Add title tags to {len(missing_title)} pages"),
        (missing_meta,     f"Add meta descriptions to {len(missing_meta)} pages"),
        (missing_h1,       f"Add H1 to {len(missing_h1)} pages"),
        (long_title,       f"Shorten {len(long_title)} titles to ≤60 chars"),
        (short_title,      f"Expand {len(short_title)} short titles to 50–60 chars"),
        (long_meta,        f"Shorten {len(long_meta)} meta descriptions to ≤160 chars"),
        (dup_metas,        f"Unique-ify {len(dup_metas)} duplicate meta descriptions"),
        (no_canonical,     f"Add canonical tags to {len(no_canonical)} pages"),
        (non_self_canonical, f"Review {len(non_self_canonical)} pages canonicalized to other URLs"),
        (thin_content,     f"Address {len(thin_content)} thin content pages (<300 words)"),
        (slow_pages,       f"Fix {len(slow_pages)} slow pages (>3s response time)"),
        (h1_title_mismatch, f"Align H1 and title keywords on {len(h1_title_mismatch)} pages"),
        (redirect,         f"Update internal links for {len(redirect)} redirect targets"),
        (uppercase_urls,   f"Lowercase {len(uppercase_urls)} URLs with uppercase characters"),
        (long_urls,        f"Shorten {len(long_urls)} URLs over 115 chars"),
        (deep_pages,       f"Improve crawlability: {len(deep_pages)} pages at depth >4"),
    ]
    for condition, label in checks:
        if condition:
            lines.append(f"- [ ] **P{priority}** {label}")
            priority += 1

    lines.append("")
    lines.append(f"---\n*Generated by [librecrawl-mcp](https://github.com/adityaarsharma/librecrawl-mcp)*")

    return "\n".join(lines)


# ── MCP Tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
def librecrawl_audit(url: str, max_pages: int = 500) -> dict:
    """
    Full SEO audit in one call — crawls the site, runs site-level checks
    (robots.txt, sitemap, HTTPS, www), exports results, and saves a
    Markdown report file covering 20+ check categories.

    Use this for 'audit X' requests. Returns report_path + summary.
    For step-by-step control use librecrawl_start_crawl instead.

    Args:
        url:       Full URL to crawl (e.g. https://example.com)
        max_pages: Max pages (default 500)
    """
    # Start crawl
    call("POST", "/api/save_settings", json={
        "enableJavaScript": False,
        "maxUrls": max_pages,
        "maxDepth": 5,
        "crawlDelay": 0.5,
        "followRedirects": True,
        "crawlExternalLinks": False,
    })
    result   = call("POST", "/api/start_crawl", json={"url": url})
    crawl_id = result.get("crawl_id")

    if not result.get("success"):
        return {"success": False, "error": result.get("message", "Failed to start crawl")}

    # Run site-level checks in parallel with crawl (no wait needed)
    site_data = _site_check(url)

    # Poll until done (max 20 min)
    deadline = time.time() + 1200
    crawled  = 0
    while time.time() < deadline:
        time.sleep(8)
        d       = call("GET", "/api/crawl_status")
        stats   = d.get("stats", {})
        crawled = stats.get("crawled", 0)
        if not d.get("is_running", True) and crawled > 0:
            break

    # Export
    if crawl_id is not None:
        call("POST", f"/api/crawls/{crawl_id}/load")

    r = get_client().post(f"{BASE}/api/export_data", json={
        "format": "json",
        "fields": EXPORT_FIELDS,
    }, timeout=120)
    r.raise_for_status()
    export = r.json()

    pages = export if isinstance(export, list) else export.get("urls", export.get("pages", []))

    if not pages:
        return {
            "success": False,
            "crawl_id": crawl_id,
            "crawled": crawled,
            "error": "Export returned no pages. Try librecrawl_generate_report(crawl_id) in 30s.",
        }

    # Generate and save report
    report_md   = _build_report(pages, url, crawl_id or 0, site_data=site_data)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    domain      = url.replace("https://","").replace("http://","").rstrip("/").split("/")[0]
    timestamp   = datetime.now().strftime("%Y%m%d-%H%M")
    report_path = REPORTS_DIR / f"{domain}-{timestamp}.md"
    report_path.write_text(report_md, encoding="utf-8")

    broken = sum(1 for p in pages if str(p.get("status_code","")).startswith(("4","5")))
    no_meta = sum(1 for p in pages if not (p.get("meta_description") or "").strip())
    no_h1   = sum(1 for p in pages if not (p.get("h1") or "").strip())
    no_can  = sum(1 for p in pages if not (p.get("canonical_url") or "").strip())

    return {
        "success": True,
        "crawl_id": crawl_id,
        "pages_crawled": len(pages),
        "report_file": str(report_path),
        "summary": {
            "broken_pages": broken,
            "missing_meta_description": no_meta,
            "missing_h1": no_h1,
            "missing_canonical": no_can,
            "robots_txt_found": site_data.get("robots_txt", {}).get("found", False),
            "sitemap_found": site_data.get("sitemap", {}).get("found", False),
            "https_ok": site_data.get("https_redirect", {}).get("http_redirects_to_https", False),
        },
        "next": f"Open {report_path} for the full report with fix checklist.",
    }


@mcp.tool()
def librecrawl_site_check(url: str) -> dict:
    """
    Run site-level technical checks without crawling.
    Instant results — no crawl needed.

    Checks:
    - robots.txt (existence, disallow rules, sitemap declaration, crawl-delay)
    - sitemap.xml (existence, URL count, index vs regular)
    - HTTPS redirect (does http:// → https:// correctly?)
    - www/non-www redirect (does the alternate host redirect to canonical?)

    Args:
        url: Site root URL (e.g. https://example.com)
    """
    return _site_check(url)


@mcp.tool()
def librecrawl_generate_report(crawl_id: int = None) -> dict:
    """
    Generate a Markdown SEO report from a completed crawl.
    Saves the report as a .md file and returns the path.

    Args:
        crawl_id: ID from librecrawl_start_crawl (optional — uses current crawl if omitted)
    """
    base_url = ""

    if crawl_id is not None:
        call("POST", f"/api/crawls/{crawl_id}/load")
        try:
            d = call("GET", "/api/crawl_status")
            base_url = d.get("stats", {}).get("baseUrl", "")
        except Exception:
            pass

    r = get_client().post(f"{BASE}/api/export_data", json={
        "format": "json",
        "fields": EXPORT_FIELDS,
    }, timeout=120)
    r.raise_for_status()
    export = r.json()

    pages = export if isinstance(export, list) else export.get("urls", export.get("pages", []))

    if not pages:
        return {"success": False, "error": "No pages found. Is the crawl complete?"}

    if not base_url and pages:
        parsed   = urlparse(pages[0].get("url", ""))
        base_url = f"{parsed.scheme}://{parsed.netloc}"

    report_md   = _build_report(pages, base_url, crawl_id or 0)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    domain      = base_url.replace("https://","").replace("http://","").rstrip("/").split("/")[0]
    timestamp   = datetime.now().strftime("%Y%m%d-%H%M")
    report_path = REPORTS_DIR / f"{domain}-{timestamp}.md"
    report_path.write_text(report_md, encoding="utf-8")

    return {
        "success": True,
        "report_file": str(report_path),
        "pages": len(pages),
    }


@mcp.tool()
def librecrawl_start_crawl(url: str, max_pages: int = 500) -> dict:
    """
    Start a crawl manually. Returns crawl_id immediately — crawl runs async.
    Poll librecrawl_get_status() until done, then librecrawl_generate_report(crawl_id).

    Use librecrawl_audit() instead for a one-call full audit.

    Args:
        url:       Full URL to crawl (e.g. https://example.com)
        max_pages: Max pages (default 500)
    """
    call("POST", "/api/save_settings", json={
        "enableJavaScript": False,
        "maxUrls": max_pages,
        "maxDepth": 5,
        "crawlDelay": 0.5,
        "followRedirects": True,
        "crawlExternalLinks": False,
    })
    result   = call("POST", "/api/start_crawl", json={"url": url})
    crawl_id = result.get("crawl_id")
    return {
        "success": result.get("success"),
        "crawl_id": crawl_id,
        "message": result.get("message"),
        "next": f"Poll librecrawl_get_status() until is_running=False, then librecrawl_generate_report({crawl_id})",
    }


@mcp.tool()
def librecrawl_get_status() -> dict:
    """
    Poll current crawl progress. Repeat until is_running=False.
    Returns: is_running, crawled, queued, issues, base_url
    """
    d     = call("GET", "/api/crawl_status")
    stats = d.get("stats", {})
    return {
        "is_running": d.get("is_running", False),
        "crawled":    stats.get("crawled", 0),
        "queued":     stats.get("queued", 0),
        "issues":     stats.get("issues", 0),
        "base_url":   stats.get("baseUrl", ""),
    }


@mcp.tool()
def librecrawl_export_results(crawl_id: int = None) -> dict:
    """
    Export raw crawl JSON. For a formatted report use librecrawl_generate_report() instead.

    Args:
        crawl_id: ID from librecrawl_start_crawl (optional)
    """
    if crawl_id is not None:
        call("POST", f"/api/crawls/{crawl_id}/load")

    r = get_client().post(f"{BASE}/api/export_data", json={
        "format": "json",
        "fields": EXPORT_FIELDS,
    }, timeout=120)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def librecrawl_list_crawls() -> dict:
    """List all saved crawls with URL, crawl_id, and timestamp."""
    return call("GET", "/api/crawls/list")


@mcp.tool()
def librecrawl_stop_crawl() -> dict:
    """Stop the currently running crawl."""
    return call("POST", "/api/stop_crawl")


# ── PageSpeed Insights ────────────────────────────────────────────────────────

def _fetch_psi(url: str, strategy: str = "mobile") -> dict:
    """Fetch Core Web Vitals + performance score from Google PSI API."""
    if not PSI_API_KEY:
        return {"error": "PAGESPEED_API_KEY not set."}
    params = {"url": url, "key": PSI_API_KEY, "strategy": strategy,
              "category": ["performance", "seo", "accessibility", "best-practices"]}
    try:
        r = httpx.get(PSI_API_BASE, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"error": str(e)}

    lhr    = data.get("lighthouseResult", {})
    cats   = lhr.get("categories", {})
    audits = lhr.get("audits", {})
    field_metrics = data.get("loadingExperience", {}).get("metrics", {})

    def score(cat): return round((cats.get(cat, {}).get("score") or 0) * 100)
    def ms(audit_id):
        v = audits.get(audit_id, {}).get("numericValue")
        return round(v) if v else None

    field = {}
    for metric, key in [("LCP","LARGEST_CONTENTFUL_PAINT_MS"), ("FID","FIRST_INPUT_DELAY_MS"),
                         ("CLS","CUMULATIVE_LAYOUT_SHIFT_SCORE"), ("INP","INTERACTION_TO_NEXT_PAINT"),
                         ("FCP","FIRST_CONTENTFUL_PAINT_MS"), ("TTFB","EXPERIMENTAL_TIME_TO_FIRST_BYTE")]:
        m = field_metrics.get(key, {})
        if m:
            field[metric] = {"value": m.get("percentile"), "category": m.get("category")}

    lab = {k: v for k, v in {
        "FCP_ms":  ms("first-contentful-paint"),
        "LCP_ms":  ms("largest-contentful-paint"),
        "TBT_ms":  ms("total-blocking-time"),
        "CLS":     audits.get("cumulative-layout-shift", {}).get("numericValue"),
        "Speed_Index_ms": ms("speed-index"),
        "TTI_ms":  ms("interactive"),
    }.items() if v is not None}

    opps = []
    for audit_id, audit in audits.items():
        if audit.get("details", {}).get("type") == "opportunity":
            savings = audit.get("details", {}).get("overallSavingsMs", 0) or 0
            if savings > 200:
                opps.append({"title": audit.get("title"), "savings_ms": round(savings)})
    opps.sort(key=lambda x: -x["savings_ms"])

    return {
        "url": url, "strategy": strategy,
        "scores": {
            "performance":    score("performance"),
            "seo":            score("seo"),
            "accessibility":  score("accessibility"),
            "best_practices": score("best-practices"),
        },
        "field_data_cwv": field,
        "lab_data": lab,
        "top_opportunities": opps[:5],
    }


@mcp.tool()
def librecrawl_pagespeed(url: str, strategy: str = "mobile") -> dict:
    """
    Core Web Vitals + Lighthouse scores via Google PageSpeed Insights.
    Returns performance/SEO/accessibility scores, LCP/CLS/FCP/TBT, real-user CrUX data.

    Args:
        url:      Full URL to test
        strategy: "mobile" (default) or "desktop"
    """
    return _fetch_psi(url, strategy)


@mcp.tool()
def librecrawl_pagespeed_audit(urls: list, strategy: str = "mobile") -> dict:
    """
    Run PageSpeed Insights on multiple URLs — ranked worst to best.
    Throttled to 1 req/sec (stays within free quota of 25k/day).

    Args:
        urls:     List of URLs to test (recommend top 10–20 pages)
        strategy: "mobile" (default) or "desktop"
    """
    if not PSI_API_KEY:
        return {"error": "PAGESPEED_API_KEY not set."}

    results = []
    for url in urls[:25]:
        results.append(_fetch_psi(url, strategy))
        time.sleep(1.1)

    results.sort(key=lambda x: x.get("scores", {}).get("performance", 100))
    valid = [r for r in results if "scores" in r]

    summary = {
        "tested": len(results),
        "avg_performance": round(sum(r["scores"]["performance"] for r in valid) / len(valid)) if valid else 0,
        "poor_performance": sum(1 for r in valid if r["scores"]["performance"] < 50),
        "needs_improvement": sum(1 for r in valid if 50 <= r["scores"]["performance"] < 90),
        "good": sum(1 for r in valid if r["scores"]["performance"] >= 90),
    }
    return {"summary": summary, "results": results}


# ── Schema.org / JSON-LD ──────────────────────────────────────────────────────

class _JsonLdExtractor(HTMLParser):
    """Extract all <script type="application/ld+json"> blocks from HTML."""
    def __init__(self):
        super().__init__()
        self._in_ld = False
        self._buf   = []
        self.schemas = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self._in_ld = True
            self._buf   = []

    def handle_endtag(self, tag):
        if tag == "script" and self._in_ld:
            self._in_ld = False
            raw = "".join(self._buf).strip()
            if raw:
                try:
                    obj = json.loads(raw)
                    for item in (obj if isinstance(obj, list) else [obj]):
                        self.schemas.append({"type": item.get("@type","Unknown"), "data": item})
                except Exception:
                    pass

    def handle_data(self, data):
        if self._in_ld:
            self._buf.append(data)


def _extract_schema(url: str) -> list:
    try:
        r = httpx.get(url, follow_redirects=True, timeout=15,
                      headers={"User-Agent": "Mozilla/5.0 (compatible; SEO-bot/1.0)"})
        parser = _JsonLdExtractor()
        parser.feed(r.text)
        return parser.schemas
    except Exception as e:
        return [{"error": str(e)}]


RICH_RESULTS_MAP = {
    "Article":           "Article rich result — date, author, image in SERP",
    "BlogPosting":       "Article rich result",
    "Product":           "Product snippet — price, availability, ratings",
    "Review":            "Review snippet — star rating in SERP",
    "AggregateRating":   "Star ratings in SERP",
    "FAQPage":           "FAQ accordion in SERP (huge CTR boost)",
    "HowTo":             "How-to steps in SERP",
    "BreadcrumbList":    "Breadcrumb path shown in SERP URL",
    "WebSite":           "Sitelinks searchbox in SERP",
    "Organization":      "Knowledge panel — logo, contacts",
    "Person":            "Author knowledge panel",
    "LocalBusiness":     "Local business panel — address, hours, maps",
    "SoftwareApplication": "App rating + price in SERP",
    "VideoObject":       "Video thumbnail in SERP",
    "Event":             "Event date/location in SERP",
    "JobPosting":        "Job listing in Google Jobs",
    "Recipe":            "Recipe rich card — time, calories, ratings",
    "Course":            "Course info in SERP",
}


@mcp.tool()
def librecrawl_schema_check(url: str) -> dict:
    """
    Extract and classify all Schema.org / JSON-LD structured data from a page.
    No API key required — parses the live page directly on the server.

    Returns schema types found, which Google rich results they unlock, and
    what high-value schema types are missing.

    Args:
        url: Full URL to check
    """
    schemas = _extract_schema(url)
    found_types = [s.get("type") for s in schemas if "type" in s]
    return {
        "url": url,
        "schema_count": len(schemas),
        "types_found": found_types,
        "rich_results_enabled": [RICH_RESULTS_MAP[t] for t in found_types if t in RICH_RESULTS_MAP],
        "missing_opportunities": [
            f"{t}: {desc}" for t, desc in RICH_RESULTS_MAP.items()
            if t not in found_types and t in ["FAQPage","BreadcrumbList","Article","Product","Review"]
        ],
        "schemas": schemas,
    }


@mcp.tool()
def librecrawl_schema_audit(urls: list) -> dict:
    """
    Check Schema.org structured data across multiple URLs.
    No API key required.

    Args:
        urls: List of URLs to check (pass top pages from a crawl export)
    """
    results    = []
    no_schema  = []
    type_count = defaultdict(int)

    for url in urls[:50]:
        schemas = _extract_schema(url)
        types   = [s.get("type") for s in schemas if "type" in s]
        for t in types:
            type_count[t] += 1
        if not types:
            no_schema.append(url)
        results.append({"url": url, "types": types, "count": len(schemas)})
        time.sleep(0.3)

    return {
        "pages_checked":         len(results),
        "pages_no_schema":       len(no_schema),
        "schema_type_breakdown": dict(sorted(type_count.items(), key=lambda x: -x[1])),
        "pages_missing_schema":  no_schema[:30],
        "results": results,
    }


# ── GSC section appender ──────────────────────────────────────────────────────

@mcp.tool()
def librecrawl_append_gsc_section(report_path: str, gsc_data: dict) -> dict:
    """
    Append a Google Search Console errors section to an existing MD audit report.

    Workflow:
      1. librecrawl_audit(url) → get report_path
      2. Use gsc-posi connector to pull GSC coverage/crawl errors for the domain
      3. Pass both here — GSC section gets appended to the report

    gsc_data keys (any/all):
      coverage_errors  — list of {url, type, last_crawled}
      crawl_errors     — list of {url, response_code, last_crawled}
      search_issues    — list of strings (manual actions, security issues)
      performance      — dict {clicks, impressions, ctr, position}

    Args:
        report_path: Path returned by librecrawl_audit() or librecrawl_generate_report()
        gsc_data:    GSC data dict from the gsc-posi connector
    """
    path = Path(report_path)
    if not path.exists():
        return {"success": False, "error": f"Report not found: {report_path}"}

    now  = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = ["\n\n---\n", f"## 🔍 Google Search Console\n", f"*Pulled: {now}*\n"]

    coverage = gsc_data.get("coverage_errors") or gsc_data.get("indexing_errors") or []
    if coverage:
        by_type = defaultdict(list)
        for item in coverage:
            err_type = item.get("type") or item.get("reason") or "Unknown"
            url      = item.get("url") or item.get("inspectionUrl") or ""
            by_type[err_type].append(url)

        FIX_HINTS = {
            "Submitted URL not found (404)":          "Remove from sitemap, or 301 redirect.",
            "Submitted URL seems to be a Soft 404":   "Return real content or proper 404.",
            "Redirect error":                          "Fix redirect chain to resolve in ≤2 hops.",
            "Server error (5xx)":                     "Check server logs — 5xx blocks indexing.",
            "Blocked by robots.txt":                  "Remove Disallow rule if page should be indexed.",
            "Blocked due to access forbidden (403)":  "Allow Googlebot access or remove from sitemap.",
            "Crawled - currently not indexed":        "Improve content quality, add internal links.",
            "Discovered - currently not indexed":     "Add internal links so Googlebot crawls it.",
            "Alternate page with proper canonical tag": "Verify canonicalization is intentional.",
            "Duplicate without user-selected canonical": "Add canonical tag pointing to preferred URL.",
            "Page with redirect":                     "Update internal links to final URL.",
            "Excluded by 'noindex' tag":              "Verify these should be noindexed.",
        }

        lines.append(f"### Indexing / Coverage Errors ({len(coverage)} URLs)\n")
        for err_type, urls in sorted(by_type.items(), key=lambda x: -len(x[1])):
            hint = FIX_HINTS.get(err_type, "Investigate in GSC Coverage report.")
            lines.append(f"**{err_type}** — {len(urls)} URLs")
            lines.append(f"> Fix: {hint}\n")
            for u in urls[:10]:
                if u: lines.append(f"- `{u}`")
            if len(urls) > 10:
                lines.append(f"- … and {len(urls)-10} more")
            lines.append("")
    else:
        lines.append("### Indexing Errors\n✅ No coverage errors in provided GSC data.\n")

    crawl_errors = gsc_data.get("crawl_errors") or []
    if crawl_errors:
        lines.append(f"### Crawl Errors ({len(crawl_errors)})\n")
        lines.append("| URL | Status | Last Crawled |")
        lines.append("|-----|--------|-------------|")
        for item in crawl_errors[:20]:
            url  = item.get("url","")
            code = item.get("response_code") or item.get("status","?")
            last = item.get("last_crawled") or item.get("lastCrawled","—")
            lines.append(f"| `{url}` | {code} | {last} |")
        if len(crawl_errors) > 20:
            lines.append(f"| … | {len(crawl_errors)-20} more | |")
        lines.append("")

    issues = gsc_data.get("search_issues") or gsc_data.get("manual_actions") or []
    if issues:
        lines.append("### ⚠️ Manual Actions / Security Issues\n")
        for issue in issues:
            lines.append(f"- 🚨 {issue}")
        lines.append("")

    perf = gsc_data.get("performance") or {}
    if perf:
        lines.append("### Search Performance (28d)\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        if "clicks" in perf:      lines.append(f"| Clicks | {perf['clicks']:,} |")
        if "impressions" in perf: lines.append(f"| Impressions | {perf['impressions']:,} |")
        if "ctr" in perf:         lines.append(f"| CTR | {perf['ctr']:.1%} |")
        if "position" in perf:    lines.append(f"| Avg Position | {perf['position']:.1f} |")
        lines.append("")

    # GSC checklist
    coverage_by_type = defaultdict(int)
    for item in coverage:
        t = item.get("type") or item.get("reason") or "Unknown"
        coverage_by_type[t] += 1

    checklist = []
    p = 1
    for t in ["Submitted URL not found (404)", "Server error (5xx)", "Redirect error"]:
        if t in coverage_by_type:
            checklist.append(f"- [ ] **P{p} (GSC)** Fix {coverage_by_type[t]}x '{t}'")
            p += 1
    for t in ["Submitted URL seems to be a Soft 404", "Crawled - currently not indexed",
              "Duplicate without user-selected canonical"]:
        if t in coverage_by_type:
            checklist.append(f"- [ ] **P{p} (GSC)** Resolve {coverage_by_type[t]}x '{t}'")
            p += 1

    if checklist:
        lines.append("### GSC Fix Checklist\n")
        lines.extend(checklist)
        lines.append("")

    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return {
        "success": True,
        "report_file": str(path),
        "gsc_section_added": True,
        "coverage_errors": len(coverage),
        "crawl_errors": len(crawl_errors),
        "manual_actions": len(issues),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.streamable_http_app(), host="127.0.0.1", port=MCP_PORT, log_level="info")
