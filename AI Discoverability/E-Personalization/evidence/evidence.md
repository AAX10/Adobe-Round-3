# Evidence and Authoritative References

This document outlines the authoritative references that support the hypotheses of the Personalization & Prompt Context Alignment skill. 
It distinguishes between the established source facts and the structural audit inferences derived for this skill.

## 1. Schema.org Specifications for Geographic Properties

**Source Fact:**
The Schema.org specification for `Organization` and `LocalBusiness` explicitly defines the `areaServed` property to denote "The geographic area where a service or offered item is provided" as distinct from the `address` property which indicates the physical location of the business.

**Reference:**
- **Title**: Schema.org - Organization
- **Publisher**: Schema.org
- **URL**: https://schema.org/Organization
- **Claim Supported**: Organizations have distinct properties for physical location (`address`) versus service footprint (`areaServed`).
- **Authority**: The official specification body for structured web data.

**Audit Inference:**
If an AI system ingests structured data to populate its knowledge graph, the presence of `address` without `areaServed` structurally constrains the entity to its physical coordinate bounding box. For online or multi-region services, this omission risks geographic exclusion during RAG retrieval.

## 2. Google Search Central - Local Business Structured Data

**Source Fact:**
Google recommends providing comprehensive structured data, stating that "Google can show your business details in the Knowledge Panel... when users search for businesses." It explicitly highlights the use of `areaServed` for service-area businesses.

**Reference:**
- **Title**: Local Business structured data
- **Publisher**: Google Search Central
- **URL**: https://developers.google.com/search/docs/appearance/structured-data/local-business
- **Claim Supported**: Search engines utilize structured geographic properties to determine the valid context and reach of a business entity.
- **Authority**: Official documentation from the largest search and entity-graph provider.

**Audit Inference:**
Because modern AI assistants frequently leverage search engine APIs and Knowledge Graphs as RAG backends, failing to supply `areaServed` translates directly to limited AI discoverability outside the immediate physical locale.

## 3. Semantic Similarity and Dense Retrieval Behavior

**Source Fact:**
Dense retrieval models (like those used in RAG systems) compute relevance by embedding queries and documents into a shared vector space. Texts dominated by specific modifiers (e.g., hyper-local city names) shift the document's vector away from the generalized concept centroid, resulting in lower dot-product similarity scores for generic queries.

**Reference:**
- **Title**: Dense Passage Retrieval for Open-Domain Question Answering (Karpukhin et al., 2020)
- **Publisher**: ACL / arXiv
- **URL**: https://arxiv.org/abs/2004.04906
- **Claim Supported**: Passage embeddings are highly sensitive to the exact semantic composition of the text chunk; lack of overlapping generic terms reduces retrieval likelihood for generic queries.
- **Authority**: Seminal peer-reviewed paper defining modern dense retrieval methodologies used in RAG.

**Audit Inference:**
If a page relies exclusively on hyper-local identifiers and lacks generic fallback definitions, it is structurally at risk of being bypassed by semantic search systems when the user's prompt context is broad or out-of-region.
