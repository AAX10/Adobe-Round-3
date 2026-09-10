---
name: site-capture
description: Documents the capture phase — fetching a target URL over plain HTTP (no browser automation), extracting HTML metadata and structured signals (JSON-LD, genre patterns) used by every engagement check. Implementation is part of the orchestrator's single consolidated script (run_audit.js); this file documents the approach and what gets captured.
license: MIT
allowed-tools:
  - bash
---

# Site Capture (phase documentation)

## Overview
Every engagement audit starts with a single, consistent snapshot of the target site: homepage HTML, sampled internal pages, extracted metadata, and text/schema signals. Rather than each skill re-fetching the site (slow, inconsistent), the orchestrator's consolidated `run_audit.js` does capture once and passes the evidence to every check.

## What gets captured

1. **Homepage fetch** (plain HTTP, no rendering): response time, raw HTML, extracted JSON-LD blocks, meta tags, and basic page metadata (title, description, lang, viewport meta presence).

2. **Internal-page sample** (up to 4 by default, concurrently fetched with limits to avoid hammering the server):
   - Prioritized toward pages that look like actual content (articles, products, contests, profiles) over generic nav/utility links
   - Robots.txt-respecting
   - Read-only (no form submissions, no logins)
   - Filtered for `text/html` content-type to skip redirects to non-HTML resources

3. **Extracted signals for business-model judgment**:
   - `genre_signals`: regex/schema hit-counts for ecommerce, news, saas, food, community business patterns — cheap corroborating evidence for the orchestrator's own reading of the site
   - Short text excerpts (500 chars of homepage, 250 chars per sampled page) — enough to read and judge the business model without shipping full HTML back
   - JSON-LD parsed blocks (used for rating/review data, structured article metadata, etc.)

## Implementation constraints (no-browser, budget-aware)

- **No browser-automation framework ever**: pure Node.js `fetch`, zero conditional branches that reach for Playwright/Puppeteer/Selenium. This is a hard submission constraint, not a fallback — a team can use such tools for local testing, but the submitted skill must not depend on one.
- **Cheap**: captures what can be extracted from raw HTML and simple text patterns, without trying to measure computed styles, true above-the-fold rendering, or console errors. Checks that genuinely need rendering (mobile tap targets, sticky-CTA detection, true node counts) are permanently listed in `not_evaluated`.
- **Respectful concurrency**: internal pages fetched 3 at a time with individual timeouts, not fully sequential (slow) or unlimited parallel (rude). Each page has a 6-second fetch timeout so one slow page can't stall the whole audit.
- **Quick**: homepage fetch + sample crawl targeted to complete in <30 seconds total, leaving the majority of the audit's 90-second runtime budget for downstream checks and orchestrator judgment.

## Output shape
```json
{
  "site": "example.com",
  "business_model_evidence": {
    "meta": { "title": "...", "description": "...", "lang": "...", "has_viewport_meta": true },
    "genre_signals": { "ecommerce": 0, "news": 3, "saas": 0, "food": 0, "community": 2 },
    "homepage_excerpt": "first 500 chars of visible text",
    "sampled_pages": [
      { "url": "...", "role_guess": "listing|detail|article|other", "excerpt": "first 250 chars" }
    ]
  },
  "not_evaluated": ["mobile_tap_targets", "above_fold_node_count_true_viewport", "sticky_cta_computed_style", "console_errors"],
  "checks": {
    "technical_baseline": [ ... ],
    "conversion_friction": [ ... ],
    "retention_content": [ ... ],
    "local_trust_leads": [ ... ]
  }
}
```

The orchestrator reads `business_model_evidence` to judge the business model and select which `checks.*` categories to include in the final report. All four check categories are always computed (cheap to do upfront) but only the relevant ones appear in the final output.
