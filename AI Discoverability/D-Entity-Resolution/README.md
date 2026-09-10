# D — Entity Resolution / JSON-LD Identity Auditor

## Overview

Mechanism D audits whether a website's JSON-LD structured data provides a complete, internally consistent entity identity graph that AI knowledge systems can resolve. It checks four critical failure modes in the **resolve** stage of the AI discovery pipeline.

## Why This Matters

When an AI assistant says "Adobe offers Creative Cloud for $59.99/month," it must:
1. **Resolve** "Adobe" to a specific entity (not Adobe Systems vs. Adobe the material)
2. **Verify** the entity identity via cross-references (Wikidata, Wikipedia)
3. **Confirm** the name on the page matches the name in the schema
4. **Validate** that the pricing claim has a structured citation

If the JSON-LD entity graph is disconnected, AI systems hallucinate entity attributes (wrong founding year, wrong CEO, wrong headquarters).

## Hypotheses

| ID | Name | Failure Mode | Severity |
|---|---|---|---|
| [D-001](hypotheses/D-001.md) | Entity Graph Connectivity Deficit | Organization node missing or lacks canonical `@id` | 🔴 Critical |
| [D-002](hypotheses/D-002.md) | External Identity Anchor Deficit | No `sameAs` links to Wikidata/Wikipedia | 🟠 High |
| [D-003](hypotheses/D-003.md) | Cross-Modal Consistency Deficit | Organization.name doesn't match page `<title>` | 🟡 Medium |
| [D-004](hypotheses/D-004.md) | Uncorroborated Factual Claim Deficit | Quantitative claims have no RDF citations | 🟡 Medium |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/audit_mechanism_d.py` | Core evaluator — runs all 4 hypothesis checks on a single URL |
| `scripts/batch_runner.py` | Orchestrator — runs audit across multiple URLs, aggregates results |

## Usage

```bash
# Single site audit
python scripts/audit_mechanism_d.py https://www.adobe.com

# Batch audit (5 enterprise sites)
python scripts/batch_runner.py
```

## Evidence

| File | Description |
|---|---|
| `evidence/all_results.json` | Full per-site findings from batch run |
| `evidence/site_inventory.json` | Individual site audit logs |
| `final_result.json` | Aggregate severity counts across all tested sites |
| `FINAL_REPORT.md` | Human-readable synthesis of findings |

## Technical Details

- **Parser:** Playwright (SPA support) + BeautifulSoup4
- **String Matching:** Jellyfish (Jaro-Winkler similarity with substring pre-check)
- **Anti-bot Handling:** HTTP 403/429/999 → "Unverifiable" (not penalized)
- **Type Checking:** Set-based `@type` matching (supports arrays and subclasses)
- **Wait Strategy:** `domcontentloaded` (prevents tracking pixel hangs)
- **Execution Time:** < 5 seconds per site