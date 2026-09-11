# Brand AI Readiness Audit — Agent Skill Marketplace

> **Adobe University Hackathon 2026 — Round 3**
> An end-to-end audit pipeline that evaluates whether enterprise websites are optimized for **AI discoverability** and **on-site engagement**.

---

## Architecture

```
URL
 │
 ▼
master-orchestrator (single entrypoint)
 │
 ├─► Pass 1: On-Site Engagement (Node.js)
 │   └─► run_audit.js ──► capture + 4 check categories
 │       │
 │       ├─ technical_baseline (always)
 │       ├─ conversion_friction (if transaction-focused)
 │       ├─ retention_content (if repeat-visit/content)
 │       └─ local_trust_leads (if lead-gen/local)
 │
 ├─► Pass 2: AI Discoverability (Python)
 │   └─► run_discoverability_audit.py ──► 6 mechanisms
 │       │
 │       ├─ A — Crawlability (robots.txt, link graph, HTTP codes)
 │       ├─ B — Source Selection (content density, heading locality, quote feasibility)
 │       ├─ C — Extractability (render-dependent content, structured data, fact-label)
 │       ├─ D — Entity Resolution (JSON-LD identity, sameAs, cross-modal consistency)
 │       ├─ E — Personalization (context retention signals)
 │       └─ F — Non-Text Lock-In (image alt, video transcripts, PDF extraction)
 │
 └─► Merge findings ──► Unified JSON Report
```

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/AAX10/Adobe-Round-3.git
cd Adobe-Round-3

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the engagement audit (Node.js)
node skills/engagement-audit-orchestrator/scripts/run_audit.js https://www.adobe.com

# 4. Run the discoverability audit (Python)
python skills/master-orchestrator/scripts/run_discoverability_audit.py https://www.adobe.com
```

## Skills

| Skill | Domain | Role |
|---|---|---|
| `master-orchestrator` **(entrypoint)** | Both | Coordinates both audit passes, merges findings into one unified report |
| `engagement-audit-orchestrator` | Engagement | Judges business model, selects relevant checks, cites research, emits engagement report |
| `site-capture` | Engagement | Documents the capture phase (homepage fetch, internal page sampling, genre signals) |
| `engagement-technical-baseline` | Engagement | Response time, accessibility screening, page complexity |
| `engagement-conversion-friction` | Engagement | Media quality, checkout friction, trust signals, dark patterns |
| `engagement-retention-content` | Engagement | Related content, ad density, freshness, onboarding, return triggers |
| `engagement-local-trust-leads` | Engagement | Contact accessibility, response-time expectations, review visibility |
| `A-Crawlability` | Discoverability | robots.txt, link graph, HTTP retrieval |
| `B-Source-Selection` | Discoverability | Content density, heading-answer locality, quote feasibility |
| `C-Extractability` | Discoverability | Render-dependent content, structured data, fact-label mapping |
| `D-Entity-Resolution` | Discoverability | JSON-LD identity, sameAs links, cross-modal consistency |
| `E-Personalization` | Discoverability | Context retention signals |
| `F-Non-Text-Lock-In` | Discoverability | Image alt text, video transcripts, PDF extraction |

## Design Principles

1. **No browser automation.** Zero dependency on Playwright, Puppeteer, or Selenium at runtime. All fetching uses Node.js `fetch` (engagement) and Python `requests` (discoverability).
2. **Business-model judgment is a reasoning step, not a regex vote.** The engagement orchestrator reads site text and makes a real analytical judgment, not a threshold on keyword counts.
3. **Every severity is grounded in cited research.** Baymard Institute, MIT/InsideSales.com, Harvard Business Review, WebAIM Million 2026, and more. Full citations in `skills/engagement-audit-orchestrator/references/research-basis.md`.
4. **Tight runtime budget.** Both passes combined target well under 5 minutes.
5. **Recommend-only.** No skill alters live site state.

## Output Schema

Both passes produce findings matching this standardized shape:

```json
{
  "site": "example.com",
  "audited_at": "2026-09-10T12:00:00Z",
  "scope": "full-audit",
  "site_understanding": "Business model judgment sentence.",
  "summary": { "total_findings": 10, "critical": 1, "high": 3, "medium": 4, "low": 2 },
  "findings": [
    {
      "id": "E-001",
      "title": "Finding title",
      "severity": "high",
      "evidence": "Concrete, traceable evidence.",
      "suggested_action": { "summary": "Fix with cited research.", "priority": "high" }
    }
  ],
  "proactive_suggestions": [],
  "coverage_gaps": []
}
```

## License

MIT — see [LICENSE](LICENSE) for details.
