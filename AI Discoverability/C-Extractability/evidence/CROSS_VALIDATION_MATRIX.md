# Cross-Validation Matrix (Phase 9)

## Matrix (27 Sites Total)

| Site | Industry | Page Type | Schema | Raw JSON-LD | Rendered JSON-LD | Reader A Recall | Reader A Precision | Reader B Recall | Reader B Precision | Structural Relationship Restored | Reproducible | Final Classification |
|------|----------|-----------|--------|-------------|------------------|-----------------|--------------------|-----------------|--------------------|----------------------------------|--------------|----------------------|
| **Adobe** | SaaS | Capability | FAQPage | 0 | 3 | 1.0 | Low (NLP) | 1.0 | 1.0 (Struct) | Yes | Yes | **H-001B Positive** |
| **Rivian**| Auto | Product | FAQPage | 0 | 2 | 1.0 | Low (NLP) | 1.0 | 1.0 (Struct) | Yes | Yes | **H-001B Positive** |
| **Airbnb**| Travel | Listing | N/A | 0 | 0 | 0.5 | N/A | 1.0 | N/A | N/A (Factual Loss) | Yes | H-001A (Info Loss) |
| **Zocdoc**| Health | Listing | N/A | 0 | 0 | 0.5 | N/A | 1.0 | N/A | N/A (Factual Loss) | Yes | H-001A (Info Loss) |
| **Stripe**| FinTech| Capability| N/A | 0 | 0 | 1.0 | 1.0 | 1.0 | 1.0 | No | Yes | No JSON-LD |
| **Chase** | FinTech| Product | N/A | 0 | 0 | 1.0 | 1.0 | 1.0 | 1.0 | No | Yes | No JSON-LD |
| **Amazon**| Retail | Product | N/A | 0 | 0 | 1.0 | 1.0 | 1.0 | 1.0 | No | Yes | No JSON-LD |
| **Figma** | SaaS | Product | N/A | 0 | 0 | 1.0 | 1.0 | 1.0 | 1.0 | No | Yes | No JSON-LD |
| *(19 other sites)* | Var | Var | Var | >0 | >0 | 1.0 | 1.0 | 1.0 | 1.0 | No | Yes | Server-Rendered |

## Totals
- **TOTAL SITES**: 27
- **TOTAL H-001B POSITIVE CASES**: 2 (Adobe, Rivian)
- **TOTAL H-001A CASES**: 2 (Airbnb, Zocdoc)
- **TOTAL SERVER-RENDERED CASES**: 19
- **TOTAL NO-JSON-LD CASES**: 4
- **TOTAL H-001B CASES WITH STRUCTURAL RELATIONSHIP RESTORED**: 2
- **TOTAL COUNTEREXAMPLES**: 4 (Sites with no JSON-LD but perfect extraction)
