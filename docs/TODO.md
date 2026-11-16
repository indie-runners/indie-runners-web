# TODO: #16 — /stats: "checked" is unclear, country list reads as a ranking

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-16_

## Steps

- [x] stats.html: Paulo's copy for "tracked" and "checked", slips fixed
- [x] Countries: `<ul>`, sorted by displayed (title-cased) name in `stats()`
- [x] Verify anon at desktop and 375px; map and links unchanged
- [x] Changelog, version bump

## Measure

- Order of the list equals sorted(name.title()); counts and hrefs as before
- Map `<svg>` markup identical before/after

## Unsure

- Whether `columns: 2 12rem` already gives one column at 375px (expected: yes)
