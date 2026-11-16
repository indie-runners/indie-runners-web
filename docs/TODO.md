# TODO: #17 — event page says "Closed" for registration that hasn't opened yet

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-16_

## Steps

- [x] `registration_opens(r)` in race_service, a template global
- [x] Race table: Sold out, Open, Opens <date>, Closed
- [x] Card: status reads Opens <date> and the Opens row drops; else Opens row in site format
- [x] Verify signed in (one upcoming, one past start, one null start) and anon
- [x] Changelog, version bump

## Measure

- Re-run the spec's targets query (read-only) for rows to verify against

## Unsure

- "Today" is the server's date (UTC on Cloud Run), as elsewhere in the app

## What the work showed

- The spec's three targets had opened; penyagolosa_trails and kaiserkrone_trail stood in
