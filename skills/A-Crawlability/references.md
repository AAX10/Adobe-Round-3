# Crawlability — Authoritative References

## Tier 1: Standards & Official Documentation

### REF-A1: RFC 9309 — Robots Exclusion Protocol
- **Organization**: IETF
- **URL**: https://www.rfc-editor.org/rfc/rfc9309
- **Publication Date**: September 2022
- **Mechanism Supported**: crawl (A-001)
- **Claim Supported**: Defines the Robots Exclusion Protocol as an Internet Standard. Compliant crawlers MUST NOT access URIs matched by Disallow rules for their user-agent group. Specifies parsing rules, caching, error handling, and Allow/Disallow precedence.
- **What It Does NOT Establish**: Impact on AI assistant citations, rankings, or discoverability beyond the crawl gate. Does not address JavaScript rendering or content quality.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-A2: RFC 9110 — HTTP Semantics
- **Organization**: IETF
- **URL**: https://www.rfc-editor.org/rfc/rfc9110
- **Publication Date**: June 2022
- **Mechanism Supported**: crawl (A-003)
- **Claim Supported**: Defines HTTP status code semantics. 4xx codes indicate client errors (resource not found, forbidden). 5xx codes indicate server errors. These are hard retrieval failures — no usable content is returned.
- **What It Does NOT Establish**: Impact on AI systems specifically. Does not prescribe retry policies or severity thresholds.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-A3: Google Search Central — Links Best Practices
- **Organization**: Google
- **URL**: https://developers.google.com/search/docs/crawling-indexing/links-crawlable
- **Mechanism Supported**: crawl (A-002)
- **Claim Supported**: Google discovers pages primarily through `<a>` HTML elements with `href` attributes. URLs in `onclick` handlers or non-standard elements without `href` may not be reliably discovered.
- **What It Does NOT Establish**: Behavior of non-Google crawlers or AI assistant retrieval systems.
- **Evidence Type**: SOURCE-DERIVED FACT (Google-specific)

### REF-A4: Google Search Central — robots.txt Introduction
- **Organization**: Google
- **URL**: https://developers.google.com/search/docs/crawling-indexing/robots/intro
- **Mechanism Supported**: crawl (A-001)
- **Claim Supported**: Googlebot honors robots.txt Disallow rules and will not crawl blocked URLs.
- **What It Does NOT Establish**: Whether AI assistants use the same crawl pipeline as Googlebot.
- **Evidence Type**: SOURCE-DERIVED FACT (Google-specific)

### REF-A5: Google Search Central — JavaScript SEO Basics
- **Organization**: Google
- **URL**: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- **Mechanism Supported**: crawl (A-002)
- **Claim Supported**: JavaScript-generated content goes through a separate rendering queue. Google recommends SSR for important content. Links should be crawlable without JS where possible.
- **What It Does NOT Establish**: Non-Google crawler behavior. Does not claim JS content is always missed.
- **Evidence Type**: SOURCE-DERIVED FACT (Google-specific)

### REF-A6: Google Search Central — Sitemaps Overview
- **Organization**: Google
- **URL**: https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview
- **Mechanism Supported**: crawl (A-002)
- **Claim Supported**: Sitemaps help search engines discover URLs that might not be found through crawling alone. Sitemap inclusion does not guarantee indexing.
- **What It Does NOT Establish**: That sitemap omission means a page is undiscoverable.
- **Evidence Type**: SOURCE-DERIVED FACT (Google-specific)

### REF-A7: Google Search Central — HTTP/Network Errors
- **Organization**: Google
- **URL**: https://developers.google.com/search/docs/crawling-indexing/http-network-errors
- **Mechanism Supported**: crawl (A-003)
- **Claim Supported**: Persistent errors cause Googlebot to reduce crawl frequency and eventually drop URLs.
- **What It Does NOT Establish**: Specific thresholds. AI assistant behavior.
- **Evidence Type**: SOURCE-DERIVED FACT (Google-specific)

## Tier 1: Round 3 Handbook

### REF-A8: Round 3 Handbook — Section A
- **Organization**: Adobe University Hackathon
- **Mechanism Supported**: crawl (A-001, A-002, A-003)
- **Claim Supported**: "the crawler has to be let in, it has to be able to read what's there, and it has to be able to pick out the specific fact" — crawl access is the first prerequisite gate.
- **What It Does NOT Establish**: Specific checks, thresholds, or remediation.
- **Evidence Type**: SOURCE-DERIVED FACT

## Source Limitations

All Google Search Central references are authoritative for Googlebot behavior but should NOT be automatically extrapolated to all AI assistant crawlers. The distinction between "Google Search behavior" and "all AI systems" is maintained throughout our hypotheses.
