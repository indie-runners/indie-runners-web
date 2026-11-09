# W-099 — Search misses races we have: ß, accents, spacing, and a country typed into the box

`priority: 3` · `effort: S` · `area: search` · `deploy: batched`
`source: docs/IDEAS.md 2026-11-02 (scraper analyst for Paulo), options A and B(i)`

## What is wrong

Paulo: *"we have to make it easier for people to find"*. The search box
compares the typed term with `ILIKE '%term%'` on four columns
(`race_service.py:235-238`). It folds case only. So `Großglockner` never
matches "Grossglockner", `Valdaran` never matches "Val Daran", and a
country name typed into the box (`Malta`) matches nothing, because the
country column is only the dropdown's filter (`race_service.py:230`).

## Evidence

From the analyst's entry, 2026-10-13 → 11-01, terms that return 0 today
for a race the catalogue has:

| Why it missed | Terms | What the catalogue has |
|---|---|---|
| Diacritic / transliteration | `Großglockner`, `Fränkische`, `Kiev`, `Transilvania`, `Julien`, `Julien Alps`, `JulienAlps` | Grossglockner Ultra Trail, Lowa Ultratrail **Fraenkische**, **Kyiv** Marathon/Half, **Transylvania**, **Julian** Alps Trail |
| Spacing / punctuation | `Valdaran` (also `JulienAlps`) | **Val Daran** Pyrenees |
| Country typed into search | `Malta` | Gozo Trail Run, Valletta Marathon, both `event_country_code = 'malta'` |

Neither `unaccent` nor `pg_trgm` is installed, and installing one is a
scraper migration. This ticket stays in the web query.

## Acceptance

1. Both sides are folded before comparing: lowercase, ß→ss, ä/ö/ü match
   both `ae/oe/ue` and `a/o/u`, other accents stripped, spaces and
   hyphens removed. In the web query (`translate()`/`replace()`), no
   migration.
2. The search term is also matched against `event_country_code`.
3. Each of these returns the event in the right-hand column above:
   `Großglockner`, `Fränkische`, `Valdaran`, `Malta`. Paste the four
   results in the TODO.
4. `Kiev`, `Transilvania`, `Julien` still miss: they are spellings, not
   folds. Say so in the changelog, not as a fix.
5. A term that hit before still hits: spot-check `glockner`, `trail`,
   `berlin`.

## Out of scope

- Options C (a zero-result state with the Form prefilled), D (keeping
  searches past 30 days) and E (aliases): left raw in IDEAS for Paulo.
- `pg_trgm` / `unaccent` / a `search_text` column: the scraper's.
