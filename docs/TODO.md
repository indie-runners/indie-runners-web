# TODO: #17 — event page says "Closed" for registration that hasn't opened yet

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-16_

## Steps

- [ ] `registration_opens(r)` in race_service, a template global
- [ ] Race table: Sold out, Open, Opens <date>, Closed
- [ ] Card: status reads Opens <date> and the Opens row drops; else Opens row in site format
- [ ] Verify signed in (one upcoming, one past start, one null start) and anon
- [ ] Changelog, version bump

## Measure

- Re-run the spec's targets query (read-only) for rows to verify against

## Unsure

- "Today" is the server's date (UTC on Cloud Run), as elsewhere in the app
