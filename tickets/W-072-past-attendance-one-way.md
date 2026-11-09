# W-072 — Attendance on a past date can be written but never removed

`priority: 3` · `effort: S` · `area: services` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-28 (while on W-066)`

## What is wrong

Two routes, two rules. `mark_attendance` stores a row on any occurrence,
whatever its date. `clear_attendance` refuses to delete a row whose
`race_date` has passed, and says so only in a log line. So a row written
on a past date can't be undone from the UI, by anyone but an operator.

The UI offers that write. The index keeps a dated event for the day
after its race (`race_service.py:170` sets `yesterday`, and the predicate
keeps `race_date >= yesterday`) whenever the view still holds that row,
and every tile carries Going / Interested. A multi-day edition's event page is served while a later race
is still ahead, but `race_date` is the occurrence's `start_date`. Either
way a click writes `race_date < today`, and the guard then locks it.

The Remove that follows answers 200 and changes nothing. The response
carries `user_status` unchanged, so the button re-renders as it was. The
user is told nothing.

## Evidence

`app/services/attendance_service.py`, mark (no date predicate):

```
            race_date = self._occurrence_date(occurrence_id)
            if race_date is None:
                logger.info("No upcoming occurrence found for event %s, storing null race date", event_id)
```

and clear:

```
        if existing.race_date is not None and existing.race_date < date.today():
            logger.info("Skipping delete for user %s occurrence %s, event date %s has passed", user_id, occurrence_id, existing.race_date)
            return
```

`main.py:340-341`: the DELETE route calls `clear_attendance`, then returns
`_attendance_response` with status 200 either way.

CHANGELOG 1.9.45, verifying W-066:

```
  - **A first attempt wrote three rows on past occurrences** (the app accepts attendance on a
    past date and refuses to clear it); they were deleted by hand within minutes.
```

Not measured (no proxy at triage, one DB session at a time): how often
the window is reached. That is acceptance 0.

## Acceptance

0. **Before the fix, quoted here:** distinct `occurrence_id` in
   `core.v_denormalized_event_data_upcoming` with
   `occurrence_start_date < current_date`, and the count of
   `web.attendance` rows with `race_date < created_at::date` (counts only).
1. **One predicate, in the service:** an occurrence is locked when its
   `start_date` is before today. Mark and clear both read it. A POST on a
   locked occurrence answers 4xx and writes nothing. A DELETE on a locked
   row answers 4xx, not a 200 that changed nothing. `attendance.js`
   already flashes an error on a non-2xx (`if (!r.ok) { flashError(btn) }`).
2. **No control the server refuses.** Signed in, on a locked occurrence,
   neither the tile nor the event page offers Going, Interested or Remove.
   A user's existing status still shows. The template reads the flag from
   the service; it doesn't compare dates itself.
3. TBC (NULL `start_date`) is not locked, as today.
4. Verified signed in by curl against the dev server: POST and DELETE on
   one locked occurrence, both refused, and the row count unchanged.
   Plus one unlocked mark and clear. Anon unchanged.

**The direction is a default, not Paulo's ruling yet.** This ticket makes
marking match the delete guard. If Paulo would rather a past "going" be
retractable, acceptance 1 flips to "clear allows it" and 2 keeps Remove.
Ask before starting if the ticket still says this.

## Out of scope

- **Retroactive "been there" marking.** Adding a race you ran is a
  feature, not this fix.
- **W-012 (retain finished events).** It will serve pages for past
  editions. It inherits acceptance 1's predicate, which is why the
  predicate lives in the service, not the template.
- **Rows already locked.** Acceptance 0 counts them. Deleting any is
  Paulo's call, by hand.
- The 1-day window's timezone (`date.today()` is UTC on Cloud Run).

## Amended by Paulo's ruling (2026-10-30, recorded in TODO and CHANGELOG 1.9.49)

Acceptance 1's predicate is **the last known day**, not `start_date`: an
occurrence locks the day after `coalesce(end_date, start_date)`. A Fri–Sun
festival is markable through Sunday. The `race_date` snapshot stays
`start_date`. Everything else in the acceptance holds as written.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-084** — 2026-10-31. One predicate
(`is_locked`) in the service, read by both routes and both templates; the
tile and the event page take their dates from the MV, which projects
`core.event_occurrences.start_date` / `end_date` unchanged (scraper
migration 073, `nuo.start_date::text AS occurrence_start_date`), so the
routes and the templates read the same dates. The TBC rule holds: the
scraper computes `start_date` and `end_date` together from the race-date
answers, and the MV states TBC as `occurrence_start_date = NULL`.
"30 and 30" does mean the same 30 rows, because `end_date >= start_date`
makes the new set a subset of the old one. Verified on :8000 from the
worktree (`/proc/<pid>/cwd` checked): event page signed in (locked, and
past start / future end) and anon, and every route by curl. Docs 71/100.
`deploy: batched`. W-084 is the profile's start-date split, which now
disagrees with a lock on `end_date`.

**Not verified:** the locked tile on a live index page. No locked
occurrence had a tile on 2026-10-30, so the four tile states were rendered
by Jinja directly. It would show on `/` the day after a single-day race the
view still holds, signed in with a mark. Also not verified: the 400 flash
in `attendance.js` from a stale page in a real browser (curl only), and
the UTC lock day (out of scope, as specced). Occurrence 6541 (Athens) locks
while a race dated after its `end_date` is still ahead. The developer
noted this and it is with the scraper (their IDEAS 2026-10-28).
