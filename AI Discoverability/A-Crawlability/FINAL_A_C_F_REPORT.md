# AI Discoverability Research Report: A + C + F Mechanisms

## Executive Summary

This report extends the AI Discoverability research from two existing hypotheses (H-001A, H-001B covering Read and Extract mechanisms) to three additional mechanisms from the Round 3 framework:

- **A — Crawlability**: 3 new hypotheses covering the crawl permission, discovery, and retrieval gates
- **C — Extractability**: 1 new hypothesis (C-003) plus 2 reformatted existing hypotheses (C-001, C-002)
- **F — Non-Text Lock-In**: 3 new hypotheses covering image, document, and visual media lock-in

**Total hypotheses**: 9 (5 CORE, 4 CANDIDATE)
**Total scripts**: 13 new Python scripts across 3 mechanism categories
**Total agent skills**: 4 reusable skill specifications

All hypotheses passed the quality bar (minimum 3.5/5.0 average). No hypotheses were rejected.

---

## Methodology

### Research Approach

1. **Handbook-first**: Every hypothesis maps to a specific mechanism and section from the Round 3 handbook
2. **Standards-backed**: All claims cite authoritative Tier 1 sources (IETF RFCs, W3C WCAG, Google Search Central, WHATWG HTML spec)
3. **Mechanism-sound**: Each hypothesis identifies a specific, testable pipeline failure (crawl gate, read gate, extract gate, lock-in gate)
4. **Falsifiable**: Every hypothesis includes explicit conditions that would reject or narrow it
5. **Counterexample-aware**: Each hypothesis lists 5+ counterexamples that should NOT generate findings

### Quality Framework

Each hypothesis was scored on 9 criteria (1-5 scale):
- Mechanistic plausibility
- Evidence quality
- Observability
- Automation feasibility
- Cross-site generalization
- False-positive resistance
- Actionability
- Unseen-site applicability
- Runtime feasibility

### Evidence Labels

Every evidence claim is explicitly labeled:
- **SOURCE-DERIVED FACT**: Directly cited from an authoritative document
- **EXPERIMENTAL OBSERVATION**: Result of our testing
- **OUR INFERENCE**: Reasoning based on evidence
- **UNPROVEN DOWNSTREAM EFFECT**: Impact on AI citations is not established

---

## Hypothesis Overview

### A — Crawlability (Average Quality: 4.6)

| ID | Name | Quality | Class | Gate |
|----|------|---------|-------|------|
| A-001 | Crawl-Blocked Important Content | 4.9 | CORE | Permission |
| A-002 | Non-Crawlable Navigation | 4.2 | CORE | Discovery |
| A-003 | Important URL Retrieval Failure | 4.8 | CORE | Retrieval |

The A hypotheses cover three sequential stages of the crawl pipeline. A page can fail at any one independently:
- **Permission** (A-001): robots.txt blocks the crawler
- **Discovery** (A-002): No crawlable link exposes the URL
- **Retrieval** (A-003): HTTP request fails to return usable content

### C — Extractability (Average Quality: 4.2)

| ID | Name | Quality | Class | Type |
|----|------|---------|-------|------|
| C-001 | Render-Dependent Factual Content | 4.4 | CORE | Information Loss |
| C-002 | Render-Dependent Structural Metadata | 4.6 | CANDIDATE | Semantic Loss |
| C-003 | Ambiguous Fact-to-Label Association | 3.7 | CANDIDATE | Association Loss |

The C hypotheses cover three layers of extraction degradation, ordered by severity:
- **Information Loss** (C-001): Facts themselves are absent from initial HTML
- **Semantic Loss** (C-002): Facts present but explicit schema missing from initial HTML
- **Association Loss** (C-003): Facts present but value-to-label mapping is ambiguous

### F — Non-Text Lock-In (Average Quality: 4.2)

| ID | Name | Quality | Class | Format |
|----|------|---------|-------|--------|
| F-001 | Image-Only Core Facts | 4.6 | CORE | Images |
| F-002 | Document-Only Critical Information | 4.2 | CANDIDATE | PDFs/Docs |
| F-003 | Non-Text Interactive/Visual Lock-In | 3.8 | CANDIDATE | Canvas/Video |

The F hypotheses share a common logic (fact + non-text representation + no text equivalent = lock-in) but differ in detection methods because each media type has different accessibility mechanisms.

---

## Script Architecture

### Crawlability Scripts (`scripts/crawlability/`)
| Script | Hypothesis | Input | Output |
|--------|-----------|-------|--------|
| `robots_audit.py` | A-001 | Base URL + candidate URLs | JSON with blocked URLs |
| `link_discovery_audit.py` | A-002 | Page URL | JSON with JS navigation patterns |
| `url_retrieval_audit.py` | A-003 | Base URL + candidate URLs | JSON with failure rates |
| `crawlability_report.py` | Aggregate | Individual check JSONs | Unified report |

### Extractability Scripts (`scripts/extractability/`)
| Script | Hypothesis | Input | Output |
|--------|-----------|-------|--------|
| `render_compare.py` | C-001, C-002 | Raw + rendered HTML files | JSON comparison |
| `structured_data_compare.py` | C-002 | Raw + rendered HTML files | JSON with schema diff |
| `fact_inventory.py` | C-001, C-002, C-003 | URL or HTML file | JSON with classified facts |
| `semantic_association_audit.py` | C-003 | URL or HTML file | JSON with orphaned values |
| `extractability_report.py` | Aggregate | Individual check JSONs | Unified report |

### Non-Text Lock-In Scripts (`scripts/non_text_lockin/`)
| Script | Hypothesis | Input | Output |
|--------|-----------|-------|--------|
| `image_fact_audit.py` | F-001 | URL or HTML file | JSON with flagged images |
| `document_fact_audit.py` | F-002 | URL or HTML file | JSON with flagged documents |
| `visual_media_audit.py` | F-003 | URL or HTML file | JSON with flagged media |
| `non_text_report.py` | Aggregate | Individual check JSONs | Unified report |

### Shared Design Principles
- All scripts accept `--help` and produce structured JSON output
- No site-specific rules are embedded anywhere
- All scripts use `--output` for file output or stdout for piping
- Respectful rate limiting (200-300ms between requests)
- Bounded input (MAX_URLS limits prevent runaway execution)

---

## Key Design Decisions

### 1. Evidence vs. Overclaim

We explicitly distinguish between what we can prove and what we cannot:
- **PROVEN**: A mechanism gate blocks content from entering the pipeline
- **NOT PROVEN**: That the blocked content would have been cited by AI assistants

This conservative approach prevents overclaiming while maintaining scientific rigor.

### 2. False-Positive Mitigation

Every hypothesis includes:
- Explicit counterexample lists (5+ per hypothesis)
- Admin/private path filtering (A-001)
- Importance classification (all hypotheses)
- Transient vs. persistent failure distinction (A-003)
- Relevance filtering for generic schemas (C-002)
- Decorative content exclusion (F-001, F-003)

### 3. No Site-Specific Rules

All checks use generic patterns. No hypothesis or script contains rules specific to Adobe, Rivian, Airbnb, Zocdoc, or any other research site.

### 4. Runtime Feasibility

All scripts complete well under the 5-minute target:
- A-001: ~1-2s (single HTTP request + local parsing)
- A-002: ~2-5s (HTTP request + HTML parsing + optional sitemap)
- A-003: ~10-30s (bounded URL sampling with retries)
- C-001/C-002: ~5-10s (requires rendering for full comparison)
- C-003: ~1-3s (local HTML parsing)
- F-001/F-002/F-003: ~1-3s each (local HTML parsing)

---

## Limitations

1. **No downstream AI impact proof**: We prove mechanism-level pipeline failures, not AI citation/ranking loss
2. **Importance classification is heuristic-based**: "Important content" is determined by signals (page type, heading association, navigation presence) rather than ground truth
3. **Some checks require rendering**: C-001 and C-002 need headless browser comparison for full analysis
4. **Canvas/video content analysis is bounded**: F-003 uses deterministic signals, not computer vision
5. **Sample-based coverage**: Large sites cannot be exhaustively audited; findings are based on sampled URLs

---

## Conclusion

The 9 hypotheses across A, C, and F mechanisms provide a comprehensive, standards-backed, deterministic audit framework for AI discoverability. Each hypothesis is:
- Rooted in authoritative standards
- Falsifiable with explicit counterexamples
- Implementable as a deterministic script
- Packageable as a reusable agent skill
- Applicable to any public website without modification
