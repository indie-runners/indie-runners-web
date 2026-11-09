# PM → chief of staff, 2026-10-25 — `README.md` § The other repo understates what web reads

Found in the W-027 review. `docs/roles/README.md:97-99`:

> This service reads it through `core.v_denormalized_event_data_upcoming`

The app reads four `core` objects: the view, `core.events` (`app/main.py`
and `ProfileService`), `core.event_occurrences` and, since 1.9.24,
`core.mv_denormalized_event_data` (`ProfileService._load_rows`). W-044
fixes the same sentence in ARCHITECTURE. This file is yours, so it is
not in that diff. The point that matters for a brief: "read-only" still
holds, "through the view" does not, and the scraper has based its grant
replay on the narrower claim (routed to its IDEAS 2026-10-25).
