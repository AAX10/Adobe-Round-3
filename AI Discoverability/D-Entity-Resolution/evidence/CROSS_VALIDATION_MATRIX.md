# Cross-Validation Matrix — Mechanism D

## Purpose
Cross-validates Mechanism D findings against other mechanisms to identify correlated defects.

## Cross-Mechanism Correlation

| Site | D (Entity Resolution) | B (Source Selection) | Correlation |
|---|---|---|---|
| Microsoft | H-D1: No Organization node | Untested | If D fails, B's quote feasibility may also suffer — ungrounded entity names in content |
| IBM | H-D1 + H-D4 | Untested | Missing entity identity (D) + uncorroborated claims (D4) suggests poor overall AI readiness |

## Hypothesis Dependency Map

```
A (Crawlability) → Can the page be fetched?
  ↓ YES
B (Source Selection) → Can the content be isolated from noise?
  ↓ YES
C (Extractability) → Can facts be machine-read?
  ↓ YES
D (Entity Resolution) → Can the entity be identified in a knowledge graph?
  ↓ YES
F (Non-Text) → Are non-text assets (images, PDFs) also accessible?
```

## Key Insight
Mechanism D sits at the **end of the AI discoverability pipeline**. A page that passes A (crawlable), B (content isolatable), and C (facts extractable) can still fail D if its JSON-LD entity graph is disconnected. This means D catches defects that are invisible to content-focused checks.

## Validation Against External Tools

| Our Finding | Google Structured Data Testing Tool | Agreement? |
|---|---|---|
| H-D1: No Organization | "No structured data found" for Organization type | ✅ Confirmed |
| H-D4: Claims without citations | Not checked by Google's tool | N/A — our unique check |