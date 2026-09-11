---
name: engagement-local-trust-leads
description: Documents the trust-and-lead-capture engagement signals that matter for local and professional-services businesses — dentists, clinics, law firms, contractors, salons, real-estate agents, home-service providers — where the visit is meant to end in a call, booking, or contact-form submission off-platform. Covers contact/booking accessibility, stated response-time expectations (grounded in MIT/InsideSales and Harvard Business Review lead-response-time research), on-site review/trust signals (grounded in BrightLocal's Local Consumer Review Survey), and real-organization credibility signals. Implementation lives in the orchestrator's consolidated script; selected by the orchestrator's own read of the site's business model.
license: MIT
allowed-tools:
  - bash
---

# Engagement: Local Trust & Lead Capture

## When to use
Included when the orchestrator's own judgment (see `engagement-audit-orchestrator/SKILL.md` step 2) concludes the site exists to generate an off-platform lead — a phone call, a booking, a contact-form or quote request — rather than to process an on-site checkout or sustain a content/community habit. This is a genuinely distinct business-model shape from both other categories: nothing is purchased on-site, and there's no feed to nurture.

## Implementation
Every check below is implemented in `engagement-audit-orchestrator/scripts/run_audit.js` (`checkContactAccessibility`, `checkResponseTimeExpectation`, `checkOnSiteReviewSignalLocal`, `checkRealOrganizationSignals`), computed once as part of the single consolidated pass.

## Checks and their rationale

1. **Contact/booking accessibility.** Flags a phone number shown as plain text without a `tel:` link — a one-tap-to-call opportunity lost for free on mobile. Also flags the absence of any booking/contact link reachable within one click of the homepage, since every additional click a prospective lead has to take is a chance for them to leave and call a competitor instead.

2. **Stated response-time expectation.** Flags the absence of any language indicating how quickly an inquiry will be answered ("we respond within 1 hour," live-chat availability, stated business hours). Grounded in real research: the **MIT/InsideSales.com Lead Response Management Study** (Oldroyd, 2007; 15,000+ leads across six companies) found contacting a lead within 5 minutes makes a business ~21x more likely to qualify it than waiting 30 minutes. The follow-up **Harvard Business Review study** (Oldroyd, McElheran & Elkington, 2011; 2,241 US firms audited) found the average firm takes 42 hours to respond and only 37% respond within an hour — firms that do respond within an hour are ~7x more likely to qualify the lead than those who wait. A site that sets no expectation at all is both quietly signaling "we may be one of the slow ones" and giving the visitor no reason to wait rather than call the next search result.

3. **On-site review/trust signal visibility.** Flags the absence of reviews or an aggregate rating on the site itself (via AggregateRating JSON-LD or rendered widget) — requiring a visitor to leave the site to verify trust is a visitor who may not come back. Cited against **BrightLocal's Local Consumer Review Survey 2026**: ~97% of consumers read reviews before choosing a local business, and 47% won't consider one with fewer than 20 visible reviews. A near-perfect rating on a small sample is flagged separately, evidence-only, as "worth confirming authenticity" — the same research found trust actually peaks around 4.2–4.5 stars.

4. **Real-organization credibility signals** (physical address, named staff, licensing/certification badges). Flagged as low-severity opportunity, not a defect — **Stanford's Persuasive Technology Lab web-credibility research** consistently found these among the most-cited trust factors visitors use to judge whether a business is trustworthy enough to contact.

## Output
Same finding-object shape as every other category.
