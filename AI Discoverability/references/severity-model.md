# Severity Model — AI Discoverability Audit

## Framework

Severity is determined by the intersection of **impact**, **scope**, and **importance**. It is never assigned solely because a technical condition exists.

## Severity Levels

### CRITICAL
A core public content area is effectively inaccessible to the machine pipeline, or a major discovery gate is entirely blocked.

**Required conditions (ALL must apply):**
- The affected content is central to the site's primary purpose
- The pipeline failure is absolute (content cannot be reached, read, or extracted at all)
- The scope affects a substantial portion of the site's important content (>50% of sampled important URLs)
- The failure is persistent and reproducible

**Examples:**
- `robots.txt` blocks the entire product catalog on an e-commerce site
- >50% of important URLs persistently return 5xx errors
- All factual product content is JS-only with no SSR fallback

### HIGH
Important content/facts across a substantial portion of the site are affected.

**Required conditions:**
- The affected content is important to the site's purpose
- The failure creates a significant gap (facts unavailable, large sections blocked)
- 25-50% of sampled important URLs/facts are affected
- The failure is reproducible

**Examples:**
- 30% of important URLs are blocked by robots.txt
- All product specifications are locked in images with no alt text
- Major content sections are undiscoverable via standard links

### MEDIUM
A meaningful but limited set of important pages/facts is affected, or the issue creates a significant semantic/accessibility gap without blocking the underlying facts entirely.

**Required conditions:**
- The affected content has identifiable importance
- 10-25% of sampled important URLs/facts are affected, OR
- The failure reduces extraction precision without blocking fact access entirely

**Examples:**
- Relevant JSON-LD schemas are client-rendered (facts present in HTML, schema missing)
- Several product pages have specs in PDFs with no HTML equivalent
- Multiple factual values lack clear semantic label associations

### LOW
Minor, supplementary, or low-impact content is affected.

**Required conditions:**
- <10% of sampled important URLs/facts are affected, OR
- Only supplementary content is affected, OR
- The failure creates a minor gap unlikely to impact core discoverability

**Examples:**
- A few supplementary pages have JS-only navigation
- Blog images lack alt text
- One or two non-critical URLs return 404

### INFO / PROACTIVE
Useful improvement without a demonstrated defect.

**Required conditions:**
- No concrete defect is detected, BUT
- An improvement opportunity is identified that would strengthen discoverability

**Examples:**
- No sitemap.xml found (content may still be discoverable via links)
- All images have alt text but none have JSON-LD ImageObject markup
- Page could benefit from additional structured data types

## Severity Determination Process

1. **Identify the mechanism failure**: crawl / read / extract / lock-in
2. **Assess importance**: Is the affected content central to the site's purpose?
3. **Measure scope**: What proportion of important content is affected?
4. **Evaluate impact**: Does the failure prevent access entirely, or degrade precision?
5. **Check reproducibility**: Is the failure persistent across multiple observations?
6. **Apply level**: Match to the severity level whose conditions are met

## Key Principles

- **Never assign severity based on a technical condition alone.** A condition is only a finding if it affects important content.
- **Prefer NO FINDING over speculative findings.** When evidence is ambiguous, do not generate a finding.
- **Importance matters more than technical presence.** A robots.txt Disallow on `/admin/` is not a finding regardless of how many pages it blocks.
- **Distinguish between "prevented" and "degraded."** Blocked crawl (content completely inaccessible) is more severe than missing JSON-LD (content accessible via text, schema missing).
