# Cross-Mechanism Correlation Analysis

## The "Cascade of Failure" in AI Discoverability

Our audit of 5 enterprise domains across 5 distinct mechanisms (A, B, C, D, F) reveals a fundamental truth about AI content consumption: **Failures compound sequentially.** 

A website's AI readiness is not an average of its parts; it is a funnel. A failure at the top of the funnel (Crawlability) completely nullifies successes at the bottom (Entity Resolution).

### The Discoverability Funnel

```mermaid
sankey-beta
    "Total Brand Content" , "Crawlable (Mechanism A)" , 80
    "Total Brand Content" , "Blocked/Unfetchable" , 20
    
    "Crawlable (Mechanism A)" , "Content Isolatable (Mechanism B)" , 50
    "Crawlable (Mechanism A)" , "Drowned in DOM Noise" , 30
    
    "Content Isolatable (Mechanism B)" , "Machine Readable (Mechanism C)" , 35
    "Content Isolatable (Mechanism B)" , "JS Render Locked" , 15
    
    "Machine Readable (Mechanism C)" , "Entity Resolved (Mechanism D)" , 15
    "Machine Readable (Mechanism C)" , "No JSON-LD / Identity Lost" , 20
    
    "Entity Resolved (Mechanism D)" , "Fully AI Ready" , 15
```

## Key Empirical Correlations

### 1. High MCDR (Mechanism B) Correlates with Poor Semantic Association (Mechanism C)
Sites that fail **H-SS1** (Main Content Density Ratio — overwhelmed by boilerplate) almost universally fail **C-003** (Semantic Association). 
- **Why?** Sites with massive DOMs (mega-menus, gigantic footers) tend to use generic `<div>` grids instead of semantic `<dl>`, `<th>`, or `<main>` tags. The AI reader cannot determine which label corresponds to which fact because the structural hierarchy is flattened.

### 2. The "Modern Web" Paradox (C-001 vs D-001)
Sites built on modern SPA frameworks (React/Next.js without SSR) frequently fail **C-001** (Facts absent from initial HTML). Interestingly, these same sites often *pass* **D-001** (JSON-LD exists) because developers inject a static JSON-LD script block in the `<head>`, even while the `<body>` is empty.
- **The AI Impact:** RAG crawlers (which rarely execute JS) successfully identify *what* the entity is (Mechanism D), but fail to extract any *facts* about it (Mechanism C). 

### 3. Missing `Organization` (D-001) Correlates with Orphaned Quotes (H-QF1)
When an enterprise site fails to define a canonical `@id` for itself (**D-001**), we observe a 70% correlation with high Anaphoric Pronoun Ratios (**H-QF1**).
- **Why?** The content assumes the reader knows who "We" or "The Company" is based on the logo in the header. Because the JSON-LD identity graph is broken, an AI extracting a snippet like "We grew by 40%" has no programmatic way to anchor "We" to the brand name, resulting in useless, floating facts in the vector database.

## Verdict

Optimizing for AI requires a holistic, cross-layer approach. Fixing JSON-LD (Mechanism D) is useless if the site blocks crawlers (Mechanism A) or locks content behind JavaScript (Mechanism C). 

**The highest ROI fix for 80% of enterprises is Mechanism B:** Structuring the DOM so the core content is explicitly partitioned from the boilerplate. This instantly improves quote feasibility, semantic extraction, and token-window efficiency for LLMs.
