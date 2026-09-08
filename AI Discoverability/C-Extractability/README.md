# C — Extractability / Machine-Readability Hypotheses

## Overview

These three hypotheses cover distinct failure modes in the **read** and **extract** mechanisms — the stages where a crawler attempts to interpret page content after successfully retrieving it.

## Why These Are Distinct

| Hypothesis | Failure Mode | Mechanism | What's Lost |
|-----------|-------------|-----------|-------------|
| **C-001** | Facts absent from initial HTML | read | The facts themselves |
| **C-002** | Structural metadata absent from initial HTML | extract | Explicit semantic relationships |
| **C-003** | Facts present but semantically unassociated | extract | Value-to-attribute mapping |

These represent three layers of the extraction challenge:

1. **C-001 (Information Loss)**: The content is literally not there for a non-JS reader. This is the most severe — absolute factual absence.
2. **C-002 (Semantic Loss)**: The facts are in the HTML, but the explicit machine-readable structure (JSON-LD) that associates them is missing without JS. An NLP-capable reader can still extract the facts but with lower structural precision.
3. **C-003 (Association Loss)**: The facts are in the HTML, but their semantic relationships to labels/attributes are unclear from the DOM structure alone. The reader can see the values but may not know what they represent.

## Relationship to Existing Research

- C-001 and C-002 are reformatted versions of the existing H-001A and H-001B hypotheses
- All existing evidence, case studies, ablation results, and counterexamples are preserved
- C-003 is a new hypothesis addressing a different extraction failure mode

## Strength Assessment

| Hypothesis | Quality Score | Classification | Strength |
|-----------|--------------|----------------|----------|
| **C-001** | 4.4 | CORE | Strong — demonstrable information loss |
| **C-002** | 4.6 | CANDIDATE | Technically strong but rare (2/27 sites) |
| **C-003** | 3.7 | CANDIDATE | Well-reasoned but heuristic-heavy |

## Evidence Required

### C-001
- Dual-fetch comparison (raw vs rendered)
- Text presence/absence verification
- Importance classification

### C-002
- JSON-LD schema comparison (raw vs rendered)
- Relevance filtering
- Ablation testing

### C-003
- DOM structure analysis
- Value-label association detection
- Orphaned value identification
