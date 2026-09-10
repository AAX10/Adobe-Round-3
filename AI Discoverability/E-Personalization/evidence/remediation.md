# Remediation Strategies

This document provides mechanism-sound recommendations to mitigate the risks identified by the Personalization & Prompt Context Alignment skill.

## 1. Mitigating Contextual Breadth Risk

**Diagnosed Mechanism:** 
The primary entity definition (H1, Meta Description, first paragraph) is so heavily saturated with local or persona-specific modifiers that semantic retrieval models classify it as highly narrow, causing context-drop for generic queries.

**Suggested Action:**
Add a concise, persona-neutral, and region-agnostic entity definition that identifies the core service footprint. 
- **Where to change:** The `<meta name="description">` and the leading `<p>` tag on the homepage and "About" page.
- **Example Fix:** Instead of starting exclusively with *"We are Austin's best local neighborhood plumbers"*, update the text to: *"We are a plumbing service provider operating in the United States. We serve the greater Texas area, specializing as Austin's premier local plumber."*
- **Why this works:** It injects global semantic anchors ("plumbing service provider", "United States", "Texas") into the same embedding chunk as the local modifier, allowing the vector to overlap with generic queries while still satisfying local queries.

## 2. Mitigating Schema Localization Risk

**Diagnosed Mechanism:** 
JSON-LD structures expose a strict physical `address` but lack an `areaServed` property, structurally confining the entity to a tight geographic bounding box in AI knowledge graphs.

**Suggested Action:**
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

## 3. Mitigating Context-Variance Risk (Chunk Fragmentation)

**Diagnosed Mechanism:** 
Core service terms are inextricably bound to local terms in every single paragraph, meaning any extracted RAG chunk will carry a heavy local bias.

**Suggested Action:**
Create distinct paragraphs or standalone sentences that define the core service independent of local geographic modifiers.
- **Where to change:** Throughout the primary visible text of the homepage or service pages.
- **Example Fix:** Ensure that somewhere on the page, the service is described objectively. "Acme provides enterprise cloud security software." (No local modifiers).
- **Why this works:** When a RAG system chunks the page, it will yield at least one chunk that is purely topical and region-agnostic. This chunk acts as a safe retrieval anchor for broad, non-localized queries, preventing the LLM from dropping the source due to perceived local irrelevance.
