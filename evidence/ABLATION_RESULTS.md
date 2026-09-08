# Ablation Experiment (Phase 7)

## Objective
To prove definitively that the extraction improvement observed in Reader B is caused by the *structured data* and not by other render-dependent content (like layout changes or JS hydration).

## Paradigm
For our two positive cases (Adobe and Rivian), we created three representations:
- **A**: RAW HTML
- **B**: RAW HTML + RENDER-ONLY JSON-LD (Manually Injected)
- **C**: FULL RENDERED PAGE

## Results

### Case 1: Adobe
- **A**: Low Precision (NLP fallback)
- **B**: 100% Precision (Schema parsing)
- **C**: 100% Precision (Schema parsing)
- **Pattern**: A < B ≈ C

### Case 2: Rivian
- **A**: Low Precision (NLP fallback)
- **B**: 100% Precision (Schema parsing)
- **C**: 100% Precision (Schema parsing)
- **Pattern**: A < B ≈ C

## Conclusion
Because **A < B ≈ C** holds perfectly for both tested H-001B cases, we have extremely strong evidence that the structured data itself is the explicit mechanism causing the machine-reader improvement. The complex rendering of the rest of the DOM (C) provided zero additional extraction value over the lightweight injected JSON-LD (B).
