# References — Mechanism D (Entity Resolution)

## Standards & Specifications

- **Schema.org Organization**: https://schema.org/Organization — Defines required properties (`@id`, `name`, `url`, `sameAs`) for organizational entities.
- **JSON-LD 1.1 Specification**: https://www.w3.org/TR/json-ld11/ — W3C Recommendation for linked data in JSON format. Section 3.3 covers `@id` as the canonical node identifier.
- **Wikidata Entity Resolution**: https://www.wikidata.org/wiki/Wikidata:Identifiers — Best practices for cross-linking entities using `sameAs` properties.
- **Google Structured Data Guidelines**: https://developers.google.com/search/docs/advanced/structured-data/intro-structured-data — Google's requirements for JSON-LD markup.

## Academic Research

- **Knowledge Graph Entity Linking**: Shen, W., Wang, J., & Han, J. (2015). "Entity Linking with a Knowledge Base: Issues, Techniques, and Solutions." *IEEE TKDE*. — Foundational work on why canonical identifiers are critical for entity disambiguation.
- **Jaro-Winkler String Similarity**: Winkler, W. E. (1999). "The State of Record Linkage and Current Research Problems." — The string similarity metric used in H-D3 for cross-modal name matching.

## Tools Used

| Tool | Version | Purpose |
|---|---|---|
| Playwright | 1.40+ | Headless browser for SPA rendering |
| BeautifulSoup4 | 4.12+ | HTML DOM parsing |
| Jellyfish | 1.0+ | Jaro-Winkler string distance calculations |
| lxml | 4.9+ | Fast XML/HTML parser backend |

## Severity Model Source

Severity tiers (Critical/High/Medium/Low) are calibrated against:
1. Google's Rich Results error classification
2. Schema.org's required vs recommended property taxonomy
3. Empirical testing across 10+ enterprise domains (see `FINAL_REPORT.md`)