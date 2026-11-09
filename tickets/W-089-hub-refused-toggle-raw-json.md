# W-089 — A hub attendance click the lock refuses lands on a raw JSON body

`priority: 4` · `effort: S` · `area: services` · `deploy: batched`
`source: W-079 review 2026-11-01`

## What is wrong

W-079's hub control is a plain form POST to `/crews/{slug}/attendance`.
When `AttendanceService` refuses it, the route raises
`HTTPException(400)`, and with no exception handler in `app/main.py` the
browser navigates to FastAPI's default body:

```
{"detail":"This event has already taken place"}
```

The event page's identical 400 is read by `attendance.js`, so nobody
sees it there. On the hub it is the whole page, with no way back.

Two paths reach it:

1. **A row rendered before midnight, posted after.** W-079's changelog
   names it "the lock working". It is, but the render is the defect.
2. **A rendered row that is already locked.** `list_agenda` keeps a row
   whose `o.status = 'tbc'` by its expected month, but `is_locked` reads
   `start_date`/`end_date` whatever the status. A TBC occurrence carrying
   a past `start_date` therefore renders a control that always answers
   400. W-079 measured this at 0 attended rows on 2026-11-01. It is a
   data shape, not an invariant: `is_locked`'s docstring says "TBC has no
   dates", while `list_agenda`'s SQL allows `status = 'tbc'` with a
   non-null `start_date`.

ARCHITECTURE § Crews (1.9.54) says the agenda filter "is the hub's only
lock, so every rendered row carries the viewer's Going | Interested
segments". The second path is where that sentence is not true.

## Acceptance

1. A refused hub POST is a 303 back to the hub at the row's month,
   carrying a one-line notice. No JSON body.
2. A hub row whose occurrence `is_locked` shows no control, or the row is
   filed as past. The developer chooses, and the changelog says why.
3. ARCHITECTURE § Crews states what the hub actually guarantees.
4. Verified signed in: a locked occurrence posted from the hub, either
   real or forced with a form edit.

## Out of scope

- The event page's refusal, which `attendance.js` already handles.
- Whether a TBC occurrence should carry a past `start_date` at all. If
  that turns out to be wrong `core.*` data, it goes to the scraper's
  `docs/IDEAS.md`.
- W-085's bare 401s for anon.
