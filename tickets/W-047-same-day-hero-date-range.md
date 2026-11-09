# W-047 — A one-day edition's hero shows "29 May – 29 May"

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-24 (Paulo)`

## What is wrong

Paulo, from `docs/IDEAS.md`:

> Sometimes, all the races are on the same day, and the web displays dates
> as 29 May – 29 May. In the case where all races are on the same day, only
> one date should be displayed, not a range.

The range is the event page hero. `app/main.py:403-404` formats both
ends through `_fmt_date` (`%-d %B`, no year), and
`app/templates/event.html:55-56` prints both whenever both are present,
without comparing them:

```jinja
{% if event.occurrence_start_date and event.occurrence_end_date %}
  {{ event.occurrence_start_date }} – {{ event.occurrence_end_date }}
```

The index tiles are already right: they go through
`format_date_range` (`app/services/race_service.py:62-66`), which returns
one date when `end == start`. So this is one render site.

## Acceptance

1. An event whose occurrence starts and ends on the same day shows one
   date in the hero, in today's format (`29 May`, no year).
2. A multi-day occurrence still shows `<start> – <end>` exactly as
   today.
3. A TBC event still shows its `tbc_display`, and an occurrence with only
   one end set still shows that one date.
4. Checked in the browser on one single-day and one multi-day event,
   signed out and signed in. Name both slugs in the changelog.

## Out of scope

- Changing the hero's date format (adding the year, or switching to
  `format_date_range`'s `%b` style). That is a design change, not this
  defect.
- Index tiles and profile rows. They do not have the defect.
- Whether `occurrence_start_date` / `occurrence_end_date` are right
  upstream. If a multi-day event shows one date, that is `core.*` and
  routes to the scraper.

## Verdict

**VERDICT: APPROVED** — 2026-10-26. One expression in `main.py:405-406`.
The end date is dropped when its raw string equals the start, so the
template's existing start-only branch prints one date. The changelog
names the wrong belief, the cost (153 of 234 dated occurrences) and the
evidence. Comparing raw strings is safe in both directions: equal
strings are the same day, and an unequal pair for the same day only
falls back to today's range. `event.html` is the only reader of the key,
and its values are already display strings with no year, so no future
caller can use them as data. The developer verified with `dev.sh` from
the worktree (`/proc/<pid>/cwd` → `irw-W047`), anon and signed in (minted
cookie), on `transylvania_100/2027` (one date), `night_marathon_luxemburg/2027`
(range kept) and `half_marathon_berlin/2027` (TBC). Docs: 28 lines.
`deploy: batched`.

**Not verified:** the end-only branch (`event.html:59-60`). No row has
only an end date, and its code is unchanged. Verified with curl, not in a
browser. For a text-only change with no CSS touched, the server's HTML is
the render, so this is accepted. I did not re-run it myself because it
needs a DB session. The production check is routed check 19.
