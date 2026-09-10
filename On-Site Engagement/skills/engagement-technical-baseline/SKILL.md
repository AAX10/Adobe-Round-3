---
name: engagement-technical-baseline
description: Documents the business-model-agnostic engagement checks that apply to every audited site — response-time-based performance signal, static accessibility screening grounded in the WebAIM Million 2026 benchmark, and homepage complexity as a page-density proxy. Uses no browser-automation framework; implementation lives in the orchestrator's consolidated script. Always included in the final report regardless of business model.
license: MIT
allowed-tools:
  - bash
---

# Engagement Technical Baseline

## When to use
Always included, for every site, regardless of business model. This is the layer most likely to hide the single biggest problem, because it fails silently — a visually polished site can still be losing most visitors to a slow response time, and no business-model-specific check will surface that.

## Implementation
Every check below is implemented in `engagement-audit-orchestrator/scripts/run_audit.js` (`checkPerformanceFromTiming`, `checkStaticAccessibility`, `checkHomepageComplexity`), computed once as part of the single consolidated pass. This file documents what each check does and why.

## Checks and their rationale

1. **Performance, from fetch timing (not a Lighthouse/PSI call).** Measures the elapsed time of the homepage fetch the capture step was already making — zero extra network cost, and avoids a known-slow, quota-limited external dependency (PageSpeed Insights was observed returning HTTP 429 in testing, and can take 10-30+ seconds per call even when it works). This is a response-time proxy, not a full Core Web Vitals measurement — the finding says so explicitly. Cited against **Google/SOASTA's mobile research** (2016-17): bounce probability rises 123% as load time goes from 1s to 10s; 53% of visitors abandon a page taking longer than 3s.

2. **Static accessibility screening.** Text-pattern checks against raw HTML for the two failure categories that are both common and detectable without rendering: `<img>` tags with no `alt` attribute at all, and `<input>` elements with no associated label/aria-label. This is explicitly a lighter screen than a full axe-core/WAVE scan (no color-contrast or focus-order checks, which need rendering) — the finding says so. Cited against the **WebAIM Million 2026** report: missing alt text on over half of home pages studied, unlabeled form inputs on 51%, at least one detectable WCAG 2 A/AA failure on 95.9% of pages overall — framing every finding against that honest baseline rather than implying zero errors is the norm.

3. **Homepage complexity as a page-density proxy.** Compares total tag count on the homepage against the sampled internal pages' average, and checks for a short, distinct button/link near the top of the markup as a proxy for a clear primary call-to-action. Explicitly not true above-the-fold measurement (that needs a rendered viewport) — the finding says so. Cited against **Google/SOASTA**: conversion probability drops 95% as page element count rises from 400 to 6,000.

4. **Permanently out-of-scope, not guessed.** Mobile tap-target sizing, true above-the-fold node counts, computed-style sticky detection, and live console errors all require rendering, which this submission does not use. These are never approximated with an unreliable static guess — they're listed in `not_evaluated` and the orchestrator adds one consolidated proactive suggestion recommending a manual/Lighthouse mobile pass instead.

## Output
Same finding-object shape as every other category.
