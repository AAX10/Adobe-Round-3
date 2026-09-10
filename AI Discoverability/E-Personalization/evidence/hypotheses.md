# Hypotheses: Personalization & Prompt Context Alignment

This document details the 3 hypotheses investigated by this Agent Skill, designed to detect and report vulnerabilities where content becomes hyper-localized or narrowly scoped, causing AI context-drop.

## Hypothesis 1: Contextual Breadth & Entity Anchors

A. **Hypothesis title:** Contextual Breadth & Entity Anchors

B. **Hypothesis statement:** 
If an entity's primary homepage or about-page definition (e.g., meta description, main H1, leading paragraph) relies exclusively on local geographical or niche persona identifiers without a broader, persona-neutral and region-agnostic fallback statement, then AI retrieval systems are more likely to drop this source for generalized or out-of-region queries because the semantic embedding vector is overly biased toward the narrow local context rather than the core entity concept.

C. **Mechanism:** 
Semantic retrieval models map text to vector space. Text saturated with local markers pushes the document vector away from the broader semantic category. A lack of global semantic anchors (e.g., country names, generic industry terms) lowers the dot-product similarity for out-of-context queries.

D. **Observable signals:** 
Count and ratio of local location markers (cities, neighborhoods) versus generalized markers (state, country, generic service categories) in `<title>`, `<meta name="description">`, `<h1>`, and the first `<p>`.

E. **Falsification criteria:** 
If the page prominently includes state-level, national, or broad categorical qualifiers alongside the local ones, the hypothesis is weakened.

F. **Minimum evidence required to report a finding:** 
The primary definition text must contain multiple local geo-markers and strictly zero higher-level geographic markers or generic entity markers.

G. **Severity recommendation:** 
HIGH. High likelihood of discoverability failure for out-of-region conversational contexts.

H. **False-positive controls:** 
If the entity is explicitly a single-location brick-and-mortar store with no online services, this is an expected restriction, but typically structured data (`areaServed`) clarifies this intent.

I. **Suggested remediation:** 
Add a concise, persona-neutral, and region-agnostic entity definition that identifies the core service footprint. 
- **Where to change:** The `<meta name="description">` and the leading `<p>` tag on the homepage and "About" page.
- **Example Fix:** Instead of starting exclusively with *"We are Austin's best local neighborhood plumbers"*, update the text to: *"We are a plumbing service provider operating in the United States. We serve the greater Texas area, specializing as Austin's premier local plumber."*
- **Why this works:** It injects global semantic anchors ("plumbing service provider", "United States", "Texas") into the same embedding chunk as the local modifier, allowing the vector to overlap with generic queries while still satisfying local queries.

J. **High-quality external references:** 
- **Title**: Dense Passage Retrieval for Open-Domain Question Answering (Karpukhin et al., 2020)
- **Publisher**: ACL / arXiv
- **URL**: https://arxiv.org/abs/2004.04906
- **Claim Supported**: Passage embeddings are highly sensitive to the exact semantic composition of the text chunk; lack of overlapping generic terms reduces retrieval likelihood for generic queries.
- **Authority**: Seminal peer-reviewed paper defining modern dense retrieval methodologies used in RAG.

---

## Hypothesis 2: Schema Localization

A. **Hypothesis title:** Schema Localization

B. **Hypothesis statement:** 
If a web page representing an organization specifies an `address` property in its JSON-LD structured data but omits the `areaServed` (or a multi-region property) when offering broader services, then an AI assistant is more likely to restrict the source's relevance strictly to the user's immediate physical location, because knowledge graphs and entity extraction systems use structured address data as a strong geographic bounding box unless explicitly widened.

C. **Mechanism:** 
Structured data is ingested into Knowledge Graphs used by AI via RAG APIs. A strict `address` without an `areaServed` implies a physical-only presence, instructing retrieval systems to filter out this entity for users querying from outside that radius.

D. **Observable signals:** 
Presence of `Organization` or `LocalBusiness` JSON-LD. Presence of `address`. Absence of `areaServed`.

E. **Falsification criteria:** 
Presence of `areaServed`, `location`, or explicitly defined service footprints.

F. **Minimum evidence required to report a finding:** 
Valid JSON-LD schema parsed containing an address but no multi-region or area expansion.

G. **Severity recommendation:** 
HIGH. Strict bounding box constraints drastically reduce relevance for broad queries.

H. **False-positive controls:** 
Only trigger on `Organization` or `LocalBusiness` types. Do not trigger if no schema is present.

I. **Suggested remediation:** 
Explicitly define the regional or global footprint of the service in the structured data.
- **Where to change:** Within the `Organization` or `LocalBusiness` JSON-LD `<script type="application/ld+json">` tag.
- **Example Fix:** 
  ```json
  {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": "Acme Tech Services",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "Austin",
      "addressRegion": "TX"
    },
    "areaServed": [
      {
        "@type": "State",
        "name": "Texas"
      },
      {
        "@type": "Country",
        "name": "United States"
      }
    ]
  }
  ```
- **Why this works:** It provides a deterministic, machine-readable footprint expansion, overriding the default assumption that the business only exists at its physical coordinates.

J. **High-quality external references:** 
- **Title**: Schema.org - Organization
- **Publisher**: Schema.org
- **URL**: https://schema.org/Organization
- **Claim Supported**: Organizations have distinct properties for physical location (`address`) versus service footprint (`areaServed`).
- **Authority**: The official specification body for structured web data.
- **Title**: Local Business structured data
- **Publisher**: Google Search Central
- **URL**: https://developers.google.com/search/docs/appearance/structured-data/local-business
- **Claim Supported**: Search engines utilize structured geographic properties to determine the valid context and reach of a business entity.
- **Authority**: Official documentation from the largest search and entity-graph provider.

---

## Hypothesis 3: Context-Variance Structural Risk (Chunk Fragmentation)

A. **Hypothesis title:** Context-Variance Structural Risk (Chunk Fragmentation)

B. **Hypothesis statement:** 
If the entity's visible content heavily clusters its core service terms exclusively with local region terms, while lacking paragraphs that combine the core service with broader regions or persona-agnostic framing, then there is a structural risk of retrieval variance, because chunk-based RAG systems may isolate local terms from the core service offering, causing the LLM to drop the source for adjacent conversational contexts.

C. **Mechanism:** 
RAG splits pages into chunks. If core service definitions are inextricably bound to local terms in every chunk, any chunk retrieved for a generic query will carry heavy local bias. The LLM may subsequently discard the chunk as irrelevant to a non-local user.

D. **Observable signals:** 
Co-occurrence analysis in paragraphs: Core entity terms appearing exclusively alongside local geographic terms, and never independently.

E. **Falsification criteria:** 
Core services appearing in paragraphs without local modifiers.

F. **Minimum evidence required to report a finding:** 
Observation of multiple paragraphs where services and local terms co-occur, with zero paragraphs where services appear neutrally.

G. **Severity recommendation:** 
MEDIUM. High inferred structural risk, but depends heavily on the specific RAG chunking strategy employed by the downstream AI.

H. **False-positive controls:** 
Require a statistically significant number of paragraph samples to establish a strict exclusivity pattern.

I. **Suggested remediation:** 
Create distinct paragraphs or standalone sentences that define the core service independent of local geographic modifiers.
- **Where to change:** Throughout the primary visible text of the homepage or service pages.
- **Example Fix:** Ensure that somewhere on the page, the service is described objectively. "Acme provides enterprise cloud security software." (No local modifiers).
- **Why this works:** When a RAG system chunks the page, it will yield at least one chunk that is purely topical and region-agnostic. This chunk acts as a safe retrieval anchor for broad, non-localized queries, preventing the LLM from dropping the source due to perceived local irrelevance.

J. **High-quality external references:** 
- **Title**: Dense Passage Retrieval for Open-Domain Question Answering (Karpukhin et al., 2020)
- **Publisher**: ACL / arXiv
- **URL**: https://arxiv.org/abs/2004.04906
- **Claim Supported**: Passage embeddings are highly sensitive to the exact semantic composition of the text chunk; lack of overlapping generic terms reduces retrieval likelihood for generic queries.
- **Authority**: Seminal peer-reviewed paper defining modern dense retrieval methodologies used in RAG.
