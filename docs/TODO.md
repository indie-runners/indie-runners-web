# TODO: #18 — search misses races typed with ß, accents, spacing or a country

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-20_

- [x] Fold term and columns the same way in the query (`_search_fold`, two passes for ä→ae / ä→a)
- [x] Match `event_country_code` too
- [x] Acceptance 3, anon `/?search=`: `Großglockner` → Grossglockner Ultra Trail; `Fränkische` → Lowa Ultratrail Fraenkische; `Valdaran` → Val Daran Pyrenees; `Malta` → Gozo Trail Run, Valletta Marathon (4 tiles in all)
- [x] Acceptance 4: `Kiev`, `Transilvania`, `Julien` → 0 (spellings, not folds)
- [x] Acceptance 5: `glockner` 1, `trail` 60, `berlin` 32 tiles; old ⊆ new over 12 terms
- Disproved: nothing. Unsure: cost of 10 folded comparisons per row, unmeasured; the view is small.
- Paulo's aliases idea (nicknames, former sponsor names) is on the board for the scraper, not here.
