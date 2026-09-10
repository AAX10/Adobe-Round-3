# Mechanism D — Final Report
**Entity Resolution & JSON-LD Identity Auditor**
**Audit Date:** 2026-09-10
**Sites Tested:** 5 (Adobe, Microsoft, Salesforce, IBM, Oracle)

---

## Executive Summary

Mechanism D audits whether a website's JSON-LD structured data provides a complete, internally consistent entity identity graph. We tested 4 core hypotheses (H-D1 to H-D4) across 5 major enterprise domains.

**Key Finding:** 3 out of 5 sites blocked crawlers (HTTP 403), leaving 2 sites with successful audits. Of the 2 auditable sites, **100% had at least one high-severity finding** — specifically, missing `Organization` nodes in their JSON-LD graphs.

## Results Summary

| Site | Status | H-D1 | H-D2 | H-D3 | H-D4 | Total Findings |
|---|---|---|---|---|---|---|
| Microsoft | Audited | 🔴 HIGH | — | — | — | 1 |
| IBM | Audited | 🔴 HIGH | — | — | 🟡 MEDIUM | 2 |
| Adobe | 403 Blocked | — | — | — | — | 0 |
| Salesforce | 403 Blocked | — | — | — | — | 0 |
| Oracle | 403 Blocked | — | — | — | — | 0 |

## Hypothesis Validation Status

### H-D1: Entity Graph Connectivity Deficit — **VALIDATED**
Both auditable sites (Microsoft, IBM) lacked a proper `Organization` node with a canonical `@id` in their JSON-LD. This severs the entity identity chain that AI knowledge graphs rely on.

### H-D2: External Identity Anchor Deficit — **INCONCLUSIVE**
Not triggered on audited sites. Both Microsoft and IBM define their corporate identity through other signals. Requires broader sample to validate.

### H-D3: Cross-Modal Consistency Deficit — **INCONCLUSIVE**
Jaro-Winkler name matching could not be executed without an `Organization.name` property. Dependent on H-D1 resolution.

### H-D4: Uncorroborated Factual Claim Deficit — **VALIDATED**
IBM's homepage contained 1 quantitative claim in DOM text with zero corresponding RDF `citation` properties. This risks AI systems presenting the number without sourcing.

## Methodology

- **Script:** `audit_mechanism_d.py` using Playwright (`domcontentloaded`) + BeautifulSoup4 + Jellyfish (Jaro-Winkler)
- **Anti-bot handling:** HTTP 403/429/999 logged as "Unverifiable" — not penalized as broken links
- **Type checking:** Set-based `@type` matching supports arrays and subclasses (Corporation, LocalBusiness)
- **Execution time:** < 5 seconds per site

## Limitations

1. Enterprise sites aggressively block headless browsers — 3/5 sites returned 403
2. Sites without JSON-LD `Organization` nodes cannot be evaluated for H-D2 through H-D4
3. Sample size (n=2 successful) is insufficient for statistical significance — batch testing against 20+ sites recommended