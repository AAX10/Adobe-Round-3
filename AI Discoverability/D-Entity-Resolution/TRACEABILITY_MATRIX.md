# Traceability Matrix — Mechanism D

Maps each hypothesis to its implementation script, evidence artifact, and validation status.

| Hypothesis ID | Hypothesis Name | Script Function | Evidence File | Test Fixture | Status |
|---|---|---|---|---|---|
| H-D1 | Entity Graph Connectivity Deficit | `evaluate_h1_graph_connectivity()` | `evidence/all_results.json` → findings where `id="H-D1"` | N/A (live sites) | ✅ Validated |
| H-D2 | External Identity Anchor Deficit | `evaluate_h2_external_identity()` | `evidence/all_results.json` → findings where `id="H-D2"` | N/A (live sites) | ⚠️ Inconclusive |
| H-D3 | Cross-Modal Consistency Deficit | `evaluate_h3_cross_modal()` | `evidence/all_results.json` → findings where `id="H-D3"` | N/A (live sites) | ⚠️ Inconclusive |
| H-D4 | Uncorroborated Factual Claim Deficit | `evaluate_h4_claim_verification()` | `evidence/all_results.json` → findings where `id="H-D4"` | N/A (live sites) | ✅ Validated |

## Script-to-Evidence Chain

```
audit_mechanism_d.py
  ├── evaluate_h1_graph_connectivity()  →  finding.id = "H-D1"
  ├── evaluate_h2_external_identity()   →  finding.id = "H-D2"
  ├── evaluate_h3_cross_modal()         →  finding.id = "H-D3"
  └── evaluate_h4_claim_verification()  →  finding.id = "H-D4"

batch_runner.py
  ├── Calls audit_mechanism_d.py per URL
  ├── Writes individual results → evidence/site_inventory.json
  ├── Aggregates all results   → evidence/all_results.json
  └── Computes summary stats   → final_result.json
```

## Evidence Artifacts

| File | Purpose | Auto-Generated? |
|---|---|---|
| `evidence/all_results.json` | Full per-site findings from batch run | ✅ Yes, by `batch_runner.py` |
| `evidence/site_inventory.json` | Individual site audit logs | ✅ Yes, by `batch_runner.py` |
| `final_result.json` | Aggregate severity counts | ✅ Yes, by `batch_runner.py` |
| `FINAL_REPORT.md` | Human-readable synthesis | ❌ Manually authored |