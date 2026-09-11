# Density Heuristics Reference

## Main Content Density Ratio (MCDR)

$$MCDR = \frac{\text{Main Content Tokens}}{\text{Total Container DOM Tokens}}$$

### Calibration Rationale
- Enterprise SaaS pages (Stripe, Vercel) typically score **0.45–0.65** MCDR.
- Documentation sites (MDN, Python docs) score **0.70–0.90**.
- Heavy marketing pages with mega-navs score **0.15–0.30**.
- A threshold of **0.35** balances sensitivity against false positives on legitimate nav-heavy pages.

### Main Content Detection Priority
1. `<main>` semantic landmark tag
2. `<article>` tag
3. `role="main"` ARIA attribute
4. Heuristic: largest `<div>`/`<section>` by text density ratio

---

## Heading-to-Answer Locality (HAL)

$$HAL = \max\left(0,\ 1 - \frac{\text{CharDistance}(\text{Heading}, \text{Answer})}{250}\right)$$

### Calibration Rationale
- Well-structured pages place answers within **0–50 characters** of a heading (HAL ≈ 0.80–1.00).
- Pages with intervening promo banners create **150–400 character** gaps (HAL < 0.40).
- The 250-character denominator was chosen empirically: most RAG chunkers use a 256-token window, which translates to roughly 250 characters of heading → answer travel.

### Intervening Element Analysis
The auditor tracks which DOM elements appear between a heading and its answer paragraph. Common offenders include:
- `<div>` promotional banners
- `<figure>` hero images without alt text
- `<nav>` breadcrumb/sub-navigation blocks

---

## Composite Source Selection Score

$$Score_{SS} = 0.55 \times MCDR + 0.45 \times HAL$$

### Weight Rationale
Content density (MCDR) receives slightly higher weight because even with perfect heading locality, a page drowning in boilerplate will produce noisy RAG chunks. Heading locality (HAL) is critical but secondary because it affects answer precision rather than retrieval recall.

### Severity Mapping
| Score Range | Severity | Interpretation |
|---|---|---|
| < 0.40 | Critical | RAG retrievers will drop or mangle core claims |
| 0.40 – 0.65 | High | High likelihood of polluted retrieval chunks |
| 0.65 – 0.82 | Medium | Minor content isolation issues |
| ≥ 0.82 | Pass | Page is fully retrieval-optimized |
