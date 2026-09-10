---
name: C-Extractability
description: Audit a public webpage's machine-readability — whether important facts can be correctly extracted by AI and machine readers. Tests render-dependent content (C-001), render-dependent structured data (C-002), and ambiguous fact-label associations (C-003). Use when checking if page content is correctly parseable.
license: MIT
metadata:
  author: adobe-hackathon-research
  version: "1.0"
  mechanism: read/extract
  hypotheses: C-001, C-002, C-003
---

# Extractability Audit

## When to use

Use when you need to check whether a page's important facts are **correctly extractable** by machine readers. This skill tests three extraction failure modes:

- **Information Loss** (C-001): Are facts absent from initial HTML, requiring JS to appear?
- **Semantic Loss** (C-002): Is structured data (JSON-LD) only available after JS rendering?
- **Association Loss** (C-003): Are factual values unassociated with semantic labels?

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `--url` | Yes* | URL of the page to audit |
| `--html` | Yes* | Path to a local HTML file to audit |
| `--raw` | For C-001/C-002 | Path to raw HTML file (before JS) |
| `--rendered` | For C-001/C-002 | Path to rendered HTML file (after JS) |
| `--output` | No | Output JSON file path |

*Provide either `--url` or `--html`.

## Procedure

1. **C-003 — Semantic association audit** (no rendering required):
   - Scan page text for factual values (prices, measurements, dates, dimensions)
   - For each value, check DOM for semantic label association (`<th>`, `<dt>`, `<label>`, ARIA)
   - Check if JSON-LD provides explicit attribute-value mapping
   - Flag values with no semantic association and no JSON-LD coverage

2. **C-001 — Render-dependent factual content** (requires Playwright headless browser):
   - Automatically fetch raw HTML via direct request
   - Automatically render the URL headlessly via Playwright
   - Extract structural text blocks (headings, paragraphs) from the rendered DOM
   - Verify if those exact text blocks exist anywhere in the raw HTML payload
   - Flag facts that are only visible to a JS execution engine

3. **C-002 — Structured data comparison** (requires raw + rendered HTML):
   - Extract JSON-LD blocks from raw and rendered HTML
   - Filter for relevant schema types (Product, FAQPage, etc.)
   - Identify render-only schemas
   - Check if schema field values exist in raw HTML text (semantic vs information loss)

## Output

Each check produces JSON with: `check_id`, `status`, `severity`, `evidence`, `reason`, `suggested_action`.

## References

- `references/extractability-sources.md` — Authoritative sources (WCAG, Schema.org, Google)
- `references/severity-model.md` — Severity framework
