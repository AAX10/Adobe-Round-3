# Severity rubric (applied consistently across all check skills)

Severity should reflect (reach x consequence), not just how "bad" a pattern sounds:

- **critical** — the site (or a core flow) is effectively broken for most visitors:
  unreachable, primary conversion/read path fails entirely, or a legal/accessibility
  blocker excludes a whole class of users.
- **high** — affects most visitors on a high-traffic surface (homepage, every
  product/article page) and has a clear, direct link to drop-off (slow LCP, no
  sticky mobile CTA, horizontal scroll, high ad density mid-article).
- **medium** — affects a meaningful subset of visitors or sessions, or has an
  indirect-but-well-evidenced link to engagement (missing trust signals, stale
  front page, undersized tap targets, moderate accessibility issues grouped).
- **low** — real but narrow in reach, cosmetic, or evidence-only/proactive in
  nature (e.g. no zoom on product images, no return-trigger infrastructure where
  the site may intentionally rely on habitual visits).

`suggested_action.priority` usually matches `severity` but is allowed to diverge
when a low-severity finding has a disproportionately cheap fix (e.g. adding a
viewport meta tag) worth sequencing early regardless of its measured impact.
