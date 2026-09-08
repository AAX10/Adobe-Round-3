# Extractability — Authoritative References

## Tier 1: Standards & Official Documentation

### REF-C1: W3C WCAG 2.2 — SC 1.3.1: Info and Relationships
- **Organization**: W3C
- **URL**: https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html
- **Mechanism Supported**: extract (C-003)
- **Claim Supported**: Information, structure, and relationships conveyed through presentation must be programmatically determinable. Visual-only associations (layout-based label-value pairing) do not satisfy this criterion.
- **What It Does NOT Establish**: Impact on AI extraction specifically. Designed for human accessibility.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-C2: WHATWG HTML Specification — Tables
- **Organization**: WHATWG
- **URL**: https://html.spec.whatwg.org/multipage/tables.html
- **Mechanism Supported**: extract (C-003)
- **Claim Supported**: `<th>`, `<caption>`, and header association attributes define semantic relationships between table headers and data cells. These are the standard mechanisms for machine-readable label-value associations in tabular data.
- **What It Does NOT Establish**: That absence of these elements always causes extraction failure.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-C3: WHATWG HTML Specification — Grouping content (dl, dt, dd)
- **Organization**: WHATWG
- **URL**: https://html.spec.whatwg.org/multipage/grouping-content.html#the-dl-element
- **Mechanism Supported**: extract (C-003)
- **Claim Supported**: Definition lists (`<dl>/<dt>/<dd>`) provide semantic association between terms and their descriptions/values.
- **What It Does NOT Establish**: That using `<dl>` is the only way to create machine-readable associations.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-C4: Schema.org — Structured Data Documentation
- **Organization**: Schema.org / W3C Community Group
- **URL**: https://schema.org/docs/documents.html
- **Mechanism Supported**: extract (C-002)
- **Claim Supported**: JSON-LD provides explicit semantic relationships for machine consumption, mapping values to standardized properties.
- **What It Does NOT Establish**: That missing JSON-LD causes AI ranking/citation loss.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-C5: Google Search Central — Structured Data
- **Organization**: Google
- **URL**: https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data
- **Mechanism Supported**: extract (C-002)
- **Claim Supported**: Google uses structured data for rich results and understanding page content.
- **What It Does NOT Establish**: That structured data absence prevents all AI understanding.
- **Evidence Type**: SOURCE-DERIVED FACT (Google-specific)

### REF-C6: Google Search Central — JavaScript SEO Basics
- **Organization**: Google
- **URL**: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- **Mechanism Supported**: read (C-001)
- **Claim Supported**: JavaScript-rendered content may be delayed or missed by crawlers. SSR is recommended.
- **What It Does NOT Establish**: All AI crawlers fail on JS content.
- **Evidence Type**: SOURCE-DERIVED FACT (Google-specific)

## Tier 1: Round 3 Handbook

### REF-C7: Round 3 Handbook — Section C
- **Organization**: Adobe University Hackathon
- **Mechanism Supported**: read/extract (C-001, C-002, C-003)
- **Claim Supported**: "the more explicitly and unambiguously a fact is stated in plain, readable text, the more likely a machine is to extract it correctly; the more it's implied, buried, or locked inside something non-textual, the more likely it's missed."
- **What It Does NOT Establish**: Specific checks or thresholds.
- **Evidence Type**: SOURCE-DERIVED FACT

## Tier 2: Experimental Research

### REF-C8: Project Cross-Site Validation (27 sites)
- **Organization**: This project
- **Mechanism Supported**: extract (C-002)
- **Claim Supported**: 19 of 27 tested modern SPAs correctly server-render JSON-LD. Client-rendered JSON-LD is uncommon but real (Adobe, Rivian).
- **What It Does NOT Establish**: Web-wide prevalence statistics.
- **Evidence Type**: EXPERIMENTAL OBSERVATION
