# Personalization & Prompt Context Alignment Audit

This marketplace contains an Agent Skill designed for the **Adobe University Hackathon 2026 — Round 3**.
It addresses the failure mode outlined in Appendix E: "Content becomes hyper-localized or narrowly scoped without global contextual anchors, causing an AI assistant to drop the source when user prompts, locations, or contextual framing vary."

## What this Skill Detects
The skill identifies structural vulnerabilities that may cause AI systems (especially RAG-based systems) to drop a website from their source selection due to overly narrow contextual framing.

It operates on 3 specific hypotheses:
1. **Contextual Breadth & Entity Anchors**: Analyzes the core visible text (H1, Meta Description, first paragraph) for an over-reliance on local location markers without generalized fallback anchors.
2. **Schema Localization**: Analyzes JSON-LD (`Organization` or `LocalBusiness`) to detect the presence of an `address` without an accompanying `areaServed` property, which structurally restricts the entity's footprint.
3. **Context-Variance Structural Risk (Chunk Fragmentation)**: Evaluates whether core service terms are exclusively bound to local geographic terms within paragraphs, which creates a high risk of chunk-based RAG fragmentation and context-drop for out-of-region queries.

## How it Works
The skill orchestrates 3 Python scripts (`check_contextual_breadth.py`, `check_schema_localization.py`, and `check_context_variance.py`). Each script fetches the target URL, extracts specific HTML/JSON-LD signals, and deterministically applies its hypothesis criteria without requiring external API calls or user-specific private data.
The entrypoint (`entrypoint.py`) aggregates the results and produces a deterministic JSON report containing finding IDs, severities, evidence, and mechanism-sound recommendations.

## Usage
To execute the skill, run the entrypoint script:
```bash
python skills/personalization-context-audit/entrypoint.py <URL>
```

## Limitations
- Operations are strictly read-only and recommend-only.
- The tool does not perform live RAG testing; it infers structural risks based on observable document properties.
- Dynamic single-page applications (SPAs) relying heavily on client-side rendering may have incomplete results if structured data or text isn't in the initial HTML payload (though basic fallback logic applies).
