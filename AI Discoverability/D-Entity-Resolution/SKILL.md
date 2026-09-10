---
name: mechanism-d-entity-graph
description: Audits the JSON-LD structured data layer to ensure an organization has a connected entity graph, strong external identity anchors, and cross-modal consistency for maximum AI discoverability.
license: MIT
---

# Mechanism D: Entity Resolution & Evidence Integrity

## When to use
Use this skill to determine why an LLM or Search Knowledge Graph is failing to attribute products, articles, or factual claims to the parent brand.

## Inputs
- `url`: The target domain to audit.

## Procedure
1. Execute `python scripts/audit_mechanism_d.py <url>`
2. The script extracts the DOM and JSON-LD AST.
3. Evaluates four core hypotheses (H-D1 to H-D4).
4. Outputs a standard JSON array of findings with evidence and prioritized actions.

## Output
A JSON report matching the marketplace schema containing `findings` and `summary`.
