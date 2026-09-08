---
name: A-Crawlability
description: Audit a public website's crawlability — the first gate in the machine discovery pipeline. Tests robots.txt blocking (A-001), non-crawlable JS-only navigation (A-002), and persistent HTTP retrieval failures (A-003). Use when checking if a site's content is accessible to crawlers.
license: MIT
metadata:
  author: adobe-hackathon-research
  version: "1.0"
  mechanism: crawl
  hypotheses: A-001, A-002, A-003
---

# Crawl Audit

## When to use

Use when you need to check whether a site's important public content is **accessible to crawlers**. This skill tests three sequential crawl gates:

- **Permission** (A-001): Is robots.txt blocking important URLs?
- **Discovery** (A-002): Are pages hidden behind JS-only navigation?
- **Retrieval** (A-003): Do important URLs return usable HTTP responses?

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `--url` | Yes | Base URL of the site to audit |
| `--urls-file` | No | File with candidate important URLs (one per line) |
| `--output` | No | Output JSON file path (defaults to stdout) |
| `--timeout` | No | Per-request timeout in seconds (default: 15) |

## Procedure

1. **A-001 — robots.txt audit**:
   - Fetch `{base_url}/robots.txt`
   - Parse Disallow/Allow rules per RFC 9309
   - Test each candidate URL against rules for `*`, `Googlebot`, `GPTBot`
   - Filter out administrative paths (`/admin`, `/wp-admin`, etc.)
   - Flag URLs that are blocked AND return 200 on direct request

2. **A-002 — Link discovery audit**:
   - Parse all `<a href>` links from initial HTML (static link graph)
   - Fetch and parse `sitemap.xml` if available
   - Detect JS-only navigation patterns (onclick handlers, "Load More" buttons, role="link" without href)
   - Identify URLs discoverable only via JS interaction

3. **A-003 — URL retrieval audit**:
   - Sample important URLs from navigation/sitemap
   - Make HTTP requests with retries (≥2 attempts, 5s delay)
   - Classify failures as persistent vs transient
   - Exclude rate-limited (429) responses from failure rate
   - Calculate persistent failure rate

## Output

Each check produces JSON with: `check_id`, `status`, `severity`, `evidence`, `reason`, `suggested_action`.

The orchestrator composes these into the final audit report.

## References

- `references/crawl-sources.md` — Authoritative sources (RFC 9309, RFC 9110, Google Search Central)
- `references/severity-model.md` — Severity framework
