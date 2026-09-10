# Ablation Results — Mechanism D

## Purpose
Ablation testing systematically disables individual hypothesis checks to measure their independent contribution to the overall audit score.

## Methodology
Each row below shows the impact of removing one hypothesis from the evaluation pipeline while keeping all others active.

## Results (Tested on IBM.com)

| Removed Check | Remaining Findings | Severity Change | Conclusion |
|---|---|---|---|
| **Remove H-D1** (Graph Connectivity) | 1 finding (H-D4 only) | HIGH → MEDIUM | H-D1 is the primary driver. Without it, the audit misses the most critical defect. |
| **Remove H-D2** (External Identity) | 2 findings (H-D1 + H-D4) | No change | H-D2 did not trigger on IBM; removal has no impact on this sample. |
| **Remove H-D3** (Cross-Modal) | 2 findings (H-D1 + H-D4) | No change | H-D3 is dependent on H-D1 (requires Organization node). Cascading dependency. |
| **Remove H-D4** (Factual Claims) | 1 finding (H-D1 only) | Drops 1 MEDIUM finding | H-D4 provides supplementary evidence but is not the primary risk signal. |

## Key Insight
**H-D1 is the gateway hypothesis.** If a site lacks an `Organization` node, H-D2 (sameAs links) and H-D3 (name matching) cannot execute. This creates a cascading dependency chain:

```
H-D1 (Organization exists?)
  ├── YES → H-D2 (sameAs links valid?)
  │          H-D3 (name matches DOM?)
  │          H-D4 (claims have citations?)
  └── NO  → H-D2 SKIPPED
             H-D3 SKIPPED
             H-D4 still runs (DOM-only check)
```