# W-061 — A tile's date span is the span of the races the filters let through

`priority: 4` · `effort: S` · `area: services` · `deploy: batched`
`source: W-023 review, 2026-10-27`

## What is wrong

`list_races` filters **races**, then groups them into events
(`race_service.py`, the `WHERE` before the grouping loop). The tile's
`race_date` / `race_date_end` are the first and last of the rows that
survived. So any filter that keeps only some of an event's races shrinks
the span:

- `date_from` / `date_to`: `filter_key` is the race's own date.
- `search`: matches `race_location`, which differs per race.

The tile renders that span (`format_date_range`), and since W-023 the
calendar popup builds its `dates=` from it too. That is the trap W-023's
ticket named: a plausible link one day short.

## Evidence

From the W-023 branch (`race_service.py`, grouping loop):

```python
"race_date": r.race_date,
"race_date_end": r.race_date,
...
if r.race_date is not None:
    cur_end = events[eid]["race_date_end"]
    if cur_end is None or r.race_date > cur_end:
        events[eid]["race_date_end"] = r.race_date
```

`athens_authentic_marathon` 2026 has races on Nov 7 and Nov 8 (W-023's
DEV_NOTES entry). On `/?date_to=2026-11-07` only the Nov 7 race survives,
so the tile reads one day, and marking going offers `20261107/20261108`.
Derived from the code; not rendered.

## Acceptance

1. A dated tile's displayed span and its calendar URL cover every dated
   race of the occurrence that the past-race cut keeps, whatever
   `date_from`, `date_to` or `search` say. Check Athens with
   `date_to=2026-11-07` and with a `search` that matches one race's town.
2. Which **events** a filter shows is unchanged: same tile set as master
   for the same query string. Check two filtered queries.
3. Anon and signed-in both render.
4. Changelog entry.

## Out of scope

- The past-race cut (`race_date >= yesterday`) narrowing an in-progress
  event. That is W-012's grain defect, and fixing it here would be doing
  W-012 halfway.
- `country`: it's event-level, so it can't split an event.
- Other per-race fields picked on first-see (location, W-055).
