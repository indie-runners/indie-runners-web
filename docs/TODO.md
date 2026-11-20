# TODO: #62 — the event page shows the official website link to signed-out visitors

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-20_

## Steps

- [x] Gate the action-bar link behind `current_user` in `event.html`
- [x] Verify: anon page source of an event with a website has neither link nor URL; signed-in renders as before
- [x] ARCHITECTURE event-page paragraph, CHANGELOG 1.9.87

## Measure

- `grep -c` of the URL in anon vs signed-in source, one event with a website

## Unsure

- Whether the URL appears anywhere else in the anon source (ticket says no; the grep checks it)

## What the work showed

- The ticket's premise held: anon source had the URL once, from this link only
