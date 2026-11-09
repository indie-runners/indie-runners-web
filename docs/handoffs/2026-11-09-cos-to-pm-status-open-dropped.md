# CoS → PM, 2026-11-09: you write `status` as `open` and `dropped`; the developer keeps `wip` `review` `done`

From Paulo, directly. No role was allowed to write `open`, and you
couldn't record `dropped`. 21 rows have a blank status today:
W-057, W-060, W-061, W-068, W-069, W-071, W-073, W-075, W-083, W-084,
W-085, W-088, W-089, W-093, W-097, W-099, W-100, W-104, W-105, W-106,
W-109. W-100 is among them, though its notes say it was dropped at
triage on 2026-11-05.

**Ruling: applied.** `status` is now split by value, so each value
still has one writer:

- **You:** `open` when you create a row, `dropped` when you drop one.
- **The developer:** `wip`, `review`, `done`, and `branch`.

Every copy changed in this commit: README roles table and § Single-writer
per column, `tickets/README.md` columns table, `pm.md` § Hard boundaries,
`/triage` § Boundaries, `developer.md` § Hard boundaries, `/dev-ticket`
§ Boundaries. The in-flight rule is unchanged: leave a row alone while
its ticket is in flight, which includes not dropping it.

**Your next pass:** fill in the 21 blanks, `open` or `dropped` (W-100
at least). If you find one that was really worked, say so on the row
rather than writing `done` yourself.

**Not applied: the status check.** Paulo suggested an optional CI step
or pre-commit hook that rejects values outside the five. That is code,
and this seat doesn't write code. If you think it's worth having, it's a
ticket for you to rank. There is no pre-commit hook today, only
`.github/workflows/ci.yml`.
