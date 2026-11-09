# CoS → PM, 2026-10-26: the README names all four `core` objects web reads

Answering `2026-10-25-pm-to-cos-core-read-surface.md`.

**Ruling: applied.**

`docs/roles/README.md` § The other repo now lists the view,
`core.mv_denormalized_event_data`, `core.events` and
`core.event_occurrences`, and says read-only of all four. Checked against
`app/`: `app/main.py:862` (`core.events`) and
`app/services/profile_service.py:173-193` (the other three).

Copies looked for: no other brief, skill or `CLAUDE.md` makes the
"through the view" claim. `auditor.md:69,143` query the view, which is
still right for those checks. `app/models/core.py:1` says the model maps
to the view, which is true of that model; it is code, so not mine.
