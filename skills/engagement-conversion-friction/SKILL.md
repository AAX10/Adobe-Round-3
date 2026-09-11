---
name: engagement-conversion-friction
description: Documents the transaction-oriented engagement checks that matter for sites where the visit is meant to end in a discrete action — e-commerce checkout, SaaS signup/demo request, food/delivery ordering. Covers product/menu imagery quality, a static heuristic for sticky-CTA and checkout friction, trust/social-proof visibility (including the Northwestern Spiegel Research Center's finding that near-perfect ratings reduce trust), delivery-time transparency, and a structured 7-category dark-pattern check based on the Princeton/Mathur et al. 2019 taxonomy. Implementation lives in the orchestrator's consolidated script; selected by the orchestrator's own read of the site's business model, not a fixed keyword threshold.
license: MIT
allowed-tools:
  - bash
---

# Engagement: Conversion & Friction

## When to use
Included in the final report when the orchestrator's own judgment (see `engagement-audit-orchestrator/SKILL.md` step 2) concludes the site's engagement model centers on a completed transaction — buying, signing up, or ordering. `genre_signals` (`ecommerce`/`saas`/`food`) are supporting evidence for that judgment, not a standalone trigger. These three business shapes share a common pattern when they do apply — a visitor moving toward one discrete committing action — so the same friction/trust logic generalizes across them even though the surface UI differs.

## Implementation
Every check below is implemented as a function in `engagement-audit-orchestrator/scripts/run_audit.js` (`checkMediaQuality`, `checkStickyCtaStatic`, `checkCheckoutFrictionStatic`, `checkTrustSignals`, `checkDeliveryTransparency`, `checkDarkPatterns`), run once as part of that single consolidated pass rather than as a separate script — see the orchestrator's runtime-budget note for why. This file documents what each check does and why, for review and composition purposes; it is not re-implemented here.

## Checks and their rationale

1. **Media quality.** Flags detail pages with fewer than 2 images — food and fashion/footwear purchases are driven by visual confidence, so this is a conversion problem, not a cosmetic one.

2. **Sticky primary-action CSS (static heuristic).** Since this submission uses no browser-automation framework, this cannot measure computed styles the way a rendered check could. Instead it does a static text match for a CSS rule pairing `position: sticky`/`fixed` with a cart/CTA-like selector. Absence is flagged **low severity** (not high) specifically because a real sticky rule applied via an externally-linked stylesheet or JS is invisible to this heuristic — the finding says as much and recommends manual verification rather than asserting the CTA definitely isn't sticky.

3. **Checkout friction (static link-tracing).** Looks for a sampled `/cart` or `/checkout` page and counts its form fields, checks for account-creation language without a nearby "guest" option, and checks whether total cost (incl. shipping) is visible. All three are grounded in **Baymard Institute's meta-analysis of 4,500+ checkouts**: forced account creation ~26% of actionable abandonment, checkout length/complexity ~22%, unexpected extra costs ~48% (the single largest driver). This is a static approximation of what a live click-through would show — it can only see what's reachable via plain links in the sampled pages, not a flow requiring an actual click/JS interaction to reveal.

4. **Trust and social-proof visibility.** Checks for `AggregateRating` JSON-LD or review/rating text. Absence is flagged citing **Northwestern's Spiegel Research Center**: the first review alone lifts conversion ~65%, five reviews correspond to ~270% higher purchase likelihood. A near-perfect rating (≥4.95) on a very small sample (<10 reviews) is flagged separately, low severity, evidence-only — the same research found trust actually peaks around 4.2–4.5 stars, since a suspiciously perfect small-sample rating reads as curated rather than genuine. Worded as "worth confirming authenticity," never an accusation.

5. **Delivery/turnaround transparency (food only).** Flags the absence of any time-estimate pattern near ordering content when `genre_signals.food` is high — unset expectations are a leading cause of one-time-only usage in this category specifically.

6. **Dark-pattern check — structured, evidence-based, never an accusation.** Text-matches for three of the seven categories in Mathur et al.'s peer-reviewed **"Dark Patterns at Scale"** (ACM CSCW 2019, ~53K pages / ~11K sites crawled): Urgency (countdown/limited-time language), Scarcity (low-stock/viewer-count claims), and Social Proof (real-time purchase notifications). Every match is flagged **medium severity, evidence-only**, with the fix always framed as "verify this claim is accurate and remove/fix if not" — the same study is explicit that real scarcity and real social proof aren't dark patterns, only fabricated versions are, and this check cannot verify truthfulness, only presence.

## Output
Same finding-object shape as every other category. Each finding states which page it was observed on, so the orchestrator's evidence strings stay traceable.
