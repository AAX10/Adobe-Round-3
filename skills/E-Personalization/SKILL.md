---
name: "Personalization Context Audit"
description: "Audits websites for hyper-localization and persona context fragmentation that causes AI systems to drop sources."
license: "MIT"
---

# Personalization & Prompt Context Audit

## When to use
Use this skill to determine if an organization's website is structurally at risk of being ignored by AI Retrieval-Augmented Generation (RAG) systems due to overly localized or narrowly scoped content framing, without adequate fallback context.

## Inputs
- `url`: The target website URL to audit.

## Procedure
1. **Contextual Breadth Analysis**: Fetches the page and extracts primary defining elements (`<title>`, `<meta name="description">`, `<h1>`, first `<p>`). Analyzes term distribution for hyper-local versus broad generic markers.
2. **Schema Localization Check**: Extracts JSON-LD (`Organization`, `LocalBusiness`). Identifies presence of physical constraints (`address`) missing multi-region expansions (`areaServed`).
3. **Context-Variance Structural Risk**: Parses visible text paragraphs. Analyzes semantic linkages to see if core service identifiers are exclusively chunked with local modifiers.
4. **Report Aggregation**: Orchestrates these 3 deterministic scripts, scoring severity based on observed impact breadth, and generating actionable remediations.

## Output
A JSON report conforming to the required schema:
- `site`: The target hostname.
- `audited_at`: ISO-8601 timestamp.
- `summary`: Total findings and counts by severity.
- `findings`: Array of identified risks, each with `id`, `title`, `severity`, `evidence`, and `suggested_action`.
