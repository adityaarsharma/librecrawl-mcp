# LibreCrawl MCP

**Self-hosted SEO crawler for Claude — Screaming Frog-level audits, zero per-crawl cost.**

Wraps [LibreCrawl](https://github.com/PhialsBasement/LibreCrawl) as a Claude MCP server. Give Claude the ability to fully audit any website — broken links, canonical issues, image alt text, orphan pages, Core Web Vitals, Schema.org, GSC errors — all running on your own server.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/Claude-MCP-orange)](https://modelcontextprotocol.io)
[![LibreCrawl](https://img.shields.io/badge/Powered%20by-LibreCrawl-green)](https://github.com/PhialsBasement/LibreCrawl)

---

## vs Screaming Frog

| Check | Screaming Frog Free | Screaming Frog Paid | LibreCrawl MCP |
|-------|:-------------------:|:--------------------:|:--------------:|
| **Pages** | 500 limit | Unlimited | Unlimited |
| **Price** | Free (capped) | £149/yr | Free + self-host |
| **Broken links (4xx/5xx) + source page** | ✅ | ✅ | ✅ |
| **Redirect chains** | ✅ | ✅ | ✅ |
| **Missing/duplicate title tags** | ✅ | ✅ | ✅ |
| **Missing/duplicate meta descriptions** | ✅ | ✅ | ✅ |
| **Title / meta too long or too short** | ✅ | ✅ | ✅ |
| **Missing H1** | ✅ | ✅ | ✅ |
| **H1 ↔ Title keyword mismatch** | ✅ | ✅ | ✅ |
| **Canonical analysis** (missing, self, non-self, broken) | ✅ | ✅ | ✅ |
| **Thin content** | ✅ | ✅ | ✅ |
| **Response time / slow pages** | ✅ | ✅ | ✅ |
| **URL quality** (uppercase, length, params) | ✅ | ✅ | ✅ |
| **Page depth warnings** | ✅ | ✅ | ✅ |
| **Noindex page detection** | ✅ | ✅ | ✅ |
| **Image alt text** | ✅ | ✅ | ✅ |
| **Broken images** | ✅ | ✅ | ✅ |
| **Orphan pages** (no inbound links) | ❌ | ✅ | ✅ |
| **Open Graph tags** | ❌ | ✅ | ✅ |
| **Viewport meta** (mobile) | ❌ | ✅ | ✅ |
| **Hreflang detection** | ❌ | ✅ | ✅ |
| **robots.txt** (rules, crawl-delay, sitemap) | ✅ | ✅ | ✅ |
| **sitemap.xml** | ✅ | ✅ | ✅ |
| **HTTPS redirect check** | ✅ | ✅ | ✅ |
| **www/non-www canonicalization** | ✅ | ✅ | ✅ |
| **Core Web Vitals (PSI)** | ❌ | ❌ | ✅ |
| **Schema.org / JSON-LD** | ❌ | ✅ | ✅ |
| **GSC indexing errors** | ❌ | ❌ | ✅ (via MCP) |
| **Analytics tag detection** (GA4, GTM, Pixel) | ❌ | ❌ | ✅ |
| **AI-generated fix checklist** | ❌ | ❌ | ✅ |
| **Natural language audit report** | ❌ | ❌ | ✅ |
| **Fully automated** (one command) | ❌ | ❌ | ✅ |

---

## What LibreCrawl MCP gives you

[LibreCrawl](https://github.com/PhialsBasement/LibreCrawl) is a powerful self-hosted SEO crawler. On its own you get a web UI and raw crawl data. This MCP layer turns it into a fully automated Claude-native audit engine — one sentence to Claude gets you a complete site audit, saved as a Markdown report, ready to act on.

### 19 tools, zero context-switching

Claude gains **19 specialised SEO tools**. Ask in plain English — Claude picks the right tool, runs it, interprets the output, and gives you a fix plan. No dashboards to navigate, no exports to download, no manual cross-referencing.

- `librecrawl_audit()` — one call: crawls the site, runs site-level checks, generates a structured Markdown report with a prioritised fix checklist. Done.
- Persistent authenticated session across all tool calls — no re-login between steps
- Every crawl saved to SQLite with full history via `librecrawl_list_crawls()`

### Report engine — 35+ checks, 12 sections

LibreCrawl's raw JSON export gets transformed into a structured audit report covering everything Screaming Frog covers, plus things it doesn't:

| Section | What it catches |
|---------|----------------|
| Summary scorecard | 30+ metrics with pass/fail at a glance |
| Critical issues | Broken pages + which pages link to them, duplicate titles, bad canonicals |
| On-page warnings | Meta length, missing H1, thin content, slow response time |
| H1 ↔ Title alignment | Keyword mismatch check — flags pages where headings contradict title intent |
| Canonical analysis | Missing, self-referencing, non-self, canonical → broken URL |
| Images | Missing alt text (per-page count + total), broken image references |
| Noindex detection | Every page with `robots: noindex` — catch accidental SEO blackouts |
| Orphan pages | Pages with zero inbound links — invisible to Googlebot |
| Redirect chains | Multi-hop chains (A→B→C), not just 3xx presence |
| Open Graph + Viewport | Social sharing tags, mobile viewport — affects CTR and ranking |
| Heading structure | Pages with content but no H2s, broken H1→H2 hierarchy |
| Analytics coverage | Pages missing GA4 or GTM — tracking blind spots |
| URL quality | Uppercase slugs, long URLs, parameter-heavy URLs, depth >4 |
| Site-level checks | robots.txt rules, sitemap.xml, HTTPS redirect, www canonicalisation |
| Hreflang | Language variant detection for multilingual sites |
| Issue type breakdown | LibreCrawl's 1,600+ built-in issue detectors, counted by type |
| Fix checklist | Auto-prioritised P1→Pn task list — paste straight into your tracker |

### Beyond crawl data — 6 specialist tools

| Tool | Value |
|------|-------|
| `librecrawl_site_check` | Instant technical health — robots.txt, sitemap, HTTPS, www. No crawl needed. |
| `librecrawl_pagespeed` | Google PageSpeed Insights: Core Web Vitals, LCP/CLS/INP, lab + field data |
| `librecrawl_pagespeed_audit` | Batch CWV across top pages — ranked worst first, throttled to stay in free quota |
| `librecrawl_schema_check` | Extract all JSON-LD from a page, map to rich results they unlock (FAQ, Product, Breadcrumb…) |
| `librecrawl_schema_audit` | Schema coverage across 50 pages at once |
| `librecrawl_internal_links_analysis` | Internal authority map: top-linked pages, dead ends, orphans, anchor text patterns |

### GSC integration

Connect any Google Search Console MCP (we recommend [mcp-gsc](https://github.com/AminForou/mcp-gsc)) and Claude will pull your real indexing errors — 404s in sitemap, server errors, soft 404s, crawl blocks — and append them to the audit report with fix hints. One conversation, complete picture.

---

## Install (1 command)

```bash
curl -fsSL https://raw.githubusercontent.com/adityaarsharma/librecrawl-mcp/main/install.sh | bash
```

**Requires:** Docker, Python 3.9+, Node.js (for PM2), Git

The installer:
1. Clones LibreCrawl and builds the Docker image (~5–8 min first run)
2. Applies all required patches to `main.py` for full DB persistence
3. Installs the Python MCP server in an isolated venv
4. Registers both services with PM2 (`restart: always`, survives reboots)
5. Prompts for optional Google PageSpeed Insights API key (free, 25k req/day)

### Custom install directory or ports

```bash
INSTALL_DIR=/opt/librecrawl-mcp LIBRECRAWL_PORT=5080 MCP_PORT=5081 bash install.sh
```

---

## Add to Claude

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "librecrawl": {
      "type": "http",
      "url": "http://127.0.0.1:5081/mcp"
    }
  }
}
```

**Claude Code** (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "librecrawl": {
      "type": "http",
      "url": "http://127.0.0.1:5081/mcp"
    }
  }
}
```

**Remote server** (via Nginx + mcp-remote):

```json
{
  "mcpServers": {
    "librecrawl": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://your-domain.com/librecrawl/mcp"]
    }
  }
}
```

Nginx location block for remote:

```nginx
location /librecrawl/ {
    proxy_pass              http://127.0.0.1:5081/;
    proxy_http_version      1.1;
    proxy_set_header        Host $host;
    proxy_read_timeout      600s;
    proxy_buffering         off;
    proxy_cache             off;
    chunked_transfer_encoding on;
}
```

---

## Add Google Search Console (optional but recommended)

LibreCrawl MCP can merge GSC coverage errors into your audit report via `librecrawl_append_gsc_section`. To use it, connect a GSC MCP server to Claude first.

### Recommended: mcp-gsc (AminForou)

The best community GSC MCP — 876+ stars, maintained, supports OAuth and service account auth.

**Install:**
```bash
pip install mcp-search-console
# or with uvx (no pip needed):
# uvx mcp-search-console
```

**Option A — OAuth (interactive, easiest):**

1. Create a project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable **Google Search Console API**
3. Create **OAuth 2.0 Client ID** → Desktop app → download `credentials.json`
4. Add to Claude config:

```json
{
  "mcpServers": {
    "gsc": {
      "command": "uvx",
      "args": ["mcp-search-console"],
      "env": {
        "GOOGLE_CREDENTIALS_FILE": "/path/to/credentials.json"
      }
    }
  }
}
```

First run opens a browser for Google auth. Token is cached.

**Option B — Service Account (automation-friendly):**

1. Create a service account at [console.cloud.google.com](https://console.cloud.google.com) → IAM → Service Accounts
2. Download the JSON key file
3. Add the service account email as a **user** in your GSC property (Settings → Users and permissions)
4. Add to Claude config:

```json
{
  "mcpServers": {
    "gsc": {
      "command": "uvx",
      "args": ["mcp-search-console"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account.json"
      }
    }
  }
}
```

### Using GSC with audit reports

Once connected, Claude can pull GSC errors and merge them into any audit:

```
"Audit uichemy.com, include GSC indexing errors"
```

Claude will:
1. Run `librecrawl_audit("https://uichemy.com")` → gets `report_path`
2. Pull GSC coverage errors via the GSC MCP
3. Call `librecrawl_append_gsc_section(report_path, gsc_data)` → adds a GSC section to the report

The GSC section includes: indexing errors with fix hints, crawl errors, manual actions, and a prioritised fix checklist.

---

## Tools (13 total)

| Tool | What it does |
|------|-------------|
| `librecrawl_audit` | **One-call full audit** — crawl + site checks + 30+ checks + report |
| `librecrawl_site_check` | Instant: robots.txt, sitemap, HTTPS, www — no crawl needed |
| `librecrawl_generate_report` | Re-generate report from a past crawl |
| `librecrawl_start_crawl` | Start async crawl, returns `crawl_id` |
| `librecrawl_get_status` | Poll crawl progress |
| `librecrawl_pause_crawl` | Pause a running crawl |
| `librecrawl_resume_crawl` | Resume a paused crawl |
| `librecrawl_stop_crawl` | Stop running crawl |
| `librecrawl_export_results` | Raw JSON export |
| `librecrawl_list_crawls` | List all saved crawls |
| `librecrawl_get_settings` | Show current crawler settings |
| `librecrawl_filter_issues` | Exclude false-positive patterns from results |
| `librecrawl_visualization_data` | Site link graph (nodes + edges) |
| `librecrawl_internal_links_analysis` | Internal authority map — top linked pages, orphans, dead ends, anchor text |
| `librecrawl_pagespeed` | Core Web Vitals for one URL (Google PSI API) |
| `librecrawl_pagespeed_audit` | Batch CWV for up to 25 URLs, ranked worst-first |
| `librecrawl_schema_check` | Schema.org / JSON-LD for one URL — rich result mapping |
| `librecrawl_schema_audit` | Schema coverage across multiple URLs |
| `librecrawl_append_gsc_section` | Merge GSC indexing errors into any audit report |

---

## Usage

Once connected, just ask:

> *"Audit uichemy.com and give me a full SEO report"*

Claude will crawl the site, run site-level checks, generate a Markdown report at `~/librecrawl-reports/uichemy.com-{timestamp}.md`, and summarise the top issues.

> *"Check Core Web Vitals on the top 10 pages"*

> *"Does uichemy.com have schema markup? What rich results is it missing?"*

> *"Run a full audit and include GSC errors"* (requires GSC MCP)

---

## Architecture

```
Claude
  │  MCP (streamable-http)
  ▼
Python MCP server (port 5081)
  │  REST API
  ▼
LibreCrawl Flask app (port 5080, Docker)
  │  Headless crawl (Playwright + Chromium)
  ▼
Target website
```

**Stack:** LibreCrawl · FastMCP · httpx · uvicorn · PM2 · Docker

---

## Manage services

```bash
# Status
pm2 status librecrawl-mcp
docker ps | grep librecrawl

# Logs
pm2 logs librecrawl-mcp
docker logs librecrawl --tail 50

# Restart
pm2 restart librecrawl-mcp
docker restart librecrawl

# Stop
pm2 stop librecrawl-mcp
docker stop librecrawl
```

---

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `INSTALL_DIR` | `~/librecrawl-mcp` | Where to install |
| `LIBRECRAWL_PORT` | `5080` | LibreCrawl internal port |
| `MCP_PORT` | `5081` | MCP server port |
| `PAGESPEED_API_KEY` | — | Google PSI API key (free at console.cloud.google.com) |
| `REPORTS_DIR` | `~/librecrawl-reports` | Where Markdown reports are saved |

---

## Related

- [LibreCrawl](https://github.com/PhialsBasement/LibreCrawl) — the crawler this wraps
- [mcp-gsc](https://github.com/AminForou/mcp-gsc) — Google Search Console MCP (876 stars, recommended)
- [Model Context Protocol](https://modelcontextprotocol.io)

---

## License

MIT — use freely, attribution appreciated.

Built by [Aditya Sharma](https://adityaarsharma.com)
