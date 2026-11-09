# TODO: W-102 — "← All events" on an event page drops the filters the user set

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-08_

## Steps
- [x] Carry the state by referrer, not query param (why: CHANGELOG 1.9.71)
- [x] `event_detail` builds `back_href`; `event.html` uses it
- [x] Verify both tiers: curl per Referer, Chrome click-through
- [x] CHANGELOG, ARCHITECTURE (referrer-policy paragraph), DEV_NOTES

## Measure
- Back-link href for: no referrer, filtered index, /profile, bare /, other host,
  `//host` path, an injected query. Done, results in CHANGELOG.

## Unsure / disproved
- Race switch on the event page drops to `/` (one hop). Left as a shortcut.
- The 302 from a finished year: not exercised.
