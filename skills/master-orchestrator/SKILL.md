---
name: master-orchestrator
description: Single entrypoint for the Brand AI Readiness Audit marketplace. Runs both the on-site engagement audit (Node.js) and the AI discoverability audit (Python) against a target URL, then merges their findings into one unified, schema-compliant JSON report. Use this — not the individual skills directly — whenever asked to audit a website.
license: MIT
allowed-tools:
  - bash
  - http_request
---

# Master Orchestrator (entrypoint)

## When to use
This is the **only** skill invoked directly by the calling agent for an audit request. It coordinates two independent audit passes — on-site engagement and AI discoverability — and merges their output into one unified report.

## Runtime budget
Target under 5 minutes total for both audit passes combined. The engagement pass typically completes in under 90 seconds; the discoverability pass runs the remaining mechanisms sequentially.

## No browser-automation dependency
This entire marketplace must not require Playwright, Puppeteer, Selenium, or any other browser-automation framework to function. All scripts use pure HTTP requests (Node.js `fetch` for engagement, Python `requests` for discoverability).

## Inputs
- `url` (string, required): the site to audit.

## Procedure

### Pass 1: On-Site Engagement
1. Execute `node skills/engagement-audit-orchestrator/scripts/run_audit.js <url>` from the repo root. It returns a JSON object containing `business_model_evidence` and `checks` (all four engagement categories computed).
2. Judge the business model yourself by reading `business_model_evidence` — see `skills/engagement-audit-orchestrator/SKILL.md` steps 2-8 for the full procedure. Use `genre_signals` as corroborating evidence only, never the decision-maker.
3. Select which engagement check categories to include based on your judgment, merge, deduplicate, prioritize, cite research, and add 1-3 proactive suggestions. Always include one proactive suggestion about the rendering-dependent checks in `not_evaluated`.

### Pass 2: AI Discoverability
4. Execute `python skills/master-orchestrator/scripts/run_discoverability_audit.py <url>` from the repo root. It runs all discoverability mechanisms (A through F) and returns a JSON object containing mechanism results and findings.
5. Take the `findings` array from the discoverability output as-is — they are already formatted with `id`, `title`, `severity`, `evidence`, and `suggested_action`.

### Merge
6. Combine the engagement findings (from step 3) and discoverability findings (from step 5) into one unified `findings` array. Prefix engagement finding IDs with `E-` (e.g., `E-001`) and keep discoverability IDs as-is (e.g., `A-001`, `H-SS1`).
7. Compute `summary.total_findings` and per-severity counts across both sets.
8. Set `scope` to `"full-audit"` (covering both engagement and discoverability).

## Output schema (required)
```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "scope": "full-audit",
  "site_understanding": "A direct-to-consumer footwear retailer; the site exists to convert browsing sessions into completed checkouts.",
  "genre_signals": { "ecommerce": 0, "news": 0, "saas": 0, "food": 0, "community": 0 },
  "summary": { "total_findings": 10, "critical": 1, "high": 3, "medium": 4, "low": 2 },
  "findings": [
    {
      "id": "E-001",
      "title": "On-site engagement finding title",
      "severity": "high",
      "evidence": "Concrete evidence string.",
      "suggested_action": { "summary": "Fix description with cited research.", "priority": "high" }
    },
    {
      "id": "A-001",
      "title": "AI discoverability finding title",
      "severity": "medium",
      "evidence": "Concrete evidence string.",
      "suggested_action": { "summary": "Fix description.", "priority": "medium" }
    }
  ],
  "proactive_suggestions": [
    { "summary": "Proactive improvement suggestion.", "priority": "medium" }
  ],
  "coverage_gaps": [
    { "check": "mobile_tap_targets", "reason": "Requires rendering a real viewport; this submission uses no browser-automation framework by design." }
  ]
}
```

## Composition notes
- Every `evidence` string must be traceable to a concrete measurement or a specific sampled URL.
- Engagement findings follow the citation standard in `skills/engagement-audit-orchestrator/references/research-basis.md`.
- Discoverability findings follow their own hypothesis-based severity model.
- `site_understanding` is always present and is the engagement orchestrator's business-model judgment.
- `coverage_gaps` is always non-empty (the four rendering-dependent engagement checks).
