# Linguistic Rules for AI Quote Feasibility

This reference document outlines the heuristics used to parse and evaluate textual content for AI discoverability.

## 1. Sentence Splitting
- Uses standard punctuation boundaries (`.`, `!`, `?`).
- Protects common abbreviations to prevent incorrect splits (e.g., Mr., Dr., Capt.).

## 2. Anaphoric Pronouns
- Focuses on initial sentence pronouns that can strip context when extracted.
- Targeted pronouns: `It`, `They`, `This`, `These`, `That`, `Those`.

## 3. Entity Extraction
- Uses a basic multi-word capitalized phrase matching regex: `\b[A-Z][a-z]+\s+[A-Z][a-z]+\b`.
- Captures common proper nouns effectively for baseline entity grounding checks.

## 4. Numeric Claim Contextualization
- Recognizes percentages (`%`), currencies (`$`), multipliers (`x`), and specific domain nouns (`users`, `customers`).
- Validates the presence of **qualifiers** (e.g., `up to`, `starting at`, `subject to`).
- Validates **baselines** (e.g., `than`, `baseline`, `compared to`) for percentages.
- Validates **timeframes** (e.g., `year`, `month`, `quarter`) for financial and large numeric claims.

## 5. Fluff vs Factual Content
- Identifies common marketing fluff words that diminish fact-density.
- Fluff corpus includes: `innovative`, `cutting-edge`, `revolutionary`, `seamless`, `robust`, `state-of-the-art`, etc.
- Calculates a fluff density ratio across paragraphs to flag overly promotional content.
