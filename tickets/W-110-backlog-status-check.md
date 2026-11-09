# W-110 — BACKLOG.csv accepts any status, including none

`priority: 5` · `effort: S` · `area: tooling` · `deploy: none`
`source: docs/handoffs/2026-11-09-cos-to-pm-status-open-dropped.md (Paulo)`

## What is wrong

Nothing checks the `status` column. A row can be written with no status,
or a typo, and nobody finds out until someone reads the whole board.

## Evidence

Before the 2026-11-09 triage, 21 rows had a blank status, from W-057
to W-109. W-069, W-089 and W-100 had
been dropped in their notes, with no status to say so. It was found by
eye during a read of the board, not by any check. The cause, which
nobody was allowed to write `open`, is fixed in the roles docs. This
ticket guards against a recurrence of the symptom.

`.github/workflows/ci.yml` runs on every pull request and push to
`master`, and has `build` and `migrations` jobs. There is no pre-commit
hook.

## Acceptance

1. A CI step (a new job or a step in `build`) fails when any row of
   `tickets/BACKLOG.csv` has a `status` outside `open`, `wip`, `review`,
   `done`, `dropped`. Read the file with a CSV parser, not by splitting
   on commas: titles and notes contain quoted commas.
2. The failure names the offending id(s) and the value it found.
3. Proven both ways: passes on `master`, and fails on a branch commit
   that blanks one status (revert that commit before handing over).
4. No new dependency. The runner's `python3` and its standard library
   are enough.

## Out of scope

- **A pre-commit hook.** It lives in each clone, nothing installs it,
  and it can be skipped. CI is shared and visible.
- **Checking other columns** (`branch` set when `wip`, `priority` range,
  `deploy` values). There's no evidence any of those drift. Add one if
  that changes.
- **Blocking the push.** A push to `master` goes through anyway; a red CI
  run is the signal. Making CI a required check is a repo setting
  (W-060's territory).
