# W-100 — A search with no results offers the suggest form, prefilled with what was typed

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-11-02 (scraper analyst for Paulo), option C; Paulo picked it 2026-11-03`

## What is wrong

When a search matches nothing, the index shows "Showing 0 races" over
an empty grid (`index.html:60`, `:115-118`). The generic "Missing a
race?" banner sits further down and opens a blank form. Nothing tells
the visitor the race may simply be spelt differently, and nothing
records what they typed: the only trace is the request log, kept 30
days. 11 of 18 zero-result terms in the last 30 days were for races we
already have (W-099 catches most of those).

## Evidence

```
app/templates/index.html:60   <span class="filter-results">Showing {{ races | length }} ... races</span>
app/templates/index.html:115  {% for race in races %} ... {% endfor %}      (no else branch)
app/templates/index.html:126  <a href="https://forms.gle/TSE2djQbkFyPLfXe7" ...>Suggest a race</a>
```

Google Forms accepts a prefill URL (`...?usp=pp_url&entry.<id>=<text>`).
The `entry.<id>` comes from the form's "Get pre-filled link" menu.
**Paulo supplies it**; the developer does not guess it.

## Acceptance

1. A search (or search + filters) that returns zero races renders, in
   place of the empty grid, a short block: no race matched the term,
   a link to clear the search, and a "Suggest a race" button whose
   href is the Form's prefill URL with the typed term in the race-link
   field.
2. The term is URL-encoded; `Großglockner` and `Trans dimitile` both
   arrive intact in the form. Checked by opening the link.
3. Zero results with no search term (filters alone) shows the same
   block without the prefill, and the existing banner is unchanged.
4. Anon and signed-in render the same block.

## Out of scope

- Recording zero-result searches in `web.*` (option D's in-app variant).
  The Form response is the record.
- Changing what the search matches (W-099) or the banner copy (W-097).
- Keeping request logs longer (infra's inbox).
