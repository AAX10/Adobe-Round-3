# Hypothesis Registry

| ID     | Name                         | Failure Mode                                                                 | Severity | Script                       |
| ------ | ---------------------------- | ---------------------------------------------------------------------------- | -------- | ---------------------------- |
| H-SS1  | Noisy Chrome                 | Main content cannot be distinguished from navigation/footer clutter.         | High     | source-selection-auditor     |
| H-SS2  | Heading Disconnect           | Logical document sections do not correspond to semantic heading tags.        | Medium   | source-selection-auditor     |
| H-SS3  | Semantic Div Soup            | Over-reliance on generic tags instead of article/section semantic tags.      | Low      | source-selection-auditor     |
| H-QF1  | Anaphoric Pronouns           | Critical facts rely heavily on unresolved pronouns (it, they, this).         | Medium   | quote-feasibility-auditor    |
| H-QF2  | Severed Qualifiers           | Conditions or qualifiers are separated from the claims they modify.          | High     | quote-feasibility-auditor    |
| H-QF3  | Non-Contiguous Data Tables   | Complex tables cannot be serialized to Markdown without losing row relations.| High     | quote-feasibility-auditor    |
| H-QF4  | Modality Traps               | Information is locked in images or charts without alt-text or data-tables.   | Critical | quote-feasibility-auditor    |
| H-QF5  | Ephemeral State (SPA)        | Required content is only rendered client-side after user interaction.        | Critical | quote-feasibility-auditor    |
| H-QF6  | Ambiguous Terminology        | Overuse of internal jargon without local definitions.                        | Low      | quote-feasibility-auditor    |
