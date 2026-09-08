# Counterexamples (Phase 8)

During our 27-site deep dive (12 original + 15 new candidate SPAs), we encountered several powerful counterexamples that heavily constrain the H-001B hypothesis.

## 1. Client-rendered JSON-LD but NO measurable extraction improvement
**Not Observed.** In our only two positive cases (Adobe, Rivian), injecting the JSON-LD did produce a measurable programmatic extraction improvement (100% precision vs probabilistic NLP). 

## 2. No JSON-LD but excellent machine extraction
**Observed: Stripe, Chase, Figma, Amazon.**
These sites represent the strongest counterevidence against the claim that JSON-LD is *mandatory* for AI discoverability. These organizations completely omit standard JSON-LD (like `FAQPage` or `Product`) from their primary capability/product pages. Yet, because their HTML is incredibly semantic and well-structured, a machine reader (LLM) effortlessly extracts all facts with 100% recall and high precision.

## 3. Server-rendered JSON-LD with good machine extraction
**Observed: 20+ Sites (e.g., Allbirds, Netflix, Zillow, Spotify).**
This is the dominant architectural paradigm on the modern web. Frameworks like Next.js natively server-render JSON-LD. This proves that H-001B is not an unavoidable web constraint, but a specific (and rare) misconfiguration where a site chooses client-side rendering for its metadata.

## 4. Render-only JSON-LD where all information is already explicit in HTML
**Observed: Adobe, Rivian.**
Both of our H-001B positive cases fit this description perfectly. The facts (e.g., FAQ Questions/Answers, Vehicle Specs) are fully present in the raw HTML text. The render-dependency is purely restricted to the *semantic wrappers* (`<script type="application/ld+json">`).

## 5. Render-only JSON-LD containing genuinely unique important information
**Not Observed.** We found no site that hid unique, critical information *exclusively* inside client-rendered JSON-LD while omitting it from the HTML text. (Airbnb hid facts in the client-rendered DOM, but not exclusively in JSON-LD).

## Conclusion
The counterexamples strictly bound our hypothesis. Because major sites (Stripe, Chase) successfully ignore JSON-LD entirely, and because almost all modern SPAs correctly server-render their JSON-LD, H-001B cannot be claimed as a universal SEO disaster. It must be classified as a highly specific, rare Semantic Loss.
