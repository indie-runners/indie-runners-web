# W-088 — The event page says "Closed" for registration that hasn't opened yet

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-31 (Paulo), measured at triage 2026-11-01`

## What is wrong

The view says two things about a race's registration: `registration_open`
(a boolean) and `registration_start` (a date). The event page reads only
the boolean, so "registration opens in two days" and "registration is
over" render the same word. The date is already on the row. This is the
web collapsing two states, not wrong `core.*` data.

`event.html:159-161`, the race table's Registration column:

```
{% if r.registration_sold_out %}Sold out
{% elif r.registration_open %}Open
{% elif r.registration_open == false %}Closed
```

`event.html:205-214`, the Registration card: an `Opens` row printing the
raw ISO date (`2026-11-03`), then `Status: Closed` under it.

Paulo, 2026-10-31: *"it should actually say the actual date of the
registration, something like "opens on Nov 1st" instead of "coming up",
so long as the date exists."*

Read-only, `core.v_denormalized_event_data_upcoming`, 2026-11-01, rows
whose `occurrence_status` is not `tbc` (a TBC page renders neither spot):

```
dated race rows                                    1217
registration_open = false                           334
  registration_start > today                         49  (17 events)
    of which sold out (already render "Sold out")     8
    of which registration_start >= race_date          5
  registration_start <= today                       146
  registration_start is null                        139
```

Targets, not sold out: `eventyrsport_skytrail/2027` (4 races, opens
2026-11-03), `kackar/2027` (4, opens 2026-11-04), `kaiserkrone_trail/2027`
(6, opens 2026-11-23). The first two flip to open within days of this
triage, so check the query before verifying.

```sql
where occurrence_status is distinct from 'tbc' and registration_open = false
  and registration_start > current_date and not coalesce(registration_sold_out, false)
```

## Acceptance

Both spots, signed in. Precedence stays: "Sold out" first, then "Open".

1. `registration_open` false, `registration_start` after today, and
   before the race date (or no race date): reads `Opens 3 Nov 2026`.
   That is the site's single-date format, `format_date_range`'s.
2. `registration_start` today or earlier: reads `Closed`, as now.
3. No `registration_start`: reads `Closed`, as now. Nothing says the
   window is still to come.
4. `registration_start` on or after the race date: reads `Closed`. An
   opening after the race is bad data, and it is routed to the scraper.
   AMENDED 2026-11-04: scraper 0.89.0 (T-197) now stores these as null,
   so they reach branch 3 as each target is re-run (3 to 7 days). Keep
   the guard for rows not yet re-run. Re-run the targets query before
   verifying: the three named above have likely opened.
5. The card prints the opening date once, never as both an `Opens` row
   and a status. Elsewhere the `Opens` row prints the date in the same
   format, not ISO.
6. Anon: no change. Both spots sit inside the signed-in block
   (`event.html:108-487`), so anon has nothing to verify beyond the page
   still rendering.

## Out of scope

- The index tile badge. It only ever says "Registration open" (check 27).
- Rows marked open, or sold out, with a start still ahead (66 and 10).
  That is contradictory `core.*` data, routed to the scraper's IDEAS on
  2026-11-01. The web keeps trusting `registration_open`.
- A "not open yet" state for a closed race with no start date.
- Any other registration field (price, transferable, refundable).
