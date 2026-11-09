# W-084 — The profile files a running multi-day edition as past

`priority: 4` · `effort: S` · `area: services` · `deploy: batched`
`source: W-072 review 2026-10-31 (DEV_NOTES 2026-10-30, while on W-072)`

## What is wrong

W-072 locks attendance the day after an occurrence's **last** known day
(`coalesce(end_date, start_date)`). `ProfileService.is_upcoming` splits on
`web.attendance.race_date`, the **start_date** snapshot. So between an
edition's first and last day, the two disagree. The site still offers
Change/Remove, but the profile has already filed the row as past:

- **going** becomes a "been there" row while the event is still running;
- **interested** disappears from the profile altogether, because the
  `interested` shelf keeps only upcoming rows (`profile_service.py:101`).
  If you mark Interested during the tail, your profile never shows it.

## Evidence

`app/services/profile_service.py:94-101`:

```
        def is_upcoming(row: ProfileRow) -> bool:
            ...
            return row.race_date is None or row.race_date >= today
        ...
        interested = [r for r in rows if r.status == "interested" and is_upcoming(r)]
```

DEV_NOTES 2026-10-30: Tirana 46991 (2026-10-25 → 11-15) is in that window
today. It was the only one on 2026-10-30.

## Acceptance

1. The profile's past/upcoming split reads the same last-known-day rule as
   `is_locked`: "past" means exactly "locked". Read the live dates, not the
   snapshot, the way `is_locked` does. NULL (TBC) stays upcoming.
2. Signed in, on a profile with a mark on an occurrence whose start has
   passed and whose end has not, the row is listed as upcoming (going or
   interested), not as been-there or missing. Anon/other-viewer render
   unchanged apart from that row.

## Out of scope

- Changing the `race_date` snapshot itself (W-072 kept it on purpose).
- The timezone of "today".

AMENDED 2026-11-04 at the W-098 review. Since 1.9.67 the profile looks
like the crew hub, so a snapshot date shows up next to the hub's live
one. The profile reads `COALESCE(a.race_date, o.start_date)`: a NULL
snapshot takes the live date, a dated one is read as taken. The hub
reads `o.start_date`, and treats `o.status = 'tbc'` as TBC even with a
date (`crew_service.py`). So the same occurrence can sit under two
different months on the two pages when an edition is rescheduled after
someone marked it, or when a `tbc` edition carries a start date. Nobody
measured either.

3. Step 1, one read-only query: count attendance rows whose dated
   snapshot differs from `o.start_date`, and `tbc` occurrences with a
   start date. Paste both counts.
4. The row's date and month heading read the live dates, as the split in
   acceptance 1 does. The snapshot stays the fallback for an occurrence
   `core.*` no longer has. Profile and hub then agree on every row.
5. A TBC row whose expected month has passed stays on the profile as
   upcoming, as acceptance 1 says. The hub drops it. That difference is
   kept on purpose: a profile is one runner's record, the hub a plan.
