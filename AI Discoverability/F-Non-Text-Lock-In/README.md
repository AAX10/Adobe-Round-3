# F — Non-Text Lock-In Hypotheses

## Overview

These three hypotheses cover distinct failure modes in the **lock-in** mechanism — where important factual information is communicated through non-text formats without equivalent readable text.

## Why These Are Distinct

| Hypothesis | Non-Text Format | Detection Method | Evidence Differs Because |
|-----------|----------------|------------------|------------------------|
| **F-001** | Images | Alt text, nearby text, JSON-LD | Images are ubiquitous; alt text is a well-defined signal |
| **F-002** | Downloadable documents (PDF) | Document link detection, page text comparison | Documents are linked, not embedded; content is external to page |
| **F-003** | Canvas/video/interactive media | Track elements, fallback content, ARIA | Each media type has different accessibility mechanisms |

## Common Decision Principle

All three hypotheses share a common logical structure:

```
IMPORTANT FACT
+ PRIMARY REPRESENTATION IS NON-TEXT
+ NO EQUIVALENT READABLE TEXT EXISTS
→ POTENTIAL LOCK-IN
```

But the evidence collection differs by format because:
- **Images**: Check alt text, captions, nearby text
- **Documents**: Check whether page HTML duplicates document facts
- **Canvas/Video**: Check track elements, transcripts, fallback content

## Strength Assessment

| Hypothesis | Quality Score | Classification | Strength |
|-----------|--------------|----------------|----------|
| **F-001** | 4.6 | CORE | Strongest — images are universal; alt text is a clear signal |
| **F-002** | 4.2 | CANDIDATE | Good — document links are detectable; importance is heuristic |
| **F-003** | 3.8 | CANDIDATE | Reasonable — element detection is clear; content importance is uncertain |

## Evidence Required

### F-001
- Image identification in factual content areas
- Alt text analysis (empty/generic/descriptive)
- Nearby text and caption detection
- JSON-LD coverage check

### F-002
- Document link detection (file extensions, link text patterns)
- Context analysis (surrounding headings, page type)
- Page HTML text coverage of likely document facts

### F-003
- Canvas/video/object/embed element detection
- Track element presence check
- Transcript/fallback content detection
- ARIA attribute analysis
