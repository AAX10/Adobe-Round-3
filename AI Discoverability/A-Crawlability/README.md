# A — Crawlability Hypotheses

## Overview

These three hypotheses cover distinct failure modes in the **crawl** mechanism — the first gate in the machine discovery pipeline. If any of these failures occur, content cannot proceed to the read or extract stages.

## Why These Are Distinct

| Hypothesis | Failure Mode | Gate | Observable At |
|-----------|-------------|------|---------------|
| **A-001** | Explicit exclusion via robots.txt | Permission gate | robots.txt parsing |
| **A-002** | Absence from crawlable link graph | Discovery gate | Link graph comparison |
| **A-003** | HTTP retrieval failure | Retrieval gate | HTTP response codes |

These three hypotheses represent three different stages of the crawl process:

1. **A-001 (Permission)**: The crawler is *told not to* access the content — a policy-level block.
2. **A-002 (Discovery)**: The crawler *cannot find* the content — the URL never enters the crawl queue because it's not in any crawlable link or sitemap.
3. **A-003 (Retrieval)**: The crawler *finds the URL* but *cannot retrieve* the content — the server fails to return a usable response.

A page can fail at any one of these gates independently. A page can pass A-001 (not blocked by robots) but fail A-002 (not linked). A page can pass both A-001 and A-002 but fail A-003 (linked and permitted, but returns 500).

## Strength Assessment

| Hypothesis | Quality Score | Classification | Strength |
|-----------|--------------|----------------|----------|
| **A-001** | 4.9 | CORE | Strongest — RFC 9309 makes this a hard, standards-defined gate |
| **A-003** | 4.8 | CORE | Strong — HTTP status codes are unambiguous |
| **A-002** | 4.2 | CORE | Good — requires rendering for full comparison, but well-supported |

## Evidence Required

### A-001
- robots.txt fetch and parse
- URL-to-rule matching
- Importance classification of blocked URLs
- False-positive filtering (admin paths)

### A-002
- Static link graph extraction
- Sitemap parsing
- Rendered link graph extraction (requires headless browser)
- Comparison of static vs rendered link sets
- Importance classification of render-only URLs

### A-003
- Bounded HTTP requests to sampled URLs
- Status code recording
- Retry for persistence classification
- Redirect chain tracking

## How They Become Reusable Checks

All three hypotheses map to deterministic scripts that can run on any public website:

1. `robots_audit.py` — fetch robots.txt, parse rules, test URLs → A-001
2. `link_discovery_audit.py` — parse links, check sitemap, compare rendered → A-002
3. `url_retrieval_audit.py` — sample URLs, request, record status → A-003
4. `crawlability_report.py` — aggregate findings into structured report

These scripts share a common output schema and can be composed by an orchestrator skill.
