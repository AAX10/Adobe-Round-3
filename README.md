# AI Discoverability Research — 3 Domain Mechanisms

Research investigating why brand content may be invisible or misrepresented in AI assistant answers. We identify **3 domain mechanisms** where the AI discovery pipeline can fail, define **9 testable hypotheses**, and provide **13 automated audit scripts** to detect these failures on any public website.

## What We Proved

We proved that **technical mechanism gates** can block content from entering an AI reader's pipeline:

| Mechanism | What Breaks | Proven? |
|-----------|------------|---------|
| **A — Crawlability** | Bots can't access the page at all (robots.txt blocks, JS-only navigation, HTTP failures) | ✅ Mechanism proven |
| **C — Extractability** | Bots reach the page but can't extract facts properly (render-dependent content, missing schemas, ambiguous labels) | ✅ Mechanism proven |
| **F — Non-Text Lock-In** | Facts are trapped in images, PDFs, or videos with no text equivalent | ✅ Mechanism proven |

> **What remains UNPROVEN**: Direct impact on AI assistant citations or rankings. We prove pipeline-level failures only.

## Repository Structure

```
ai-discoverability/
│
├── mechanisms/                    # The 3 domain mechanism overviews
│   ├── A-crawlability/README.md   #   Crawl permission, discovery, retrieval
│   ├── C-extractability/README.md #   Information loss, semantic loss, association loss
│   └── F-non-text-lockin/README.md#   Image, document, visual media lock-in
│
├── hypotheses/                    # All 9 hypothesis documents (full detail)
│   ├── A-crawlability/            #   A-001, A-002, A-003
│   ├── C-extractability/          #   C-001, C-002, C-003
│   └── F-non-text-lockin/         #   F-001, F-002, F-003
│
├── scripts/                       # All 13 executable audit scripts
│   ├── crawlability/              #   robots_audit.py, link_discovery_audit.py, url_retrieval_audit.py
│   ├── extractability/            #   render_compare.py, structured_data_compare.py, fact_inventory.py, semantic_association_audit.py
│   └── non_text_lockin/           #   image_fact_audit.py, document_fact_audit.py, visual_media_audit.py
│
├── proven/                        # Final results and reports
│   ├── FINAL_A_C_F_REPORT.md      #   Comprehensive report across all 3 mechanisms
│   ├── FINAL_REPORT.md            #   27-site cross-validation report
│   ├── CANONICAL_RESULT.json      #   Machine-readable canonical result
│   └── final_result.json          #   Structured hypothesis result (H-001)
│
├── evidence/                      # Raw evidence supporting the hypotheses
│   ├── ABLATION_RESULTS.md        #   Ablation test proving the mechanism
│   ├── COUNTEREXAMPLES.md         #   Sites that disprove overclaims
│   ├── CROSS_VALIDATION_MATRIX.md #   Cross-site validation matrix
│   ├── MACHINE_READER_RESULTS.md  #   Machine reader extraction comparison
│   ├── site_inventory.json        #   All sites tested
│   ├── all_results.json           #   Full cross-site results
│   └── cross_site_results.json    #   Summary cross-site results
│
├── references/                    # Authoritative source citations
│   ├── crawl-sources.md           #   RFC 9309, Google Search Central, etc.
│   ├── extractability-sources.md  #   Schema.org, Google Structured Data, etc.
│   ├── non-text-sources.md        #   WCAG 1.1.1, W3C PDF techniques, etc.
│   └── severity-model.md          #   Severity classification model
│
├── HYPOTHESIS_REGISTRY.md         # Master registry of all 9 hypotheses with quality scores
├── TRACEABILITY_MATRIX.md         # Full traceability: mechanism → evidence → script → skill
└── requirements.txt               # Python dependencies
```

## Hypothesis Summary

| ID | Name | Domain | Quality | Class |
|----|------|--------|---------|-------|
| A-001 | Crawl-Blocked Important Content | Crawlability | 4.9 | **CORE** |
| A-002 | Non-Crawlable Navigation | Crawlability | 4.2 | **CORE** |
| A-003 | Important URL Retrieval Failure | Crawlability | 4.8 | **CORE** |
| C-001 | Render-Dependent Factual Content | Extractability | 4.4 | **CORE** |
| C-002 | Render-Dependent Structural Metadata | Extractability | 4.6 | **CANDIDATE** |
| C-003 | Ambiguous Fact-to-Label Association | Extractability | 3.7 | **CANDIDATE** |
| F-001 | Image-Only Core Facts | Non-Text Lock-In | 4.6 | **CORE** |
| F-002 | Document-Only Critical Information | Non-Text Lock-In | 4.2 | **CANDIDATE** |
| F-003 | Non-Text Interactive/Visual Lock-In | Non-Text Lock-In | 3.8 | **CANDIDATE** |

**5 CORE** checks (ready for production) · **4 CANDIDATE** checks (sound, needs extra false-positive safeguards)

## Evidence Labels

Every claim in this research is explicitly tagged:
- **SOURCE-DERIVED FACT** — Cited from an authoritative document (RFC, W3C, Google)
- **EXPERIMENTAL OBSERVATION** — Result of our testing
- **OUR INFERENCE** — Reasoning based on evidence
- **UNPROVEN DOWNSTREAM EFFECT** — Impact on AI citations is NOT established

## Quick Start

```bash
pip install -r requirements.txt

# Run a crawlability check
python scripts/crawlability/robots_audit.py --url https://example.com

# Run an extractability check
python scripts/extractability/semantic_association_audit.py --url https://example.com

# Run a non-text lock-in check
python scripts/non_text_lockin/image_fact_audit.py --url https://example.com
```

All scripts accept `--help`, produce structured JSON output, and work on any public website.

## Key Design Principles

1. **No overclaiming** — We distinguish proven mechanisms from unproven downstream effects
2. **No site-specific rules** — All checks are generic and work on any website
3. **Counterexample-aware** — Every hypothesis lists 5+ cases that should NOT be flagged
4. **Standards-backed** — All claims cite RFC, W3C, or Google documentation
5. **Deterministic** — No LLM-dependent logic in the core audit scripts
