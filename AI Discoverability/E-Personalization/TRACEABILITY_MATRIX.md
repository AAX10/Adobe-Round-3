# Traceability Matrix — Mechanism E

Maps each hypothesis to its implementation script, evidence artifact, and validation status.

| Hypothesis ID | Hypothesis Name | Script Function | Evidence File | Test Fixture | Status |
|---|---|---|---|---|---|
| E-001 | Contextual Breadth & Entity Anchors | `scripts/check_contextual_breadth.py` | `evidence/site_inventory.json` → findings where `id="E-001"` | N/A (live sites) | ✅ Validated |
| E-002 | Schema Localization | `scripts/check_schema_localization.py` | `evidence/site_inventory.json` → findings where `id="E-002"` | N/A (live sites) | ✅ Validated |
| E-003 | Context-Variance Structural Risk | `scripts/check_context_variance.py` | `evidence/site_inventory.json` → findings where `id="E-003"` | N/A (live sites) | ⚠️ Inconclusive |

## Script-to-Evidence Chain

```
entrypoint.py
  ├── check_contextual_breadth.py    →  finding.id = "E-001"
  ├── check_schema_localization.py   →  finding.id = "E-002"
  └── check_context_variance.py      →  finding.id = "E-003"

batch_runner.py (External to skill)
  ├── Calls entrypoint.py per URL
  ├── Writes individual results → evidence/site_inventory.json
  ├── Aggregates all results   → evidence/all_results.json
  └── Computes summary stats   → final_result.json
```

## Evidence Artifacts

| File | Purpose | Auto-Generated? |
|---|---|---|
| `evidence/all_results.json` | Full per-site findings from batch run | ✅ Yes, by batch orchestrator |
| `evidence/site_inventory.json` | Individual site audit logs | ✅ Yes, by batch orchestrator |
| `final_result.json` | Aggregate severity counts | ✅ Yes, by batch orchestrator |
| `FINAL_REPORT.md` | Human-readable synthesis | ❌ Manually authored |
