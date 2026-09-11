---
name: engagement-retention-content
description: Documents the content-and-return-loop engagement checks that matter for sites where value comes from repeated visits and content depth rather than a single transaction — news/media publishers and community/social/forum platforms. Covers related-content discovery (grounded in Chartbeat's Engaged Time research), ad density, freshness, onboarding clarity for specialized systems, and return-trigger infrastructure. Implementation lives in the orchestrator's consolidated script; selected by the orchestrator's own read of the site's business model.
license: MIT
allowed-tools:
  - bash
---

# Engagement: Retention & Content

## When to use
Included when the orchestrator's own judgment (see `engagement-audit-orchestrator/SKILL.md` step 2) concludes the site's engagement model centers on repeat visits and content/community depth rather than a single transaction. `genre_signals` (`news`/`community`) are supporting evidence, not a standalone trigger.

## Implementation
Every check below is implemented in `engagement-audit-orchestrator/scripts/run_audit.js` (`checkRelatedContentModule`, `checkAdDensity`, `checkFreshness`, `checkOnboardingHelp`, `checkReturnTriggers`), computed once as part of the single consolidated pass.

## Checks and their rationale

1. **Related-content / next-action modules.** Flags article pages with no related-content block after the main content. Cited against **Chartbeat's Engaged Time research**: near-identical pageview counts hid a 91%-vs-7% gap in real reader engagement across two articles — extending a session past the first page is the metric that matters, not raw traffic.

2. **Ad density (news genre).** Flags articles where ad-slot markers exceed half the count of paragraph blocks — a well-documented, fast-acting bounce driver on publisher sites.

3. **Freshness.** Flags a stale homepage/feed (newest dated JSON-LD item older than 48h) for sites scoring high on the `news` signal.

4. **Onboarding clarity for specialized systems.** Flags a displayed reputation/rank/karma system with no in-context explanation (tooltip, help link) reachable nearby — invisible friction for new users that veteran users and the site's own team will never notice on their own.

5. **Return-trigger infrastructure.** Flags the absence of any detectable notification mechanism as a low-severity, evidence-only opportunity — some sites intentionally rely on habitual direct visits instead, so this is framed as a suggestion, not a defect.

## Output
Same finding-object shape as every other category.
