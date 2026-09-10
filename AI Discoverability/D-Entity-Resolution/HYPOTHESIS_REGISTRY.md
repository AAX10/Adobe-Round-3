# Hypothesis Registry — Mechanism D (Entity Resolution)

## Overview

This registry catalogs all hypotheses under Mechanism D, which audits the **resolve** stage of the AI content consumption pipeline. Each hypothesis identifies a specific failure mode in JSON-LD entity identity graphs.

## Hypothesis Summary

| ID | Name | Pipeline Stage | Severity | Status |
|---|---|---|---|---|
| D-001 | Entity Graph Connectivity Deficit | Resolve | 🔴 Critical | ✅ Validated |
| D-002 | External Identity Anchor Deficit | Resolve | 🟠 High | ⚠️ Inconclusive |
| D-003 | Cross-Modal Consistency Deficit | Resolve | 🟡 Medium | ⚠️ Inconclusive |
| D-004 | Uncorroborated Factual Claim Deficit | Resolve | 🟡 Medium | ✅ Validated |

## Detailed Registry

### D-001: Entity Graph Connectivity Deficit

| Property | Value |
|---|---|
| **ID** | D-001 |
| **Classification** | CORE |
| **Severity** | 🔴 Critical |
| **Pipeline Stage** | Resolve → Entity Identity |
| **Script Function** | `evaluate_h1_graph_connectivity()` |
| **Trigger Condition** | No `Organization` node in JSON-LD OR node lacks canonical `@id` |
| **Failure Mode** | AI knowledge graphs cannot resolve the page's entity identity |
| **Evidence** | `evidence/all_results.json` → findings where `id="H-D1"` |
| **Validation** | ✅ Validated on Microsoft.com and IBM.com — both lack Organization `@id` |
| **Remediation** | Add `Organization` with absolute URL `@id`, `name`, `url` properties |

---

### D-002: External Identity Anchor Deficit

| Property | Value |
|---|---|
| **ID** | D-002 |
| **Classification** | CORE |
| **Severity** | 🟠 High |
| **Pipeline Stage** | Resolve → Cross-Reference |
| **Script Function** | `evaluate_h2_external_identity()` |
| **Trigger Condition** | Organization `sameAs` array missing Wikidata or Wikipedia links |
| **Failure Mode** | AI cannot cross-reference entity with authoritative external KGs |
| **Evidence** | `evidence/all_results.json` → findings where `id="H-D2"` |
| **Validation** | ⚠️ Inconclusive — dependent on H-D1 (Organization must exist first) |
| **Remediation** | Add `sameAs` array with Wikidata QID and Wikipedia URL |

---

### D-003: Cross-Modal Consistency Deficit

| Property | Value |
|---|---|
| **ID** | D-003 |
| **Classification** | CANDIDATE |
| **Severity** | 🟡 Medium |
| **Pipeline Stage** | Resolve → Name Matching |
| **Script Function** | `evaluate_h3_cross_modal()` |
| **Trigger Condition** | Jaro-Winkler similarity between `Organization.name` and page `<title>` < 0.75 |
| **Failure Mode** | AI sees conflicting names between structured data and visible page content |
| **Evidence** | `evidence/all_results.json` → findings where `id="H-D3"` |
| **Validation** | ⚠️ Inconclusive — cascading dependency on H-D1 |
| **Remediation** | Ensure `Organization.name` matches the page's visible brand name |

---

### D-004: Uncorroborated Factual Claim Deficit

| Property | Value |
|---|---|
| **ID** | D-004 |
| **Classification** | CANDIDATE |
| **Severity** | 🟡 Medium |
| **Pipeline Stage** | Resolve → Claim Verification |
| **Script Function** | `evaluate_h4_claim_verification()` |
| **Trigger Condition** | Quantitative claims in DOM text with zero RDF `citation` properties |
| **Failure Mode** | AI systems present stats without sourcing, increasing hallucination risk |
| **Evidence** | `evidence/all_results.json` → findings where `id="H-D4"` |
| **Validation** | ✅ Validated on IBM.com — 1 uncorroborated quantitative claim |
| **Remediation** | Embed `citation` or `isBasedOn` properties adjacent to quantitative assertions |

## Dependency Graph

```
D-001 (Organization exists?)
  ├── YES → D-002 (sameAs links valid?)
  │          D-003 (name matches DOM?)
  │          D-004 (claims have citations?)
  └── NO  → D-002 SKIPPED
             D-003 SKIPPED
             D-004 still runs (DOM-only check)
```

## Quality Metrics

| Hypothesis | Quality Score (1-5) | False Positive Rate | Empirical Hit Rate |
|---|---|---|---|
| D-001 | 4.8 | 0% | 100% of auditable sites |
| D-002 | 4.2 | 0% | N/A (dependent on D-001) |
| D-003 | 3.9 | < 5% (substring pre-check mitigates) | N/A (dependent on D-001) |
| D-004 | 3.7 | ~10% (regex-based claim detection) | 50% of auditable sites |
