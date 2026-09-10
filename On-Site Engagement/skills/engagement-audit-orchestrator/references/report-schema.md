# Final report schema (on-site engagement scope)

Required top-level fields: `site`, `audited_at`, `summary` (with `total_findings`,
`critical`, `high`, `medium`), `findings` (array).

Extensions used by this marketplace beyond the contest's minimum floor:
- `site_understanding`: a one-to-two sentence analytical judgment of what the
  site actually is and how it makes or sustains money, written by the
  orchestrator from reading the captured content directly — not a genre
  label, not copied from `genre_signals`. This is what drives which check
  skills get dispatched (see `SKILL.md` step 3). Always present.
- `scope`: always the literal string `"on-site-engagement"` — makes explicit to any
  downstream consumer (e.g. a paired discoverability marketplace) that this report
  does not cover crawlability/citation concerns.
- `genre_signals`: the raw regex/schema scores from `site-capture`, included so a
  human reviewer can see the corroborating evidence behind `site_understanding`
  — supporting evidence for the orchestrator's judgment, never the
  decision-maker itself.
- `summary.low`: count of low-severity findings, beyond the required floor.
- `proactive_suggestions`: array of `{ summary, priority }` objects with no
  corresponding `finding` — improvements suggested even where no defect was
  detected, as explicitly invited by the brief.
- `coverage_gaps`: array of `{ check, reason }` objects listing any check that
  could not run because `site-capture` ran in `fetch_only` mode (no browser
  runtime was already available, and none was installed, to keep total audit
  runtime bounded — see `site-capture/SKILL.md` step 0). Empty when
  `render_mode` was `full_browser`. This keeps a missing check from being
  silently misread as either a pass or a fail.

Each `findings[i]` object:
| field | required | notes |
|---|---|---|
| `id` | yes | `F-001`, `F-002`, ... in final priority order |
| `title` | yes | short, human-scannable |
| `severity` | yes | `critical`/`high`/`medium`/`low` |
| `evidence` | yes | concrete measurement or specific URL(s); never a bare verdict |
| `suggested_action.summary` | yes | what to change |
| `suggested_action.priority` | yes | independent of severity — usually matches, but can differ if a low-severity finding has a very cheap, very high-leverage fix worth doing first |
