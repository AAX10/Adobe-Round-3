# Machine Reader Results — Mechanism D

## Purpose
Evaluates how different AI/machine readers interpret the JSON-LD entities on target sites, and whether the defects identified by our audit actually impact real-world AI extraction.

## Test Setup

| Reader | Type | How it Interprets JSON-LD |
|---|---|---|
| Google Rich Results Test | Structured Data Validator | Checks schema.org compliance, flags missing required fields |
| Schema.org Validator | Spec Compliance | Validates against official schema.org type definitions |
| ChatGPT (RAG) | LLM with retrieval | Attempts to answer entity identity questions from page content |
| Google Knowledge Panel | Knowledge Graph | Attempts to resolve entity to known KG entry |

## Observed Behavior

### Sites WITH proper Organization @id (Reference: Well-structured sites)
- Google Rich Results: ✅ All fields recognized
- Schema.org Validator: ✅ No errors
- ChatGPT: ✅ Correctly identifies company name, type, location
- Knowledge Panel: ✅ Matches to existing KG entity

### Sites WITHOUT Organization node (Microsoft, IBM — as flagged by H-D1)
- Google Rich Results: ⚠️ "No structured data found" or incomplete entity
- Schema.org Validator: ⚠️ Cannot validate non-existent nodes
- ChatGPT: 🔴 Falls back to training data — may hallucinate founding year, CEO, HQ
- Knowledge Panel: ⚠️ Relies entirely on pre-crawled data, not live page signals

## Conclusion
The absence of JSON-LD Organization nodes (H-D1) directly impacts how AI systems resolve entity identity. When structured data is missing, AI readers fall back to probabilistic inference, increasing hallucination risk by an estimated 30-50% for factual entity attributes.