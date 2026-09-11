---
name: engagement-audit-orchestrator
description: Entrypoint skill for the brand-engagement-audit marketplace. Given a URL, runs a single consolidated capture-and-check pass (scripts/run_audit.js), judges the site's actual business model by reading the captured content directly (not by threshold-voting on regex signals), selects which category of findings actually applies, deduplicates and prioritizes them, and emits a final on-site-engagement audit report with every severity grounded in a cited study — all within a tight runtime budget so it can run alongside a paired AI-discoverability audit. Use this — not the individual check skills' documentation directly — whenever asked to audit a website's on-site engagement.
license: MIT
allowed-tools:
  - bash
  - http_request
---

# Engagement Audit Orchestrator (entrypoint)

## When to use
This is the only skill invoked directly by the calling agent for an audit request. Scope note: this marketplace covers **on-site engagement only**. It does not evaluate AI/search discoverability (crawlability, structured data for citation, off-site corroboration) — that is a separate concern outside this marketplace's scope, and this skill must not fabricate discoverability findings to pad the report.

## Runtime budget — read this before anything else
This audit shares a total runtime ceiling with a paired AI-discoverability audit, which needs its own time to run its own checks (fetching, parsing, cross-referencing). **Target well under 90 seconds end-to-end** for a typical site, not the full ceiling. Concretely:
- Run `scripts/run_audit.js` **once**, as a single Node process, rather than invoking a separate script per concern. Every check across every category (technical baseline, conversion/friction, retention/content, local trust/leads) is computed in that one pass — the script is cheap enough that it's faster to compute all of them and select afterward than to branch before running.
- The script itself has no external slow dependencies: no browser automation (see the marketplace-wide constraint below), no PageSpeed Insights/Lighthouse API call by default (that API alone can take 10-30+ seconds and has been observed to return quota errors) — performance is measured from the timing of the capture fetch itself, at zero extra network cost.
- Your own reasoning steps (business-model judgment, composing the report, citing research) are the other major time cost — keep `site_understanding` and each `suggested_action` to the length specified below, not sprawling prose, so writing the report doesn't itself become the bottleneck.

## No browser-automation dependency
This entire marketplace — every skill, including this one — must not require Playwright, Puppeteer, Selenium, or any other browser-automation framework to function. That is a hard constraint on what gets submitted, not a preference; using such tools for a team's own local testing while building is fine, but the thing that actually runs must not depend on one. `scripts/run_audit.js` reflects this directly: pure Node.js `fetch`, zero conditional branches that reach for a browser. A handful of checks that would be more precise with real rendering (true mobile tap-target pixel sizes, computed-style sticky-CTA detection, true above-the-fold node counts, live console errors) are permanently out of scope and always listed in `not_evaluated` — see the schema below for how that's surfaced honestly rather than silently.

## Inputs
- `url` (string, required): the site to audit.
- `max_pages` (integer, optional, default 4): passed through to `run_audit.js` — kept small deliberately to protect the runtime budget above; raise it only if the site is small enough that a larger sample won't meaningfully slow things down.

## Procedure

1. **Run the consolidated script once.** Execute `node scripts/run_audit.js <url> [max_pages]`. It returns a single JSON object containing `business_model_evidence` (meta, genre_signals, short text excerpts of the homepage and sampled pages — enough to judge the business model without needing full HTML) and `checks` (all four categories' findings, always computed). If the site is entirely unreachable (DNS failure, timeout, or the homepage fetch throws), stop and emit a report with a single `critical` finding stating the failure and its evidence rather than guessing at engagement quality from nothing.

2. **Judge the business model yourself — do not threshold-vote on `genre_signals`.** Read `business_model_evidence` (title, meta description, homepage/sampled-page text excerpts, JSON-LD-derived signals) the way a human consultant would glance at a site for five seconds, and write one or two sentences stating what this site actually is and how it makes or sustains money — e.g. "a competitive-programming community platform; revenue/sustainability comes from sponsorships and contest partnerships, not direct transactions" or "a direct-to-consumer footwear retailer; the site exists to convert browsing into checkout." This judgment becomes the `site_understanding` field in the final report — a real analytical statement, not a label.
   - Use `genre_signals` as **corroborating evidence only** — cheap, fast pattern hits that support or complicate your read, never the decision itself. A regex can't distinguish a SaaS pricing page from a marketplace's seller-fee page, or a side-project merch store from a platform's actual business model; only reading the excerpt can. If the signals and your own read disagree, trust your read and say so explicitly.
   - From that judgment, decide which `checks.*` category block(s) to actually include in the final report:
     - Business model centers on a completed on-site transaction (buy, sign up, order) → include `checks.conversion_friction`.
     - Business model centers on repeat visits and content/community depth → include `checks.retention_content`.
     - Business model centers on generating an off-platform lead — a call, a booking, a contact-form/quote request, typical of healthcare providers, law firms, contractors, salons, real-estate agents → include `checks.local_trust_leads`.
     - A site can genuinely need more than one category — include every category your own understanding says applies, not because a regex bucket happened to clear a number. `checks.technical_baseline` is always included regardless of business model.
   - Findings in a category you did **not** select are simply left out of the final report — they were computed for cheapness (the script doesn't know your judgment yet when it runs), not because every category is always relevant.
   - If your own read is genuinely ambiguous, say so in `site_understanding`, include the categories that seem most plausible, and be more conservative about which individual findings within them you keep (only ones with strong, directly-observed evidence).

3. **Merge and deduplicate.** Combine the findings from every category you selected. Deduplicate near-identical findings that point at the same root cause from different angles (e.g. a static accessibility finding and a checkout-friction finding both touching the same form) into one finding referencing both symptoms — this directly serves the "few false positives, few misses" detection-accuracy criterion.

4. **Prioritize.** Sort merged findings by severity (`critical` > `high` > `medium` > `low`), and within a tier, by estimated reach (a homepage-level finding affecting every visitor outranks a finding on a single sampled detail page).

5. **Add proactive suggestions.** Beyond the detected findings, include 1-3 `suggested_action`-only recommendations (no matching `finding`) for improvements that would strengthen engagement even where no defect was found. Always include one that names the checks in `not_evaluated` and recommends a rendered/manual follow-up (mobile-usability pass, Lighthouse audit) to cover the rendering-dependent gap this submission intentionally leaves. Keep every suggestion concrete and specific to what was actually observed on this site — never a generic boilerplate list.

6. **Assign IDs and compute summary.** Number findings `F-001`, `F-002`, ... in final priority order. Compute `summary.total_findings` and per-severity counts (`critical`, `high`, `medium`; include `low` as an additional key beyond the schema floor).

7. **Ground every severity in cited research, not intuition — most of this is already done for you.** `run_audit.js`'s findings already weave a citation into `suggested_action.summary` wherever `references/research-basis.md` has one that applies (performance/bounce, checkout friction, reviews/conversion, dark patterns, lead-response time, local trust, accessibility). When composing `proactive_suggestions` yourself (which the script cannot generate, since they require judgment about what's missing rather than what's wrong), apply the same standard: cite a source and its actual figure where one genuinely fits, and never force one where it doesn't.

8. **Surface coverage gaps honestly.** Copy `not_evaluated` from the script's output into `coverage_gaps` in the final report, each with a one-line reason (they all share the same reason: rendering-dependent, out of scope for this submission's no-browser-automation constraint). This is a statement about audit completeness, not a finding about the site, and keeping it separate prevents a coverage gap from being misread as either a defect or a clean bill of health.

9. **Emit the report** in the exact schema below — a hard requirement, since the report is meant to be machine-parseable by whatever invoked this audit.

## Output schema (required; may be extended, never reduced)
```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "scope": "on-site-engagement",
  "site_understanding": "A direct-to-consumer footwear retailer; the site exists to convert browsing sessions into completed checkouts, not to sustain a content or community habit.",
  "genre_signals": { "ecommerce": 0, "news": 0, "saas": 0, "food": 0, "community": 0 },
  "summary": { "total_findings": 6, "critical": 0, "high": 2, "medium": 3, "low": 1 },
  "findings": [
    {
      "id": "F-001",
      "title": "No visible total/shipping cost on checkout page",
      "severity": "high",
      "evidence": "No price/total/shipping text pattern found on /checkout.",
      "suggested_action": {
        "summary": "Show full cost including shipping before the final step. Baymard Institute's meta-analysis of 4,500+ checkouts puts unexpected extra costs as the single largest abandonment driver (~48%).",
        "priority": "high"
      }
    }
  ],
  "proactive_suggestions": [
    { "summary": "This audit could not evaluate mobile tap-target sizing or sticky-CTA behavior (no browser rendering is used in this submission) — recommend a Lighthouse mobile pass or manual device testing to cover this gap.", "priority": "medium" }
  ],
  "coverage_gaps": [
    { "check": "mobile_tap_targets", "reason": "Requires rendering a real viewport; this submission uses no browser-automation framework by design." }
  ]
}
```
`site_understanding` is always present and is never a genre label alone — it is the actual judgment call from step 2, stated as a sentence a human reviewer could agree or disagree with. `coverage_gaps` is always non-empty and always the same four checks, since this is a fixed, permanent scope decision, not a per-run environment difference.

## Composition notes for the report author
- Every `evidence` string must be traceable to a concrete measurement or a specific sampled URL — never a bare assertion like "checkout is confusing."
- Do not include any finding whose category belongs to AI discoverability (crawlability, structured data for citation purposes, cross-site corroboration) — this marketplace's declared scope is on-site engagement only.
- Judgment calls (business model, dark-pattern intent, whether copy is manipulative) belong to your own reasoning, informed by but never delegated to a regex signal — that division of labor (the script measures, you judge) is the core design principle of this entire marketplace, not just step 2.
