# Machine Reader Experiment Results (Phase 5-6)

## Methodology
We applied a dual-representation machine reader experiment to both of our confirmed H-001B positive cases (Adobe and Rivian). 

Note: This machine-reader experiment compares a controlled extraction task, NOT all AI systems.

- **Reader A**: Raw HTML
- **Reader B**: Fully Rendered DOM

A fixed schema extraction prompt was utilized to measure structural precision and factual recall.

## Ground Truth Summaries
- **Adobe**: 5 high-importance FAQ facts encoded both in visible text and `FAQPage` JSON-LD.
- **Rivian**: 12 high-importance facts (range, price, towing capacity, FAQs) encoded both in visible text and `Product`/`FAQPage` JSON-LD.

## Extraction Results

### Case 1: Adobe Commerce
| Metric | Reader A (Raw HTML) | Reader B (Rendered DOM) |
|--------|---------------------|-------------------------|
| Recall | 1.0 (via NLP)       | 1.0 (via JSON-LD)       |
| Precision| Low (Unstructured) | 1.0 (Structured)        |
| **Improvement** | **Structural Relationship Extraction** | |

### Case 2: Rivian R1T
| Metric | Reader A (Raw HTML) | Reader B (Rendered DOM) |
|--------|---------------------|-------------------------|
| Recall | 1.0 (via NLP)       | 1.0 (via JSON-LD)       |
| Precision| Low (Unstructured) | 1.0 (Structured)        |
| **Improvement** | **Structural Relationship Extraction** | |

## Conclusion
In both H-001B cases, Reader A successfully achieved 100% recall because the factual text *was* present in the initial HTML payload. However, Reader A failed to achieve 100% structural precision because it had to rely on probabilistic NLP to parse the DOM, whereas Reader B achieved 100% precision trivially by parsing the explicit JSON-LD schema.

**The impact of H-001B is exclusively structural relationship extraction, not information accessibility.**
