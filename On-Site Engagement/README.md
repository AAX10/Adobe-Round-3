# brand-engagement-audit

An Agent Skill Marketplace that audits a website's **on-site engagement** (why visitors who arrive don't stay) and emits a prioritized findings report, all within a shared runtime budget so it can run alongside a paired AI-discoverability audit. **Scope note**: this marketplace covers on-site engagement only. It does not evaluate AI/search discoverability (crawlability, structured data for citation, off-site corroboration) — that is a separate concern.

## What makes this different

1. **Business-model judgment is a reasoning step, not a regex vote.** Most audit tools classify a site by scoring keyword/schema hits against fixed thresholds and picking whichever bucket wins. That approach can't tell a SaaS pricing page from a marketplace's seller-fee page, or a side-project merch store from a community platform's actual business model — only reading the content can. The orchestrator reads the captured homepage and sampled pages (short text excerpts, not full HTML) the way a human consultant would glance at a site for five seconds, and writes an actual judgment (`site_understanding` in the report) that a reviewer could agree or disagree with. `genre_signals` (regex/schema hit-counts) still get computed — they're cheap and fast — but they're corroborating evidence for that judgment, never the decision-maker.

2. **Every severity is grounded in a cited study, not intuition.** Load-time thresholds cite Google/SOASTA's mobile bounce-rate research; checkout friction severities cite Baymard Institute's meta-analysis of 4,500+ checkouts; review/trust findings cite Northwestern's Spiegel Research Center; the dark-pattern check uses the peer-reviewed 7-category taxonomy from Mathur et al. (ACM CSCW 2019); lead-response-time findings cite MIT/InsideSales.com and Harvard Business Review; local-trust findings cite BrightLocal's 2026 survey; and the accessibility check is framed against the WebAIM Million 2026 benchmark (95.9% of the top 1M home pages have at least one detectable WCAG failure). Full citations live in `engagement-audit-orchestrator/references/research-basis.md`. Not every check gets a citation — purely structural checks (form field counts) are left uncited rather than forcing a study onto a claim that's already self-evidently true.

3. **Single consolidated process, not five separate scripts.** Earlier designs had a separate script file per skill, each invoked as its own subprocess — overhead that eats directly into the shared runtime budget. This redesign runs capture + all four check categories in one Node process (`scripts/run_audit.js`), computed once, with the orchestrator selecting which categories to include in the final report based on its own business-model judgment. Result: clean decomposition (each skill's SKILL.md still documents its own checks and reasoning in full) with zero subprocess/permission-prompt overhead.

4. **Tight runtime budget.** Target well under 90 seconds end-to-end for a typical site, leaving the majority of any shared 5-minute ceiling to an AI-discoverability audit running alongside. No browser-automation framework (Playwright, Puppeteer, Selenium) anywhere — that's a hard submission constraint, not a preference. No PageSpeed Insights/Lighthouse API call by default (known source of slowness and quota errors) — performance is measured from the timing of the capture fetch itself, at zero extra network cost.

## Skills and composition

| Skill | Role |
|---|---|
| `engagement-audit-orchestrator` (**entrypoint**) | Receives the audit request, invokes the consolidated script, reads the business-model evidence to judge which category(ies) apply, selects the relevant findings, deduplicates/prioritizes them, cites research, adds proactive suggestions, and emits the final schema-compliant report. |
| `site-capture` | Documentation of the capture phase — fetching the homepage over plain HTTP, sampling internal pages (robots.txt-respecting, read-only, concurrency-limited), extracting metadata and genre signals. Implementation is now part of the orchestrator's consolidated script, not a separate subprocess. |
| `engagement-technical-baseline` | Documentation of business-model-agnostic checks: response-time performance signal, static accessibility screening (grounded in WebAIM Million 2026), homepage complexity as a page-density proxy. Always included in every report. |
| `engagement-conversion-friction` | Documentation of transaction-focused checks: media quality, static sticky-CTA heuristic, checkout friction, trust/review visibility (grounded in Spiegel Research), delivery-time transparency, dark-pattern honesty check (Mathur et al. taxonomy). Included when the orchestrator's business-model judgment identifies a transaction-focused site. |
| `engagement-retention-content` | Documentation of content/community checks: related-content modules (grounded in Chartbeat Engaged Time research), ad density, freshness, onboarding clarity for specialized systems, return-trigger infrastructure. Included when the orchestrator's business-model judgment identifies a repeat-visit site. |
| `engagement-local-trust-leads` | Documentation of lead-generation checks: contact/booking accessibility, stated response-time expectations (MIT/InsideSales.com and HBR research), on-site review visibility (BrightLocal survey), real-organization credibility signals. Included when the orchestrator's business-model judgment identifies a local/professional-services site. |

Each skill's SKILL.md is documentation of what its checks do and why — it is not re-implemented as a separate script. The actual logic for all checks lives in `engagement-audit-orchestrator/scripts/run_audit.js`, run once per audit.

## How the entrypoint composes the others

```
url
 │
 ▼
run_audit.js ──► capture (homepage, 4 sampled pages, genre_signals, excerpts) + 4 check categories (all computed)
 │
 ▼
orchestrator reads business_model_evidence (meta, genre_signals, text excerpts)
 │
 ├─► judges the actual business model (not a threshold vote on genre_signals)
 │
 ├─► includes technical_baseline findings (always)
 │
 ├─(if transaction-focused)─► + conversion_friction findings
 │
 ├─(if retention/content-focused)─► + retention_content findings
 │
 ├─(if lead-gen/local)─► + local_trust_leads findings
 │
 └─► merges, dedupes, prioritizes, cites research, adds suggestions, emits report
```

## Runtime budget design — why this matters

`run_audit.js` is designed to complete in well under 90 seconds for a typical site, not the full 5-minute ceiling. Why? Because this marketplace was built to run **alongside** an AI-discoverability marketplace on the same site, within a shared runtime limit. If engagement-audit consumed 3+ minutes just on page fetching and checks, discoverability would be starved for time.

Specifically:
- **No browser install ever** — the moment you `npm install playwright` + download Chromium on a cold environment, you've already burned several minutes of budget before a single actual check runs. This marketplace never does that: pure Node.js `fetch`, zero conditional branches reaching for a browser.
- **Capture + checks in one pass** — no separate subprocess invocations per skill, no permission prompts in an agent UI, no duplication of fetches or parsing logic.
- **No external API calls by default** — PageSpeed Insights / Lighthouse APIs can take 10-30+ seconds per call and have been observed to return quota errors (HTTP 429). Performance is instead measured from the capture fetch itself.
- **Small sample size** (4 internal pages by default, not 20+) — enough to spot patterns in most sites, fast to crawl.

Checks that would genuinely require rendering (mobile tap targets, true above-the-fold counts, sticky-element detection via computed styles, console errors) are permanently listed as `not_evaluated` in the final report, paired with a proactive suggestion recommending a manual Lighthouse/mobile-device follow-up. This is honest: "we couldn't measure this, here's why, here's how to cover the gap" beats silently guessing.

## Guardrails honored throughout

- **Recommend-only.** No skill submits a final form, logs in, creates an account, enters payment details, or otherwise alters any live site state.
- **robots.txt respected** by the capture phase before any internal-page sampling.
- **Deterministic where it counts, reasoning where it should.** Every objectively measurable quantity (response time, tag count, form field count, regex matches) is computed by fixed logic — same input, same output, every run. Business-model judgment, dark-pattern intent, and fresh-vs-stale decisions are explicitly left to the agent's own reading of the content.
- **No external service required** to resolve the manifest or run the audit (apart from the target site itself, and optionally a Lighthouse API for a *future* enhanced version, but not in this submission).
