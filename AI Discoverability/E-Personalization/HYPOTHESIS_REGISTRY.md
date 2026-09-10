# Hypothesis Registry

## Summary

| ID | Short Name | Mechanism | Quality Score | Classification |
|----|-----------|-----------|---------------|----------------|
| E-001 | Contextual Breadth & Entity Anchors | context | 4.5 | **CORE** |
| E-002 | Schema Localization | context | 5.0 | **CORE** |
| E-003 | Context-Variance Structural Risk | context | 4.3 | **CORE** |

## Quality Score Breakdown

### E-001 — Contextual Breadth & Entity Anchors (4.5)

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

### E-002 — Schema Localization (5.0)

| Criterion | Score |
|-----------|-------|
| Mechanistic plausibility | 5 |
| Evidence quality | 5 |
| Observability | 5 |
| Automation feasibility | 5 |
| Cross-site generalization | 5 |
| False-positive resistance | 5 |
| Actionability | 5 |
| Unseen-site applicability | 5 |
| Runtime feasibility | 5 |

### E-003 — Context-Variance Structural Risk (4.3)

| Criterion | Score |
|-----------|-------|
| Mechanistic plausibility | 4 |
| Evidence quality | 4 |
| Observability | 4 |
| Automation feasibility | 4 |
| Cross-site generalization | 4 |
| False-positive resistance | 4 |
| Actionability | 5 |
| Unseen-site applicability | 5 |
| Runtime feasibility | 5 |

## Classification Rules

- **CORE** (Score ≥ 4.2): Ready for implementation as a primary audit check
- **CANDIDATE** (Score 3.5–4.1): Technically sound, implement with additional false-positive safeguards
- **RESEARCH-ONLY** (Score < 3.5): Needs more evidence before implementation
- **REJECT**: Failed quality bar — not included in registry

## Rejected Hypotheses

None. All 3 hypotheses passed the quality bar.
