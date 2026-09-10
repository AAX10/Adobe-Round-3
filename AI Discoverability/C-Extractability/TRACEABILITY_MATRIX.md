# Traceability Matrix

Every surviving hypothesis traces through: mechanism → evidence → script → skill.

## A — Crawlability

### A-001 — Crawl-Blocked Important Content

| Element | Detail |
|---------|--------|
| **Hypothesis** | A-001 |
| **Handbook Mechanism** | Crawl — Section A: "the crawler has to be let in" |
| **Field Observation** | robots.txt Disallow rules can block important public content paths |
| **Supporting References** | RFC 9309, Google Search Central robots.txt docs (REF-A1, REF-A4) |
| **Experiment** | Fetch robots.txt → parse rules → test important URLs against Disallow → verify blocked URLs return 200 |
| **Observable Signal** | Important public URL matches Disallow rule and returns 200 on direct request |
| **Script** | `scripts/crawlability/robots_audit.py` |
| **Evidence** | "Tested N candidate URLs; M important public URLs are blocked by robots.txt" |
| **Severity** | Critical/High/Medium/Low based on proportion and importance |
| **Remediation** | Remove or narrow Disallow rules for important public content |
| **Future Skill** | `skills/crawl-audit/` |

---

### A-002 — Non-Crawlable Navigation

| Element | Detail |
|---------|--------|
| **Hypothesis** | A-002 |
| **Handbook Mechanism** | Crawl — Section A: discovery through links |
| **Field Observation** | JS-only navigation (Load More, onclick, infinite scroll) hides URLs from static crawlers |
| **Supporting References** | Google Search Central links docs, JS SEO docs (REF-A3, REF-A5) |
| **Experiment** | Extract static `<a href>` links → check sitemap → detect JS navigation patterns → compare link sets |
| **Observable Signal** | Important URLs present only in rendered DOM, absent from static links and sitemap |
| **Script** | `scripts/crawlability/link_discovery_audit.py` |
| **Evidence** | "Found N JS-only navigation patterns. Static links: M. Sitemap URLs: K" |
| **Severity** | High/Medium/Low based on scope of undiscoverable content |
| **Remediation** | Add crawlable `<a href>` links or include URLs in sitemap |
| **Future Skill** | `skills/crawl-audit/` |

---

### A-003 — Important URL Retrieval Failure

| Element | Detail |
|---------|--------|
| **Hypothesis** | A-003 |
| **Handbook Mechanism** | Crawl — Section A: crawler must read what's there |
| **Field Observation** | Persistent HTTP errors (4xx, 5xx, timeouts) on important URLs prevent retrieval |
| **Supporting References** | RFC 9110, Google HTTP errors docs (REF-A2, REF-A7) |
| **Experiment** | Sample important URLs → request with retries → classify persistent vs transient failures |
| **Observable Signal** | ≥10% of sampled important URLs persistently fail with non-2xx responses |
| **Script** | `scripts/crawlability/url_retrieval_audit.py` |
| **Evidence** | "Tested N URLs; M (X%) persistently failed to return usable content" |
| **Severity** | Critical/High/Medium/Low based on failure rate |
| **Remediation** | Fix broken links, resolve server errors, repair redirect chains |
| **Future Skill** | `skills/crawl-audit/` |

---

## C — Extractability

### C-001 — Render-Dependent Factual Content

| Element | Detail |
|---------|--------|
| **Hypothesis** | C-001 (formerly H-001A) |
| **Handbook Mechanism** | Read — Section C: "content is only assembled after a page loads" |
| **Field Observation** | CSR-only sites deliver empty HTML; facts appear only after JS execution |
| **Supporting References** | Google JS SEO docs (REF-C6), Handbook Section C (REF-C7) |
| **Experiment** | Dual-fetch (raw vs rendered) → identify facts in rendered DOM → verify absence from raw HTML |
| **Observable Signal** | Important factual text present in rendered DOM, completely absent from raw HTML |
| **Script** | `scripts/check_render_factual_content.py`, `scripts/extractability/fact_inventory.py` |
| **Evidence** | "Text delta: N chars. Render-only content ratio: Mx" |
| **Severity** | High — absolute factual omission for non-JS readers |
| **Remediation** | Server-render critical content via SSR/SSG |
| **Future Skill** | `skills/extractability-audit/` |

---

### C-002 — Render-Dependent Structural Metadata

| Element | Detail |
|---------|--------|
| **Hypothesis** | C-002 (formerly H-001B) |
| **Handbook Mechanism** | Extract — Section C: explicit vs implied facts |
| **Field Observation** | JSON-LD injected by JS only; raw HTML lacks semantic schema |
| **Supporting References** | Schema.org docs, Google structured data docs (REF-C4, REF-C5) |
| **Experiment** | Compare JSON-LD in raw vs rendered → filter for relevant schemas → verify text coverage → ablation |
| **Observable Signal** | Relevant JSON-LD type (FAQPage, Product) in rendered DOM but absent from raw HTML |
| **Script** | `scripts/extractability/structured_data_compare.py` |
| **Evidence** | "Render-only relevant schemas: [FAQPage]. Classification: semantic_loss" |
| **Severity** | Medium — semantic gap, but underlying facts accessible via text |
| **Remediation** | Server-render JSON-LD into initial HTML |
| **Future Skill** | `skills/extractability-audit/` |

---

### C-003 — Ambiguous Fact-to-Label Association

| Element | Detail |
|---------|--------|
| **Hypothesis** | C-003 |
| **Handbook Mechanism** | Extract — Section C: "the more explicitly and unambiguously a fact is stated" |
| **Field Observation** | Important values (prices, specs) rely on CSS layout for label association |
| **Supporting References** | WCAG 1.3.1, HTML table/dl specs (REF-C1, REF-C2, REF-C3) |
| **Experiment** | Find factual values → check DOM for semantic label (th, dt, label, ARIA) → check JSON-LD |
| **Observable Signal** | Factual values without semantic label association and no JSON-LD coverage |
| **Script** | `scripts/extractability/semantic_association_audit.py` |
| **Evidence** | "Found N factual values; M lack clear semantic label association" |
| **Severity** | Medium/Low — extraction precision risk |
| **Remediation** | Use semantic HTML (table/th, dl/dt/dd, label) or JSON-LD for value-attribute mapping |
| **Future Skill** | `skills/extractability-audit/` |

---

## F — Non-Text Lock-In

### F-001 — Image-Only Core Facts

| Element | Detail |
|---------|--------|
| **Hypothesis** | F-001 |
| **Handbook Mechanism** | Lock-in — Section F: "carried by something a summarizer can't read" |
| **Field Observation** | Factual specs/pricing communicated through images without text equivalents |
| **Supporting References** | WCAG 1.1.1, Google image docs (REF-F1, REF-F7) |
| **Experiment** | Find images in factual areas → check alt text quality → check nearby text → check JSON-LD |
| **Observable Signal** | Image in factual area with missing/generic alt text, no nearby text equivalent |
| **Script** | `scripts/non_text_lockin/image_fact_audit.py` |
| **Evidence** | "Found N images; M in factual areas lack descriptive alt text and no text equivalent" |
| **Severity** | High/Medium based on number and importance of locked facts |
| **Remediation** | Add descriptive alt text or HTML text equivalent for factual images |
| **Future Skill** | `skills/non-text-lockin-audit/` |

---

### F-002 — Document-Only Critical Information

| Element | Detail |
|---------|--------|
| **Hypothesis** | F-002 |
| **Handbook Mechanism** | Lock-in — Section F |
| **Field Observation** | Specs/pricing available only in linked PDFs, not in page HTML |
| **Supporting References** | W3C PDF techniques, Google indexable types (REF-F6, REF-F8) |
| **Experiment** | Find document links → classify by context → check if page HTML contains equivalent facts |
| **Observable Signal** | Factual document linked from page with no equivalent text in HTML |
| **Script** | `scripts/non_text_lockin/document_fact_audit.py` |
| **Evidence** | "Found N document links; M factual documents lack HTML text equivalents" |
| **Severity** | High/Medium based on criticality of locked facts |
| **Remediation** | Add HTML text equivalent (spec table, pricing section) to the page |
| **Future Skill** | `skills/non-text-lockin-audit/` |

---

### F-003 — Non-Text Interactive/Visual Fact Lock-In

| Element | Detail |
|---------|--------|
| **Hypothesis** | F-003 |
| **Handbook Mechanism** | Lock-in — Section F |
| **Field Observation** | Facts in canvas/video/interactive elements without text equivalents |
| **Supporting References** | WCAG 1.2.x, HTML canvas/video specs (REF-F2, REF-F3, REF-F4) |
| **Experiment** | Detect video/canvas/embed → check tracks/fallback/ARIA → check for data tables |
| **Observable Signal** | Non-text element in factual area without captions, transcript, or fallback content |
| **Script** | `scripts/non_text_lockin/visual_media_audit.py` |
| **Evidence** | "Found N non-text elements; M lack text equivalents in factual areas" |
| **Severity** | Medium/Low based on prevalence and importance |
| **Remediation** | Add captions, transcripts, fallback content, or data table equivalents |
| **Future Skill** | `skills/non-text-lockin-audit/` |
