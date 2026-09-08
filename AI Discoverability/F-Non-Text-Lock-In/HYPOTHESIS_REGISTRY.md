# Hypothesis Registry

## Summary

| ID | Short Name | Mechanism | Quality Score | Classification |
|----|-----------|-----------|---------------|----------------|
| A-001 | Crawl-Blocked Important Content | crawl | 4.9 | **CORE** |
| A-002 | Non-Crawlable Navigation | crawl | 4.2 | **CORE** |
| A-003 | Important URL Retrieval Failure | crawl | 4.8 | **CORE** |
| C-001 | Render-Dependent Factual Content | read | 4.4 | **CORE** |
| C-002 | Render-Dependent Structural Metadata | extract | 4.6 | **CANDIDATE** |
| C-003 | Ambiguous Fact-to-Label Association | extract | 3.7 | **CANDIDATE** |
| F-001 | Image-Only Core Facts | lock-in | 4.6 | **CORE** |
| F-002 | Document-Only Critical Information | lock-in | 4.2 | **CANDIDATE** |
| F-003 | Non-Text Interactive/Visual Fact Lock-In | lock-in | 3.8 | **CANDIDATE** |

## Quality Score Breakdown

### A-001 — Crawl-Blocked Important Content (4.9)

| Criterion | Score |
|-----------|-------|
| Mechanistic plausibility | 5 |
| Evidence quality | 5 |
| Observability | 5 |
| Automation feasibility | 5 |
| Cross-site generalization | 5 |
| False-positive resistance | 4 |
| Actionability | 5 |
| Unseen-site applicability | 5 |
| Runtime feasibility | 5 |

### A-002 — Non-Crawlable Navigation (4.2)

| Criterion | Score |
|-----------|-------|
| Mechanistic plausibility | 5 |
| Evidence quality | 4 |
| Observability | 4 |
| Automation feasibility | 4 |
| Cross-site generalization | 5 |
| False-positive resistance | 3 |
| Actionability | 5 |
| Unseen-site applicability | 5 |
| Runtime feasibility | 3 |

### A-003 — Important URL Retrieval Failure (4.8)

| Criterion | Score |
|-----------|-------|
| Mechanistic plausibility | 5 |
| Evidence quality | 5 |
| Observability | 5 |
| Automation feasibility | 5 |
| Cross-site generalization | 5 |
| False-positive resistance | 4 |
| Actionability | 5 |
| Unseen-site applicability | 5 |
| Runtime feasibility | 4 |

### C-001 — Render-Dependent Factual Content (4.4)

| Criterion | Score |
|-----------|-------|
| Mechanistic plausibility | 5 |
| Evidence quality | 4 |
| Observability | 5 |
| Automation feasibility | 4 |
| Cross-site generalization | 4 |
| False-positive resistance | 4 |
| Actionability | 5 |
| Unseen-site applicability | 5 |
| Runtime feasibility | 4 |

### C-002 — Render-Dependent Structural Metadata (4.6)

| Criterion | Score |
|-----------|-------|
| Mechanistic plausibility | 5 |
| Evidence quality | 5 |
| Observability | 5 |
| Automation feasibility | 5 |
| Cross-site generalization | 3 |
| False-positive resistance | 4 |
| Actionability | 5 |
| Unseen-site applicability | 5 |
| Runtime feasibility | 4 |

### C-003 — Ambiguous Fact-to-Label Association (3.7)

| Criterion | Score |
|-----------|-------|
| Mechanistic plausibility | 4 |
| Evidence quality | 3 |
| Observability | 3 |
| Automation feasibility | 3 |
| Cross-site generalization | 4 |
| False-positive resistance | 3 |
| Actionability | 5 |
| Unseen-site applicability | 4 |
| Runtime feasibility | 4 |

### F-001 — Image-Only Core Facts (4.6)

| Criterion | Score |
|-----------|-------|
| Mechanistic plausibility | 5 |
| Evidence quality | 4 |
| Observability | 4 |
| Automation feasibility | 4 |
| Cross-site generalization | 5 |
| False-positive resistance | 4 |
| Actionability | 5 |
| Unseen-site applicability | 5 |
| Runtime feasibility | 5 |

### F-002 — Document-Only Critical Information (4.2)

| Criterion | Score |
|-----------|-------|
| Mechanistic plausibility | 5 |
| Evidence quality | 3 |
| Observability | 4 |
| Automation feasibility | 4 |
| Cross-site generalization | 4 |
| False-positive resistance | 3 |
| Actionability | 5 |
| Unseen-site applicability | 5 |
| Runtime feasibility | 5 |

### F-003 — Non-Text Interactive/Visual Fact Lock-In (3.8)

| Criterion | Score |
|-----------|-------|
| Mechanistic plausibility | 5 |
| Evidence quality | 3 |
| Observability | 3 |
| Automation feasibility | 3 |
| Cross-site generalization | 3 |
| False-positive resistance | 3 |
| Actionability | 5 |
| Unseen-site applicability | 4 |
| Runtime feasibility | 5 |

## Classification Rules

- **CORE** (Score ≥ 4.2): Ready for implementation as a primary audit check
- **CANDIDATE** (Score 3.5–4.1): Technically sound, implement with additional false-positive safeguards
- **RESEARCH-ONLY** (Score < 3.5): Needs more evidence before implementation
- **REJECT**: Failed quality bar — not included in registry

## Rejected Hypotheses

None. All 9 hypotheses passed the quality bar (minimum score 3.5).
