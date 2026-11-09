# W-037 — The index silently stops at 60 events, and `/stats` now shows the numbers it hides

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-23 (while on W-026), filed at the W-026 review`

## What is wrong

`app/main.py:241` (master), at the end of `index()`:

> `races = races[:60]`

and `app/templates/index.html:60`:

> `Showing {{ races | length }} races`

The count is taken after the cut, so a filter that matches more than 60
events says "Showing 60 races" with no sign that more exist. The cap is
older than W-026. W-026 makes it visible: `/stats` lists Germany at 102
upcoming events and links to `/?country=germany`, which shows 60. The
developer curled all 42 country links: 41 match the listed count and
Germany does not (1.9.18 changelog).

## Acceptance

1. When a filter matches more than the cap, the index says so: either
   the true count beside the shown one, or a way to see the rest. The
   developer names which, and why.
2. `/?country=germany` and the unfiltered `/` checked anon and signed
   in, quoted.
3. Below the cap, nothing changes.

## Out of scope

- Changing the `/stats` counts. They are correct. The index is what
  undercounts.
- Changing the engagement-first sort (W-029 covers tie order).

## Verdict

**VERDICT: APPROVED** — 2026-10-26. The count is taken before the cut
(`main.py` `total_races`), and the template adds "of N" only when N is
over what is shown. At 60 or fewer nothing changes, exactly 60 included.
`index()` is the only route that renders `index.html`, so no other
caller is left with an undefined `total_races`. The changelog names the
wrong belief, the cost (Germany 60 of 98 with no sign of more), and why
it shows the count rather than paging (the sort runs in Python over
every match). Verified with `dev.sh` from the worktree (`/proc/<pid>/cwd`),
anon and with a minted cookie: `/` 60 of 381, Germany 60 of 98, France 23,
Spain 24. Master's code on the same server still said "Showing 60 races".
`static/js/script.js`, which writes its own "Showing x of y", is loaded
only by `mockup_reference.html`, so it does not touch this. Docs: 39 lines.
`deploy: batched`.

**Not verified:** a filter matching exactly 60 events, and the zero-match
render. Both read correctly but nobody rendered them. Phone width was not
checked in a browser. The line is 6 characters longer, `white-space:
nowrap`, and no CSS changed, so this is accepted. I did not re-run it
myself because that needs a DB session. The production check is routed
check 20.
