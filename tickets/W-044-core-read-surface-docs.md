# W-044 — The docs say web reads `core` only through the view; it reads four objects

`priority: 5` · `effort: S` · `area: docs` · `deploy: batched`
`source: W-027 review 2026-10-25`

## What is wrong

`docs/ARCHITECTURE.md` § The core read model, line 33:

> Everything this service reads from `core` comes through one mapped object:
> `Race` in `app/models/core.py`, pointed at `core.v_denormalized_event_data_upcoming`.

This was already false. `ProfileService._load_rows` reads `core.events` and
`core.event_occurrences` in raw SQL, and `app/main.py` reads `core.events`
for the stats headline (W-025). W-027 (1.9.24) added
`core.mv_denormalized_event_data` directly, for `race_location`,
`terrain_type`, `race_date`, `race_distance`, `occurrence_id`, `event_id` and
`mv_id`. The scraper believes the same false thing (its `docs/IDEAS.md`: the
view "is the frontend surface — `core.py` in `indie-runners-web` reads it and
nothing else"). That belief is why its MV rebuild replays grants onto the
view only. The upstream half was routed to the scraper's IDEAS at this
review.

Two sentences in the 1.9.24 changelog state a measurement as a property:

- "because the MV holds exactly one edition per event": true on 2026-10-25,
  not guaranteed by the MV definition. The SQL already handles two
  editions.
- "so profile and tile name the same town": they share a rule, not a
  result. The tile breaks ties by Postgres's row order (W-029); the profile
  breaks them by `mv_id`.

## Acceptance

1. ARCHITECTURE § The core read model names every `core` object this
   service reads, and the service that reads each one. Dated.
2. A changelog entry corrects the two 1.9.24 sentences above. Leave 1.9.24
   itself as written.
3. The § `ProfileService` bullet gets the full stop W-027 dropped ("the
   day after it runs **Location and terrain…").

## Out of scope

- Any code change, including moving the profile onto the view.
- `docs/roles/README.md` § The other repo has the same sentence. That file
  belongs to the chief of staff, so it goes there as a handoff, not in this
  diff.
- W-029's tie-break. When it lands, `mv_id` would make the tile agree with
  the profile; noted on W-029.
