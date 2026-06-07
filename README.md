<!-- mcp-name: io.github.adityaarsharma/librecrawl-technical-seo-audit-mcp -->

<div align="center">

# 🕷️ librecrawl-technical-seo-audit-mcp

### **The AI-native technical SEO crawler.**

Run a complete on-site SEO audit on any website — straight from Claude, Cursor, Codex, or any Model Context Protocol (MCP) client. **Unlimited pages · 50+ checks · PDF + CSVs · MIT-licensed · self-hosted · ephemeral by design.**

Built on the open-source [**LibreCrawl**](https://github.com/PhialsBasement/LibreCrawl) engine, exposed through 37 MCP tools your AI assistant calls directly.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-orange?style=for-the-badge&logo=anthropic)](https://modelcontextprotocol.io)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Latest Release](https://img.shields.io/github/v/release/adityaarsharma/librecrawl-technical-seo-audit-mcp?style=for-the-badge&color=brightgreen)](https://github.com/adityaarsharma/librecrawl-technical-seo-audit-mcp/releases)
[![GitHub stars](https://img.shields.io/github/stars/adityaarsharma/librecrawl-technical-seo-audit-mcp?style=for-the-badge&color=yellow)](https://github.com/adityaarsharma/librecrawl-technical-seo-audit-mcp/stargazers)
[![Built on LibreCrawl](https://img.shields.io/badge/Built%20on-LibreCrawl-7C3AED?style=for-the-badge)](https://github.com/PhialsBasement/LibreCrawl)

[![Works With](https://img.shields.io/badge/Claude%20Code-supported-D97757?style=flat-square)](https://docs.anthropic.com/claude-code)
[![Works With](https://img.shields.io/badge/Claude%20Desktop-supported-D97757?style=flat-square)](https://claude.ai/download)
[![Works With](https://img.shields.io/badge/Cursor-supported-000000?style=flat-square)](https://cursor.com)
[![Works With](https://img.shields.io/badge/OpenAI%20Codex-supported-10A37F?style=flat-square)](https://github.com/openai/codex)
[![Works With](https://img.shields.io/badge/Windsurf-supported-00C2A8?style=flat-square)](https://codeium.com/windsurf)
[![Works With](https://img.shields.io/badge/Continue.dev-supported-7C3AED?style=flat-square)](https://continue.dev)

**[⚡ Install in 60s](#-install-in-60-seconds) · [🪄 What it does](#-the-whole-pitch-in-4-lines) · [🚀 50+ checks](#-50-checks-every-audit) · [🆚 Compare](#-feature-comparison-to-other-on-site-seo-crawlers) · [📖 Quick start](#-your-first-audit)**

</div>

---

## 🤔 Don't know what an MCP is? Read this 30-second explainer

> **Model Context Protocol (MCP)** is the open standard that lets AI assistants like Claude, Cursor, or Codex call external tools. Think of it as "USB for AI assistants" — you plug a tool in, the AI can use it. librecrawl-technical-seo-audit-mcp is one of those tools. Once installed, you just *ask* your AI assistant to audit a site, and it does. No GUI. No dashboard. No exports.

**New to all this?**
- Don't have Claude Code yet? → [Install Claude Code](https://docs.anthropic.com/claude-code) (free for individuals).
- Prefer Cursor? → [Get Cursor](https://cursor.com).
- Already have one of those? → Skip to [Install in 60s](#-install-in-60-seconds).

---

## 🪄 The whole pitch in 4 lines

```
You:    Audit https://acme.com — full site, no caps, give me the zip
Agent:  → librecrawl_start_chunked_audit · polls until done · saves zip locally
You:    Show me broken pages + broken external links + hreflang errors
Agent:  → reads CSVs, prints filtered tables. Server already forgot the audit.
```

That's the product. **Your AI assistant runs a full technical SEO audit for you.** You get a branded PDF + 7 CSVs covering 50+ technical checks, ready to hand a client. The server wipes everything the moment you download.

---

## 🔥 Why this exists

There are great desktop SEO crawlers (you know the ones). There are great cloud SEO suites. **There was no AI-native crawler.** librecrawl-technical-seo-audit-mcp fills that gap with five things no comparable open-source MCP server does:

### ⚡ It runs **inside your AI assistant**

37 MCP tools your agent calls directly. No GUI app to babysit, no SaaS dashboard to log into, no CSV exports to upload to ChatGPT. **You just ask.**

### 🚀 Chunked-progressive crawler that **never times out**

Most SEO MCP servers (SiteAudit MCP, AgentAEO, SE Ranking MCP) run synchronously and disconnect on sites over a few hundred pages. librecrawl-technical-seo-audit-mcp runs the crawl in a **background worker thread**, persists progress to SQLite WAL, and returns a `session_id` in **under 2 seconds**. Your agent polls a tiny status tool until done. **10,000-page enterprise sites work the same as 50-page blogs.** Survives PM2 / MCP-client restarts mid-crawl.

### 🛡️ Catches WAF challenges other crawlers **silently misreport**

Cloudflare, Akamai, DataDome, Imperva, and PerimeterX challenge pages are served as `200 OK` but contain a JavaScript challenge instead of your content. Most crawlers report these as "page OK, all good". librecrawl-technical-seo-audit-mcp fingerprints the challenge in the response body and flags `bot_block_challenge_detected`. **You see what's actually broken.**

### 🤖 An **AIMD controller** tunes crawl delay live

Additive-Increase / Multiplicative-Decrease — the same algorithm TCP congestion control uses. Error rate > 10% → halve chunk, double delay. p95 latency > 1.5× target → 1.5× delay. Clean signals → additive decrease. **Polite by construction. No rate-limit blow-ups. No manual tuning.** Respects `robots.txt` `Crawl-Delay` floor.

### 🧹 **Ephemeral by design** — the agency-safe default

Once you download the zip, the server deletes the session row, every artifact file on disk, AND the upstream LibreCrawl crawl record. **Per-audit server footprint after cleanup: 0 bytes, 0 rows.** Auditing 50 client sites? Zero data persists where another operator could see it.

### 📄 Branded **PDF reports** ready to hand a client

WeasyPrint, A4, page numbers, footer on every page. Open in any PDF viewer. No SaaS watermark. Hand it to a client as your work.

---

## ⚡ Install in 60 seconds

```bash
curl -fsSL https://raw.githubusercontent.com/adityaarsharma/librecrawl-technical-seo-audit-mcp/main/install.sh | bash
```

The installer asks 3 questions (target client, optional Google PageSpeed API key, optional GSC integration) and writes a ready-to-use MCP entry into your Claude / Cursor / Codex / Windsurf config. **Done.**

<details>
<summary><strong>What if I'm not a developer?</strong></summary>

You don't need to be. If you can:
1. Open a terminal (macOS: Cmd+Space → "Terminal" · Windows: Win+R → "powershell")
2. Paste the `curl` command above
3. Answer 3 yes/no questions

…you're done. The installer handles Python, Docker, the LibreCrawl backend, and your AI client config. **First-audit-to-zip is under 10 minutes from cold start.**

</details>

<details>
<summary><strong>Manual install (Python 3.10+, Docker for LibreCrawl backend)</strong></summary>

```bash
git clone https://github.com/adityaarsharma/librecrawl-technical-seo-audit-mcp.git
cd librecrawl-technical-seo-audit-mcp
python3 -m venv venv && source venv/bin/activate
pip install httpx mcp weasyprint markdown fpdf2
# Start LibreCrawl backend on :5080 (see install.sh for Docker compose)
python server.py
```

Add to your client config (Claude Desktop example):

```json
{
  "mcpServers": {
    "librecrawl": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://127.0.0.1:5081/mcp"]
    }
  }
}
```

</details>

---

## 🚀 50+ checks every audit

<table>
<tr>
<td valign="top" width="50%">

#### 🔒 Security & headers
`missing_hsts` · `missing_csp` · `missing_x_frame_options` · `missing_x_content_type_options` · `missing_referrer_policy` · `x_robots_tag_vs_meta_mismatch` · `mixed_content`

#### 🛡️ WAF / bot-block detection
`bot_block_challenge_detected` — fingerprints **Cloudflare · Akamai · DataDome · Imperva · PerimeterX**

#### 🗺️ Sitemap & robots
`sitemap_url_noindex` · `sitemap_url_3xx` · `sitemap_url_disallowed_in_robots` · `sitemap_contains_canonicalized` · `sitemap_over_50k_urls` · `sitemap_over_50mb`

#### 🌍 Hreflang full audit
`missing_return_tag` · `missing_self_reference` · `missing_x_default` · `invalid_codes` · `to_noindex` · `to_broken` · `conflicts_lang_attr`

#### 🔗 Canonical health
`canonical_chain_depth` · `canonical_to_relative` · `canonical_to_redirect` · `canonical_outside_head` · `bad_canonical`

#### 🔁 Redirects (every flavour)
`redirect_chains` · `meta_refresh_redirect` · `js_redirect` · `http_refresh_redirect`

#### 🏷️ Schema.org (16 types)
Article · Product · Recipe · FAQPage · BreadcrumbList · Event · JobPosting · VideoObject · HowTo · Organization · LocalBusiness · Person · Review · AggregateRating · Course · NewsArticle — validates **schema.org spec** AND **Google Rich Results** required fields. Handles `@graph` (Yoast / Rank Math / WPRM).

</td>
<td valign="top" width="50%">

#### 🔤 URL quality
`url_contains_space` · `url_multiple_slashes` · `url_non_ascii` · `url_underscores` · `url_repetitive_path` · `long_urls` · `uppercase_urls` · `url_params_heavy`

#### ⚓ Anchor text
`non_descriptive_anchor_text` · `empty_anchor_text` · `anchor_image_no_alt` · `broken_bookmarks`

#### 🕸️ Internal linking
`internal_nofollow_outlinks` · `nofollow_only_inbound` · `follow_and_nofollow_mixed` · `orphan_pages`

#### 🖼️ Image performance + CLS
`lazy_load_attr_missing` · `srcset_missing` · `image_dimensions_missing` · `next_gen_image_format` · `image_oversized_kb` · `missing_alt_pages` · `broken_img_pages`

#### 📐 HTML structure
`html_over_2mb` · `noscript_in_head` · `broken_or_invalid_html` · `dom_size_excessive` · `lorem_ipsum_detected`

#### ♿ Accessibility / metadata
`iframes_present` · `iframe_missing_title` · `missing_favicon` · `missing_html_lang` · `invalid_html_lang` · `missing_charset` · `missing_viewport`

#### 🪤 Crawl-budget killers
`spider_trap_calendar` · `url_session_id_high_entropy` · `faceted_url_explosion`

#### ✍️ Content quality
`low_readability` (Flesch) · `long_sentences` · `passive_voice_pct` · `missing_terminal_punctuation` · `boilerplate_ratio` · `ai_tell_tokens_found` (delve · unlock · seamlessly · leverage) · `has_lorem_ipsum`

#### 🚨 Dev leaks
`outlinks_to_localhost` (RFC1918 in production)

</td>
</tr>
</table>

**🔗 Every outbound URL HEAD/GET-validated** into 17 status classes — `ok` · `redirect` · `forbidden` · `not_found` · `timeout` · `dns_error` · `ssl_error` · `connection_refused` · etc. Per-target: final URL after redirects, source pages, anchor text, response time, server header.

**📈 GSC merge** — pull Google Search Console data, call `librecrawl_merge_gsc_data(crawl_id, gsc_data)`. URLs normalised before joining. Emits **4 extra CSVs**: `per-page-with-gsc` · `gsc-winners` · `gsc-losers` (high impr + CTR <2%) · `gsc-quick-wins` (position 11–20 + impr ≥100).

---

## 🆚 Feature comparison to other on-site SEO crawlers

> This is a factual feature comparison. Prices were checked at publication and may have changed — see each vendor's site for current pricing. Brand names belong to their respective owners.

| Capability | Desktop crawler (Screaming Frog SEO Spider™)<sup>1</sup> | Desktop+cloud crawler (Sitebulb™)<sup>2</sup> | Cloud site-audit (Ahrefs™)<sup>3</sup> | **librecrawl-technical-seo-audit-mcp** |
|---|:---:|:---:|:---:|:---:|
| **Pricing model** | Free tier (500 URLs) · paid annual licence | Paid monthly subscription | Bundled with main subscription | **Free, MIT-licensed, self-hosted** |
| **Page cap** | 500 free / unlimited paid | Unlimited | Tiered by subscription plan | **♾️ Unlimited** |
| **Runs inside your AI assistant** | ❌ | ❌ | ❌ | ✅ |
| **Chunked / background crawl (no timeout)** | ❌ | ❌ | Cloud only | ✅ |
| **Auto-adaptive crawl delay (AIMD)** | ❌ | Manual | Hidden | ✅ |
| **WAF / bot-block detection on 200-OK pages** | ❌ | ❌ | ❌ | ✅ |
| **Sitemap-orphan fill (URLs not internally linked)** | ❌ | ❌ | ❌ | ✅ |
| **Ephemeral by default (zero server footprint)** | N/A | N/A | N/A | ✅ |
| Broken links (4xx/5xx/timeout/DNS/SSL) | ✅ | ✅ | ✅ | ✅ |
| Redirect chains with destination | ✅ | ✅ | ✅ | ✅ |
| Title / meta / H1 + duplicates | ✅ | ✅ | ✅ | ✅ |
| Canonical full audit | ✅ | ✅ | ✅ | ✅ |
| Hreflang full audit (incl. return-tag graph) | ✅ | ✅ | Partial | ✅ |
| Sitemap full cross-checks | ✅ | ✅ | Partial | ✅ |
| Schema.org validation (16 types + Rich Results) | ✅ | ✅ | Partial | ✅ |
| Soft-404 fingerprinting | ✅ | ✅ | ✅ | ✅ |
| Mixed content (HTTPS → HTTP) | ✅ | ✅ | ✅ | ✅ |
| Security headers pack | ✅ | ✅ | Partial | ✅ |
| Image performance + CLS | ✅ | ✅ | ✅ | ✅ |
| Content quality (Flesch · AI-tells · boilerplate) | ❌ | Partial | ❌ | ✅ |
| Crawl-budget traps (calendar · session-id · facets) | ✅ | ✅ | ✅ | ✅ |
| Branded PDF report | ❌ | ✅ | ❌ | ✅ |
| GSC clicks/impressions merge | Paid add-on | Paid add-on | Native | ✅ |
| JavaScript rendering | ✅ | ✅ | Cloud only | 🛣️ Roadmap |

<sub>
<sup>1</sup> Screaming Frog SEO Spider is a trademark of Screaming Frog Ltd, UK. We are not affiliated.<br>
<sup>2</sup> Sitebulb is a trademark of Sitebulb Ltd, UK. We are not affiliated.<br>
<sup>3</sup> Ahrefs is a trademark of Ahrefs Pte. Ltd., Singapore. We are not affiliated.
</sub>

**Reading guide:** if you currently use a paid on-site crawler and your workflow is *"crawl → export CSVs → analyse"*, librecrawl-technical-seo-audit-mcp covers that flow inside your AI assistant for £0 with no page caps. If your workflow depends on JavaScript-rendered SPAs, that's on the [roadmap](#-roadmap) but not shipped yet — use the desktop tool for now.

---

## 📊 What every audit produces

Single zip, 8 files:

| File | Use |
|---|---|
| `SUMMARY.txt` | One-page orientation |
| `<domain>-<ts>.pdf` | **Branded human-readable PDF** (open in any viewer) |
| `<domain>-<ts>.md` | Markdown source of the PDF (grep-friendly) |
| `per-page.csv` | 1 row per URL × 30 columns of check booleans + `failed_checks_list` |
| `sitemap-recon.csv` | Sitemap-vs-crawl diff |
| `external-links.csv` | Every outbound URL + status |
| `content-audit.csv` | Per-page readability + AI-tells |
| `extended-checks.csv` | 1 row per (URL × check × severity × detail) — all 50+ checks |

---

## 📖 Your first audit

```text
You:   Audit https://example.com — full site, no caps

Agent: → librecrawl_start_chunked_audit(url=..., total_max_pages=10000)
         returns session_id in <2s

       → polls librecrawl_audit_status every 25s
         status: crawling, pages_done: 47,  current_delay_ms: 250
         status: crawling, pages_done: 312, last chunk p95: 480ms, err_rate: 0%
         status: done,     pages_done: 534, artifacts_ready: true

       → librecrawl_audit_zip(session_id, auto_cleanup=True)
         returns base64 zip (8 files, 320 KB)
         SAVES LOCALLY as example.com-1780572742.zip
         Server wiped: session_rows=4, files=8, upstream_crawl=1

You:   Show me broken pages + broken external links

Agent: → unzips, reads per-page.csv (filters status_4xx OR status_5xx)
       → reads external-links.csv (filters not_found · forbidden · 5xx · timeout)
       → prints both tables
```

**Local zip is the only copy.** Server is back to zero state.

---

## 🛣️ Roadmap

| | Status |
|---|:---:|
| **JavaScript rendering** (Playwright headless, DOM diff vs raw HTML) — catches SPA / React / Next.js apps | 🟡 Designed |
| **Core Web Vitals from CrUX** — real-user 28-day field data, not just lab PSI | 🟡 Designed |
| **axe-core accessibility audit** — contrast, ARIA, focus order, alt-text quality | 🟡 Planned |
| **White-label PDF theming** (`--brand-config` for agencies) | 🟡 Planned |
| **Diff mode** — audit A vs audit B, "what regressed since last week?" | 🟡 Planned |
| **Webhook on completion** (Slack / Discord) — ping when long crawls finish | 🟡 Planned |

> **Not planned:** keyword research, backlink analysis, SERP tracking. Those are different problems with different MCP servers (DataForSEO, etc.). This tool is laser-focused on **technical on-site SEO crawling**.

[Open an issue](https://github.com/adityaarsharma/librecrawl-technical-seo-audit-mcp/issues/new) to bump priorities or request a check.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  MCP client (Claude Code / Desktop / Cursor / Codex …)      │
└────────────────────────────┬────────────────────────────────┘
                             │  streamable HTTP or stdio
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  librecrawl-technical-seo-audit-mcp wrapper  (server.py — FastMCP, 37 tools)    │
│  ┌─────────────────┐    ┌──────────────────────────────┐    │
│  │ runner.py       │    │ external_links / schema /    │    │
│  │ background      │    │ content_audit / extended_    │    │
│  │ worker thread   │    │ checks / sitemap_fill /      │    │
│  │ AIMD controller │    │ pdf_report                   │    │
│  └────────┬────────┘    └──────────────────────────────┘    │
│           │                                                  │
│  ┌────────▼────────┐    ┌──────────────────────────────┐    │
│  │ state.py        │    │ libreclient.py — typed       │    │
│  │ SQLite WAL      │    │ wrapper to upstream API      │    │
│  │ session state   │    └──────────────┬───────────────┘    │
│  └─────────────────┘                   │                    │
└─────────────────────────────────────────┼────────────────────┘
                                          │
                                          ▼
                          ┌──────────────────────────────┐
                          │  LibreCrawl Flask backend    │
                          │  :5080 — single-tenant       │
                          │  crawls + extracts SEO data  │
                          └──────────────────────────────┘
```

---

## ⚙️ Configuration

| Env var | Default | Purpose |
|---|---|---|
| `LIBRECRAWL_PORT` | `5080` | LibreCrawl backend port |
| `MCP_PORT` | `5081` | MCP wrapper port |
| `MCP_TRANSPORT` | `http` | `http` (streamable) or `stdio` |
| `REPORTS_DIR` | `~/librecrawl-reports` | Where audit artifacts land |
| `PAGESPEED_API_KEY` | unset | Optional — enables `librecrawl_pagespeed*` |
| `LIBRECRAWL_STATE_DB` | `~/librecrawl-state.db` | SQLite WAL state store |

---

## 🛠️ 37 MCP tools

<details>
<summary><strong>Expand the full tool reference</strong></summary>

**Chunked audit (95% of work):**
- `librecrawl_start_chunked_audit` · `librecrawl_audit_status` · `librecrawl_audit_zip`
- `librecrawl_audit_pause` · `librecrawl_audit_resume` · `librecrawl_audit_cancel` · `librecrawl_audit_force_advance`
- `librecrawl_audit_artifacts` · `librecrawl_audit_pdf` · `librecrawl_report_content`

**Specialist:**
- `librecrawl_external_links_audit` — re-run external-link validation on a specific crawl
- `librecrawl_schema_validate` · `librecrawl_schema_check` · `librecrawl_schema_audit`
- `librecrawl_merge_gsc_data` · `librecrawl_append_gsc_section` — Google Search Console data merge
- `librecrawl_pagespeed` · `librecrawl_pagespeed_audit` · `librecrawl_pagespeed_audit_all_crawl_pages` — PageSpeed Insights
- `librecrawl_site_check` — instant site-level check
- `librecrawl_internal_links_analysis` · `librecrawl_filter_issues` · `librecrawl_visualization_data`

**Maintenance:**
- `librecrawl_wipe_everything` — nuclear reset to zero
- `librecrawl_brain_purge_audit` — purge a single audit

**Legacy (kept for backwards compat, avoid for big sites):**
- `librecrawl_audit` · `librecrawl_full_audit_strict` · `librecrawl_generate_report` · `librecrawl_export_results` · `librecrawl_get_status` · `librecrawl_get_settings` · `librecrawl_list_crawls` · `librecrawl_start_crawl` · `librecrawl_stop_crawl` · `librecrawl_pause_crawl` · `librecrawl_resume_crawl` · `librecrawl_resume_from_crawl_id`

</details>

---

## 📜 License & trademarks

**Code: MIT.** Use it on client work, agency work, internal tools, anything. No attribution required (but appreciated). See [LICENSE](LICENSE).

**Trademarks.** All third-party product names mentioned in this README (including any names referenced in the comparison table) are property of their respective owners. This project is not affiliated with, endorsed by, or sponsored by any third-party tool vendor. Comparisons are based on publicly available information at the time of writing and exist for the purpose of informing readers evaluating different categories of SEO tooling.

---

## 🙏 Credits

- **[LibreCrawl](https://github.com/PhialsBasement/LibreCrawl)** — the upstream open-source crawler this MCP server wraps. MIT. **Please go star them — this project would not exist without that work.**
- **[Anthropic Model Context Protocol](https://modelcontextprotocol.io)** — the protocol this server speaks
- **[WeasyPrint](https://weasyprint.org/)** — Markdown → HTML → PDF rendering
- **[FastMCP](https://github.com/jlowin/fastmcp)** — the Python MCP server framework

---

<div align="center">

### Built by [Aditya Sharma](https://adityaarsharma.com) · MIT · No telemetry · No SaaS · No vendor lock-in

</div>

---

<sub>

**Discoverability keywords:** seo audit mcp server · open-source seo crawler · self-hosted seo crawler · technical seo audit mcp · on-site seo audit tool · alternative to paid seo crawlers · free seo audit tool · seo crawler for claude · seo crawler for cursor · seo crawler for openai codex · seo crawler for windsurf · seo crawler for continue.dev · mcp server for seo · model context protocol seo · hreflang audit tool free · canonical chain checker · broken link checker unlimited · core web vitals audit cli · structured data validator command line · schema.org rich results validator · sitemap audit tool · sitemap orphan detection · WAF detection crawler · cloudflare challenge detector · security headers checker · CSP HSTS audit · google search console integration crawler · soft 404 detection · chunked crawler no timeout MCP · technical SEO audit api · python seo crawler · seo agency tool open source · ephemeral seo audit · agency-safe seo crawler · branded pdf seo report · seo audit cli tool · mit-licensed seo crawler · free site audit tool · enterprise seo crawler self-hosted · librecrawl mcp · librecrawl mcp server

</sub>
