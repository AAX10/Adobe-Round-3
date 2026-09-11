---
name: F-Non-Text-Lock-In
description: Audit a public webpage for non-text lock-in — important facts trapped in images, PDFs, or video/canvas without readable text equivalents. Tests image-only facts (F-001), document-only facts (F-002), and video/canvas lock-in (F-003). Use when checking if key information is invisible to text-oriented AI readers.
license: MIT
metadata:
  author: adobe-hackathon-research
  version: "1.0"
  mechanism: lock-in
  hypotheses: F-001, F-002, F-003
---

# Non-Text Lock-In Audit

## When to use

Use when you need to check whether important facts are **locked in non-text formats** without readable equivalents. This skill tests three media types:

- **Images** (F-001): Facts in images without descriptive alt text or text alternatives
- **Documents** (F-002): Critical specs/pricing only in PDFs, not in page HTML
- **Visual Media** (F-003): Facts in video/canvas/interactive elements without captions or fallback

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `--url` | Yes* | URL of the page to audit |
| `--html` | Yes* | Path to a local HTML file to audit |
| `--output` | No | Output JSON file path |

*Provide either `--url` or `--html`. No rendering required — all checks work on initial HTML.

## Procedure

1. **F-001 — Image fact audit**:
   - Find all `<img>` elements on the page
   - Classify alt text quality (missing, empty/decorative, generic, descriptive)
   - Skip intentionally decorative images (`alt=""`) and small icons
   - Check if image is in a factual content area (product, pricing, spec section)
   - Check for nearby text equivalents (figcaption, adjacent text, JSON-LD coverage)
   - Flag images in factual areas with poor alt text and no text equivalent

2. **F-002 — Document fact audit**:
   - Find links to downloadable documents (PDF, DOCX, XLSX by extension or link text)
   - Classify document importance by context (link text, heading, page type)
   - Filter out supplementary documents (terms of service, whitepapers, user manuals)
   - Check if page HTML contains equivalent factual information
   - Flag factual documents whose content is not available in page HTML

3. **F-003 — Visual media audit**:
   - Detect `<video>`, `<canvas>`, `<object>`, `<embed>`, and large SVG elements
   - For video: check for `<track>` captions/subtitles and nearby transcripts
   - For canvas: check fallback content and ARIA attributes
   - For SVGs: check for extractable `<text>` elements vs path-only content
   - Flag non-text elements in factual areas without text equivalents

## Output

Each check produces JSON with: `check_id`, `status`, `severity`, `evidence`, `reason`, `suggested_action`.

## References

- `references/non-text-sources.md` — Authoritative sources (WCAG 1.1.1, 1.2.x, HTML spec)
- `references/severity-model.md` — Severity framework
