---
name: audit-orchestrator
description: Orchestrate a full AI discoverability audit across crawlability, extractability, and non-text lock-in mechanisms. Composes outputs from crawl-audit, extractability-audit, and non-text-lockin-audit into a single audit report with findings and prioritized actions. Use when diagnosing why a brand is missing or misrepresented in AI assistants.
license: MIT
metadata:
  author: adobe-hackathon-research
  version: "1.0"
---

# AI Discoverability Audit — Orchestrator (Entrypoint)

## When to use

Run this skill when you need a **complete AI discoverability audit** of a public website. It composes three mechanism-specific skills:

- **crawl-audit** — Can crawlers access the content? (robots.txt, link discovery, HTTP retrieval)
- **extractability-audit** — Can machine readers correctly extract facts? (render-dependency, semantic associations)
- **non-text-lockin-audit** — Are facts locked in non-text formats? (images, PDFs, video/canvas)

Use when:
- Diagnosing why a brand is missing or misrepresented in AI assistant answers
- Auditing a site before launch for AI readiness
- Producing an actionable report of discoverability issues with prioritized fixes

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `--url` | Yes | Base URL of the site to audit (e.g., `https://example.com`) |
| `--output` | No | Path to write the JSON report (defaults to stdout) |
| `--timeout` | No | Per-request timeout in seconds (default: 15) |

## Procedure

1. **Crawlability phase** (site-level):
   - Run `robots_audit.py` to check robots.txt for blocked important content (A-001)
   - Run `link_discovery_audit.py` to detect JS-only navigation patterns (A-002)
   - Run `url_retrieval_audit.py` to test for persistent HTTP failures (A-003)

2. **Extractability phase** (page-level):
   - Run `semantic_association_audit.py` on the main page to detect orphaned factual values (C-003)

3. **Non-text lock-in phase** (page-level):
   - Run `image_fact_audit.py` to detect images with facts but no text equivalents (F-001)
   - Run `document_fact_audit.py` to detect PDFs with facts not in page HTML (F-002)
   - Run `visual_media_audit.py` to detect video/canvas without text alternatives (F-003)

4. **Compose report**: Aggregate all findings into the required report schema with severity counts and prioritized actions.

## Output

A single JSON audit report conforming to the required schema:

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {
    "total_findings": 3,
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 0
  },
  "findings": [
    {
      "id": "A-001",
      "title": "Crawl-Blocked Important Content",
      "severity": "high",
      "evidence": "Tested 10 candidate URLs; 3 important public URLs are blocked by robots.txt.",
      "suggested_action": {
        "summary": "Remove or narrow robots.txt Disallow rules for important public content.",
        "priority": "high"
      }
    }
  ]
}
```

**Required fields per finding**: `id`, `title`, `severity`, `evidence`, `suggested_action`.

**Required summary metadata**: `site`, `audited_at`, counts by severity.

## Running

```bash
python skills/audit-orchestrator/scripts/run_audit.py --url https://example.com --output report.json
```

## Constraints

- **Read-only**: No modifications to the target site
- **No authentication**: Only public content
- **Respectful**: Rate-limited requests (200-300ms delays)
- **Runtime**: Full audit completes in under 5 minutes
- **No site-specific rules**: All checks are generic
