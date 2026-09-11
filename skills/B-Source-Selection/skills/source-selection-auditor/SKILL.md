---
name: source-selection-auditor
description: Evaluates whether an AI retriever can reliably select a page's primary factual content by measuring content density ratio, heading-to-answer locality, and proposition fragmentation.
license: MIT
---

# Source Selection Auditor

## When to use
Use this skill when auditing a webpage to determine whether AI retrievers and RAG chunkers can extract the core factual content without being polluted by layout chrome, heading-answer disconnects, or cross-boundary proposition splits.

## Inputs
- `url` or local `.html` filepath: The target page to audit.

## Procedure
1. Execute `python scripts/evaluate_source_selection.py <url_or_filepath>`
2. The script extracts the DOM, detects the main content region via semantic landmarks.
3. Evaluates three core hypotheses:
   - **H-SS1**: Content Density Ratio (MCDR)
   - **H-SS2**: Heading-to-Answer Semantic Locality (HAL)
   - **H-SS3**: Fragmented Proposition Split
4. Computes composite Score_SS = 0.55 × MCDR + 0.45 × HAL
5. Generates proactive recommendations even on PASS pages.

## Output
A JSON report matching the Adobe Hackathon audit schema with `audited_at`, `site`, `score_ss`, `summary`, and `findings`.
