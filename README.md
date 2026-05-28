# LibreCrawl MCP

**Self-hosted SEO crawler for any AI agent — Screaming Frog-level audits, zero per-crawl cost.**

Wraps [LibreCrawl](https://github.com/PhialsBasement/LibreCrawl) as a fully local MCP server. Give your AI the ability to fully audit any website — broken links, canonical issues, image alt text, orphan pages, Core Web Vitals, Schema.org, GSC errors — 100% on your own machine. No cloud. No account. No data leaving your server.

Works with **any MCP-compatible AI agent** — Claude, Cursor, Windsurf, OpenAI Codex, Continue.dev, VS Code Copilot, and more.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-orange)](https://modelcontextprotocol.io)
[![LibreCrawl](https://img.shields.io/badge/Powered%20by-LibreCrawl-green)](https://github.com/PhialsBasement/LibreCrawl)
[![Works With](https://img.shields.io/badge/Works%20With-Claude%20%7C%20Cursor%20%7C%20Codex%20%7C%20Windsurf-blue)](https://modelcontextprotocol.io)

---

### What's new in v1.1.1

- **🆕 `librecrawl_resume_from_crawl_id(crawl_id)`** — crawl a huge site in chunks across days, sessions, and server restarts. Pause now, resume tomorrow from a different MCP session — picks up at the exact URL it stopped on, re-uses every page already crawled, zero duplicate requests to the target server. The "however big, in chunks, polite to the server" feature.

### What's new in v1.1.0

- **Auto-recovery from stuck crawler** — `librecrawl_audit()` and `librecrawl_start_crawl()` now silently reset paused/stale crawler state before starting a new run. No more *"Crawl already in progress"* errors after a previous session was interrupted. Run a fresh audit anytime — it just works.
- **GSC top queries section** — the report now includes a top-25 search queries table (clicks, impressions, CTR, position) automatically appended via `librecrawl_append_gsc_section()`.
- **🎯 Quick wins detection** — page-2 keywords (positions 6-20) with high impressions are auto-surfaced as optimisation opportunities.
- **Flat-or-nested GSC input** — `gsc_data` now accepts performance metrics either nested under `performance` or flat at the top level. Whichever your GSC MCP returns, it just works.

---

## Crawling huge sites politely

LibreCrawl MCP is built to handle sites of any size without putting load on the target server, and to crawl in chunks across multiple sessions.

**Polite by default:**
- **Token-bucket rate limiter** — smooth distribution, no bursting. Default `crawlDelay: 0.5s` = 2 requests/second.
- **Respects `Crawl-Delay` directive in robots.txt** — if your target sets `Crawl-Delay: 5`, LibreCrawl will wait 5s between requests.
- **Same User-Agent across the crawl** — `LibreCrawl/1.0 (Web Crawler)`, identifiable and well-behaved.
- **Single connection, sequential by default** — no parallel hammering. Configurable up to 5 concurrent workers if you control the server.

**Crawl in chunks:**

```text
Day 1:  Audit https://huge-site.com (max 5000 pages)
        → runs, returns crawl_id 42
        → pause anytime with librecrawl_pause_crawl()

Day 2:  list_crawls() → see crawl_id 42 with status "paused" at 1,847 pages
        librecrawl_resume_from_crawl_id(42)
        → picks up at page 1,848 — every previously-crawled URL is re-used from
          the SQLite DB, no duplicate HTTP requests to the target

Day 3:  Same thing — resume_from_crawl_id(42) until done
        → generate_report(42) for the full Markdown audit
```

State persists across PM2 restarts, server reboots, and entirely different MCP client sessions. The crawl is keyed by `crawl_id`, not by the MCP session.

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

[LibreCrawl](https://github.com/PhialsBasement/LibreCrawl) is a powerful self-hosted SEO crawler. On its own you get a web UI and raw crawl data. This MCP layer turns it into a fully automated AI-native audit engine — one sentence gets you a complete site audit, saved as a Markdown report, ready to act on.

### 20 tools, works with any AI agent

Your AI gains **20 specialised SEO tools**. Ask in plain English — the AI picks the right tool, runs it, interprets the output, and gives you a fix plan. No dashboards to navigate, no exports to download, no manual cross-referencing.

- `librecrawl_audit()` — one call: crawls the site, runs site-level checks, generates a structured Markdown report with a prioritised fix checklist. Done.
- Persistent authenticated session across all tool calls — no re-login between steps
- Every crawl saved to SQLite with full history via `librecrawl_list_crawls()`

### Report engine — 37 checks, 17 sections

LibreCrawl's raw JSON export gets transformed into a structured audit report covering everything Screaming Frog covers, plus things it doesn't:

| Section | What it catches |
|---------|----------------|
| Summary scorecard | 37 metrics with pass/fail at a glance |
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

Connect any Google Search Console MCP (we recommend [mcp-gsc](https://github.com/AminForou/mcp-gsc)) and your AI will pull:
- **Indexing errors** — 404s in sitemap, server errors, soft 404s, crawl blocks (with fix hints)
- **Top 25 search queries** — clicks, impressions, CTR, average position
- **🎯 Quick wins** — page-2 keywords (pos 6-20) with high impressions, auto-surfaced for optimisation

All appended to the same audit report. One conversation, complete picture.

> **GSC property type matters.** If your site is verified as a **Domain property** in GSC, pass `sc-domain:yoursite.com` as the site URL. If it's a **URL-prefix property**, pass the full `https://yoursite.com/` (trailing slash matters). The installer's GSC step walks through both.

---

## Quick Start — Your First Audit

This guide takes you from zero to a full SEO audit report in under 10 minutes.

### Step 1 — Install (1 command)

```bash
curl -fsSL https://raw.githubusercontent.com/adityaarsharma/librecrawl-mcp/main/install.sh | bash
```

What happens:
- LibreCrawl Docker image is pulled and built (~5–8 min, first run only)
- Python MCP server is installed and registered with PM2
- Both services start automatically and survive reboots

You'll be asked for a Google PageSpeed Insights API key (optional but recommended — free at [console.cloud.google.com](https://console.cloud.google.com), 25k req/day).

**Verify everything is running:**
```bash
pm2 status librecrawl-mcp          # MCP server — should show "online"
docker ps | grep librecrawl        # LibreCrawl — should show "healthy"
```

---

### Step 2 — Add to your AI agent

The installer auto-configures this for you when you answer question [2/3]. If you prefer manual setup, use the configs below.

LibreCrawl MCP supports **two transport modes**:
- **HTTP mode** — for Claude Desktop and Claude Code (server runs persistently via PM2)
- **Stdio mode** — for Cursor, Codex, Windsurf, Continue.dev and any agent that spawns subprocesses

---

#### Claude Desktop
Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `~/.config/Claude/claude_desktop_config.json` (Linux):

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
Restart Claude Desktop after saving.

#### Claude Code
Edit `~/.claude/settings.json`:

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

#### Cursor
Edit `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per project):

```json
{
  "mcpServers": {
    "librecrawl": {
      "command": "python3",
      "args": ["~/librecrawl-mcp/mcp-server/server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "LIBRECRAWL_PORT": "5080"
      }
    }
  }
}
```

#### OpenAI Codex CLI
Edit `~/.codex/config.yaml`:

```yaml
mcpServers:
  librecrawl:
    command: python3
    args:
      - ~/librecrawl-mcp/mcp-server/server.py
    env:
      MCP_TRANSPORT: stdio
      LIBRECRAWL_PORT: "5080"
```

#### Windsurf
Edit `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "librecrawl": {
      "command": "python3",
      "args": ["~/librecrawl-mcp/mcp-server/server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "LIBRECRAWL_PORT": "5080"
      }
    }
  }
}
```

#### Continue.dev
Edit `.continue/config.yaml` in your project:

```yaml
mcpServers:
  - name: librecrawl
    command: python3
    args:
      - ~/librecrawl-mcp/mcp-server/server.py
    env:
      MCP_TRANSPORT: stdio
      LIBRECRAWL_PORT: "5080"
```

#### VS Code with Copilot / GitHub Copilot Agent
Edit `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "librecrawl": {
      "type": "stdio",
      "command": "python3",
      "args": ["~/librecrawl-mcp/mcp-server/server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "LIBRECRAWL_PORT": "5080"
      }
    }
  }
}
```

> **Note for stdio mode:** LibreCrawl Docker must already be running (`docker ps | grep librecrawl`). The AI agent spawns a fresh MCP process per session that connects to it on `LIBRECRAWL_PORT`.

---

### Step 3 — Run your first audit

Open your AI agent and type:

```
Audit https://example.com and give me a full SEO report
```

Your AI will:
1. Crawl the entire site (runs in background, progress visible in `pm2 logs librecrawl-mcp`)
2. Run site-level checks (robots.txt, sitemap, HTTPS, www redirect)
3. Analyse all 37 SEO checks across every crawled page
4. Save a Markdown report to `~/librecrawl-reports/example.com-YYYYMMDD-HHMMSS.md`
5. Return a summary of the top issues with a prioritised fix checklist

**For large sites** (1,000+ pages), the crawl can run up to 2 hours. To cap it:
```
Audit https://bigsite.com — limit to 500 pages
```

---

### Step 4 — Read your report

The report is saved at `~/librecrawl-reports/`. Each report has:

| Section | What it shows |
|---------|--------------|
| Scorecard | Pass/fail for every check at a glance |
| Critical issues | Broken pages (404/5xx) + which pages link to them |
| On-page warnings | Missing titles, duplicate metas, thin content, slow pages |
| Canonical analysis | Missing, self, non-self, broken canonical URLs |
| Orphan pages | Pages with zero inbound links — Googlebot may never find them |
| Redirect chains | Multi-hop chains (A→B→C) eating crawl budget |
| Images | Pages with missing alt text, broken image references |
| Analytics coverage | Pages not tracked by GA4 or GTM |
| Fix checklist | P1→Pn priority tasks — paste straight into Jira/ClickUp |

---

### Step 5 — Add GSC errors + top queries (recommended)

Install a Google Search Console MCP ([mcp-gsc](https://github.com/AminForou/mcp-gsc) is recommended — the installer handles this automatically at question [3/3]), then ask:

```
Audit https://example.com and include GSC indexing errors + top queries
```

Your AI will merge into the same report:
- Real GSC coverage errors — 404s in sitemap, soft 404s, server errors, crawl blocks
- Top 25 search queries with clicks, impressions, CTR, position
- 🎯 Auto-surfaced page-2 quick wins (queries at position 6-20 with high impressions)

**First-time GSC setup gotchas:**

1. **Property type matters.** In GSC, sites are verified as either:
   - **Domain property** → use `sc-domain:example.com` as the site URL
   - **URL-prefix property** → use the full `https://example.com/` (trailing slash matters)
   
   If the GSC tool returns *"User does not have sufficient permission for site"*, you almost certainly mixed these up. Run `list_sites` first to see how your property is registered:
   
   ```
   List all GSC sites I have access to
   ```

2. **OAuth on first use.** The GSC MCP opens a browser for Google OAuth on the first call. Pick the Google account that owns the verified property. Token is cached after — no re-auth.

3. **Service account alternative.** For team setups or headless servers, use a Google Cloud service account instead of OAuth. Grant the service account email **Restricted user** access in GSC → Settings → Users and permissions.

---

### Other things to ask

```
Check Core Web Vitals on the top 10 pages of example.com
```
```
Does example.com have schema markup? What rich results is it missing?
```
```
Run an internal links analysis — which pages are orphans?
```
```
Quick site health check for example.com — no crawl needed
```

---

## Remote server setup (optional)

For local installs see the Quick Start above. To expose your LibreCrawl MCP over Nginx (e.g. on a VPS so your whole team can use it):

**Claude Desktop / Claude Code** (via mcp-remote):

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

LibreCrawl MCP can merge GSC coverage errors into your audit report via `librecrawl_append_gsc_section`. To use it, connect a GSC MCP server to your AI agent first.

### Recommended: mcp-gsc (AminForou)

The best community GSC MCP — 900+ stars, maintained, supports OAuth and service account auth.

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
4. Add to your AI agent config:

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
4. Add to your AI agent config:

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

Once connected, your AI can pull GSC errors and merge them into any audit:

```
"Audit uichemy.com, include GSC indexing errors"
```

Your AI will:
1. Run `librecrawl_audit("https://uichemy.com")` → gets `report_path`
2. Pull GSC coverage errors via the GSC MCP
3. Call `librecrawl_append_gsc_section(report_path, gsc_data)` → adds a GSC section to the report

The GSC section includes: indexing errors with fix hints, crawl errors, manual actions, and a prioritised fix checklist.

---

## Tools (19 total)

| Tool | What it does |
|------|-------------|
| `librecrawl_audit` | **One-call full audit** — crawl + site checks + 37 checks + report |
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

## Architecture

```
Any MCP-compatible AI agent
(Claude / Cursor / Codex / Windsurf / Continue.dev / Copilot / ...)
  │
  │  HTTP mode (Claude Desktop/Code):  streamable-http via PM2 → port 5081
  │  Stdio mode (Cursor/Codex/etc.):   subprocess spawn, stdin/stdout JSON-RPC
  │
  ▼
LibreCrawl MCP server (server.py)
  │  REST API (localhost only)
  ▼
LibreCrawl Flask app (Docker, port 5080)  ←  Visual UI at localhost:5080
  │  Headless crawl (Playwright + Chromium)
  ▼
Target website
```

**Stack:** LibreCrawl · FastMCP · httpx · uvicorn · PM2 · Docker  
**Transport:** `MCP_TRANSPORT=http` (default, PM2/HTTP — Claude Desktop & Code) or `MCP_TRANSPORT=stdio` (Cursor, Codex, Windsurf, Continue.dev)

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
- [mcp-gsc](https://github.com/AminForou/mcp-gsc) — Google Search Console MCP (900+ stars, recommended)
- [Model Context Protocol](https://modelcontextprotocol.io)

---

## License

MIT — use freely, attribution appreciated.

Built by [Aditya Sharma](https://adityaarsharma.com)
