# Research basis for this marketplace's checks and severities

Every severity level and every `suggested_action` framing in this marketplace is
grounded in a specific, citable study rather than intuition. This file is the
single source of truth for those citations — check skills reference it by name
rather than restating figures inline, so a correction only has to happen once.

## Performance → bounce/conversion

- **Google/SOASTA, "Why Marketers Should Care About Mobile Page Speed" (2016)**:
  40% of consumers abandon a page taking longer than 3 seconds to load; 79% of
  shoppers dissatisfied with site performance say they're less likely to
  purchase from that site again.
- **Google/SOASTA neural-network study (2017, 90% prediction accuracy)**: bounce
  probability rises 123% as load time goes from 1s to 10s. Independently, as
  page element count goes from 400 to 6,000, conversion probability drops 95%.
  DOM-ready time (not full page load) was found to be the strongest single
  predictor of bounce.
- **Pingdom analysis of the same Google data**: a page 2 seconds slower than an
  optimal baseline sees bounce rise from ~40% to ~53%; another 2 seconds slower
  again and bounce reaches ~76%.

Used in: `engagement-technical-baseline` (performance, above-fold density).

## Checkout / signup friction → abandonment

- **Baymard Institute, meta-analysis of 50 studies / 4,500+ checkouts (updated
  2025)**: average cart abandonment is ~70%. Of abandoners citing an
  actionable (non-"just browsing") reason: unexpected extra costs ~48%, forced
  account creation ~26%, checkout too long/complicated ~22%, distrust of
  payment security ~18%, total cost not shown upfront ~17%. Baymard's own
  usability testing shows checkout UX fixes alone can yield up to a 35.26%
  conversion lift.

Used in: `engagement-conversion-friction` (checkout friction, guest-checkout,
cost transparency).

## Reviews / social proof → conversion

- **Northwestern University Spiegel Research Center (with PowerReviews),
  "How Online Reviews Influence Sales" (2017) and a follow-up study of 57,000
  products**: the first review alone lifts conversion ~65% versus zero
  reviews; five reviews correspond to ~270% higher purchase likelihood than
  none; the effect is larger for higher-priced items (up to ~380%). Purchase
  likelihood peaks at a 4.2–4.5 star average, not a perfect 5.0 — near-perfect
  ratings measurably reduce trust because shoppers suspect curation or fake
  reviews.

Used in: `engagement-conversion-friction` (trust/review signals — including a
new check for suspiciously perfect ratings, not just absent ones).

## Dark patterns → deceptive engagement

- **Mathur, Acar, Friedman, Lucherini, Mayer, Chetty, Narayanan — "Dark
  Patterns at Scale: Findings from a Crawl of 11K Shopping Websites,"
  Proc. ACM Hum.-Comput. Interact. 3, CSCW (2019)**, a peer-reviewed,
  large-scale empirical crawl of ~53K product pages across ~11K sites. Found
  1,818 dark pattern instances across **7 categories**: Urgency, Scarcity,
  Social Proof, Misdirection, Sneaking, Obstruction, and Forced Action —
  present on ~11.1% of shopping sites studied. This is the taxonomy used
  (rather than an invented one) precisely because it is peer-reviewed and
  empirically derived at scale, not because every instance the paper counted
  is necessarily deceptive — real scarcity and real social proof are not
  dark patterns, only fabricated versions are, which is why every dark-pattern
  finding in this marketplace is worded as a request to *verify authenticity*
  rather than an accusation of bad faith.

Used in: `engagement-conversion-friction` (urgency/scarcity honesty check,
now upgraded to the full 7-category taxonomy as a structured check rather
than a single note).

## Attention / engagement quality (news & community)

- **Chartbeat, "Using Engaged Time to Understand Your Audience"**: pageview
  counts hide wildly different engagement — two articles with near-identical
  traffic had 91% vs. 7% of visitors actually scroll-engaging with the
  content. Chartbeat's "Engaged Time" metric (active scrolling/typing/mouse
  movement in a foregrounded tab) is a materially better engagement signal
  than raw time-on-page or pageviews.

Used in: `engagement-retention-content` (reframes freshness/related-content
checks around genuine engagement signals rather than presence/absence alone,
and justifies why scroll-depth-style modules — reading progress, related
content — matter more than they might first appear).

## Lead response time → lead qualification (local/professional services)

- **MIT/InsideSales.com, "Lead Response Management Study" (Oldroyd, 2007)**:
  analysis of 15,000+ leads and 100,000+ call attempts across six companies
  found the odds of successfully contacting a lead drop ~100x, and the odds
  of qualifying it drop ~21x, when response is attempted at 30 minutes versus
  5 minutes after submission.
- **Harvard Business Review, "The Short Life of Online Sales Leads" (Oldroyd,
  McElheran & Elkington, 2011)**: an audit of 2,241 US firms and 100,000+
  web-generated leads found the average firm took 42 hours to first respond,
  only 37% responded within an hour, and firms that did respond within an
  hour were ~7x more likely to qualify the lead than those who waited even
  one more hour.

Used in: `engagement-local-trust-leads` (stated response-time expectation
check) — the finding is that most sites in this category give the visitor no
signal of how fast they respond at all, at a moment when the underlying
research shows response speed is one of the single largest levers on whether
a captured lead ever converts.

## Accessibility → baseline of what "normal" looks like

- **WebAIM Million (2026 edition)**, an annual automated (WAVE-engine) audit
  of the top 1,000,000 website home pages by page popularity: 95.9% of home
  pages had at least one detectable WCAG 2 A/AA failure, averaging 56.1
  distinct errors per page — a ~10% year-over-year increase, reversing several
  prior years of slow improvement. Home page complexity (element count) rose
  22.5% in a single year, which the report ties directly to the accessibility
  regression. The most common failure categories (low-contrast text, missing
  alt text, unlabeled form inputs) have been the same for seven consecutive
  years of the report.

Used in: `engagement-technical-baseline` (accessibility check) — this
benchmark is what lets a finding say "critical issues found" against an
honest baseline (nearly every site has *some* failures) rather than implying
any detected error is unusual; the check's severity logic focuses on
*critical-impact* violations specifically because that's the class the
WebAIM data shows is both common and disproportionately harmful, not because
zero errors is a realistic bar.

## Local business trust signals → contact/lead conversion

- **BrightLocal, "Local Consumer Review Survey 2026"** (representative panel
  of 1,002 US adult consumers): ~97% of consumers read online reviews before
  choosing a local business; 47% will not consider a business with fewer than
  20 visible reviews; 31% will only use a business rated 4.5 stars or higher
  (nearly double the 17% who said so the prior year); 88% would use a
  business that responds to its reviews, versus 47% for one that responds to
  none.

Used in: `engagement-local-trust-leads` (on-site review/rating visibility
check) — the finding this supports is specifically that reviews need to be
visible *on the site itself*, not just on a third-party platform the visitor
has to leave to go check.

## How this is applied

Each check skill's `suggested_action.summary` should, where a citation from
this file applies, name the source and the number inline (e.g. "Baymard's
meta-analysis of 4,500+ checkouts found forced account creation costs ~26% of
abandoners") rather than a generic claim. This is a deliberate design choice:
a report that cites its evidence reads like an expert audit, not a linter, and
it lets a human reviewer independently verify or challenge any given severity
rather than trusting it blindly. Not every check needs, or gets, a citation —
purely technical/structural checks (console errors, form field counts,
horizontal overflow) are left uncited rather than forcing a study onto a
claim that doesn't need external validation to be self-evidently true.
