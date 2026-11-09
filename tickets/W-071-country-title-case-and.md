# W-071 — `| title` writes "Bosnia And Herzegovina"

`priority: 5` · `effort: S` · `area: templates` · `deploy: batched`
`source: W-065 review 2026-10-28`

## What is wrong

The view's country is a lowercased name, and every page that shows it
title-cases it with Jinja's `| title`, which capitalises every word:

```
$ python3 -c "import jinja2; print(jinja2.Environment().from_string('{{ c | title }}').render(c='bosnia and herzegovina'))"
Bosnia And Herzegovina
$ curl -s https://indierunners.co/stats | grep -o "Bosnia[^<]*"
Bosnia And Herzegovina: 1
Bosnia And Herzegovina
```

Three render sites: the index dropdown (`index.html:49`), `/stats`
(`stats.html:45`), and since W-065 the event hero (`event.html`). The
PM's W-065 spec asked for the same filter, so it is consistent, not
right. One country in the view today (`sarajevo_marathon`).

## Acceptance

1. One way to display a country name, used by all three sites, that
   keeps "and" (and "of", "the") lower case unless it's the first word.
   "Bosnia and Herzegovina", "United Kingdom", "North Macedonia".
2. The `?country=` value and the filter's match are unchanged: only the
   displayed text changes.
3. `/stats`, `/` dropdown and `sarajevo_marathon`'s hero rendered,
   quoted in the changelog.

## Out of scope

- Raw codes like "Xk" (scraper T-147, routed check 18).
- Mapping names from codes on the web side.
