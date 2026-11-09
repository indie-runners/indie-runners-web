# W-054 — CI applies every web migration on top of the scraper's baseline

`priority: 2` · `effort: M` · `area: infra` · `deploy: none`
`source: claude/CICD_TERRAFORM_PLAN.md step 3 (Paulo, 2026-10-25)` —
sequence 7 (web) of that plan. It depends on scraper sequence 6, which is
T-158, done 2026-10-26 (scraper 0.80.4). CI/CD is the highest priority on
the board after emergencies (Paulo, 2026-10-27): **take this next.**

## What is wrong

Nothing states which `core.*` schema this app's migrations expect. The
dependency only shows up when a migration fails against live.

**Correction to the paste's count:** six of the twelve files *mention*
`core.*`, but only three *query* it. 001, 007 and 010 mention it in
comments only.

```
002_attendance_event_id.sql:13:    FROM core.mv_denormalized_event_data
005_attendance_race_date.sql:21:    FROM core.mv_denormalized_event_data
005_attendance_race_date.sql:32:    FROM core.mv_denormalized_event_data
006_attendance_occurrence_id.sql:16:FROM core.event_occurrences o
```

The scraper now publishes what this check needs. Its
`database/baseline.sql` is a schema-only dump of live that excludes
`web.*`, and its header names the newest migration the dump contains:

```
-- baseline: 079
...
--   pg_dump --schema-only --no-owner --no-privileges --exclude-schema=web
```

Its newest migration at `aad6a87` is
`079_answer_moved_ignores_only_known_model_switches.sql`, so at that ref
the baseline is the whole of `core.*`. If a later pin's header lags its
migrations, `core.*` at that ref is the baseline plus the migrations
above it. The scraper's own `scripts/ci_apply_migrations.py` applies
those.

### Three facts the paste does not account for

1. **The materialized view is empty, and 002 and 005 read it.** The
   header says "the materialized views are WITH NO DATA", and
   baseline.sql:1714 is `WITH NO DATA;`. Postgres refuses a SELECT from a
   materialized view that has never been refreshed. As pasted, the job
   is red on master. Between the baseline and the migrations, run
   `REFRESH MATERIALIZED VIEW core.mv_denormalized_event_data`. The
   tables under it are empty, so the refresh is instant and leaves the
   view empty but readable.
2. **postgres:15, not 16.** The scraper's migrations job pins
   `postgres:15`, and its comment says `gcloud sql instances describe`
   reads `POSTGRES_15`. The baseline was "Taken ... from PostgreSQL
   15.17". Use the same major version as live.
3. **Both repos are private.** `gh repo view` gives `PRIVATE` for
   `indie-runners/indie-runners-web` and for
   `indie-runners/indie-runners-scraper`. This workflow's default
   `GITHUB_TOKEN` cannot check out the other repo, so the job needs one
   secret. W-045's rule was "no `secrets.*`". For this job it becomes:
   **no GCP, no write, one read-only secret.**

## Acceptance

1. A `migrations` job in `.github/workflows/ci.yml`, on the same
   triggers as the build. It has a `postgres:15` service container. It
   checks out `indie-runners/indie-runners-scraper` at a commit SHA
   pinned in the workflow and loads its `database/baseline.sql`. It
   refreshes `core.mv_denormalized_event_data`, then applies every file
   in `migrations/` in filename order with `ON_ERROR_STOP`, and fails on
   the first error. The gap at 004 is expected: run what is on disk.
2. The pin is a full SHA, with a comment naming the scraper version
   (`aad6a87…` is 0.80.4), and the comment says the baseline header
   matched that ref's newest migration. Write the bump rule in one line
   next to it: bump by hand when `core.*` changes in a way this app
   reads, and the bump ticket quotes the scraper changelog entry.
3. The checkout uses a read-only token scoped to the scraper repo alone,
   for example a fine-grained PAT with Contents: read. **Step for Paulo:**
   create it and add it as a repo secret. The developer names the secret
   and says in the changelog how it expires. An expired token shows up
   as a red run, which must not be mistaken for a schema mismatch.
4. Green on master. Link the run in the changelog entry.
5. **Red, shown.** Moving the pin back cannot show this, because
   `baseline.sql` first appeared at T-158 (2026-10-26). No earlier
   scraper ref has the file, so the job would fail on the missing file,
   not on the schema. Instead, push a throwaway commit to the ticket
   branch, for example a `migrations/999_probe.sql` that selects a column
   `core.event_occurrences` does not have. Link the red run, quote the
   error in this ticket, and revert the commit before review.
   *Done 2026-10-27:* [red run](https://github.com/indie-runners/indie-runners-web/actions/runs/40482555500), `psql:migrations/999_probe.sql:1: ERROR:  column "occurrence_does_not_exist" does not exist`; reverted in 3f8222d.
6. If a migration that has already been applied fails against today's
   baseline, **do not edit it.** An applied migration is a record of
   what ran. Stop, and say which migration and what error in
   `docs/TODO.md`. The PM amends this ticket.
7. Changelog entry with the reasoning. FILE_TREE if a file is added.

## Out of scope

- **Running any migration against live.** The standing rule holds. CI
  only proves that a file applies to a copy.
- **Automating the bump.** The pin is moved by hand, on purpose: a bump
  is a claim that this app still reads `core.*` correctly.
- **Checking what a migration does to data.** The tables are empty, so
  the backfills in 002, 005 and 006 touch zero rows. The check proves
  the names and types resolve, not that the backfill is right.
- **Whether the ORM matches the view** (W-048), and **a test suite**
  (W-003).

## Verdict

**VERDICT: BLOCKED — R1, R2** — 2026-10-27. Reviewed `git diff master...fix/migration-check-in-ci`
(`bdf6ba0`..`08d35a7`). The job itself is right, and I checked these against the source:

- Pin `aad6a87e…` is scraper 0.80.4. At that ref `baseline.sql` reads `-- baseline: 079`, 079
  is the newest migration, and scraper `origin/main` has no `database/` change since. The pin is
  current today.
- The three runs are what the changelog says. The green run `40482447999` (`bdf6ba0`) has both
  jobs green and logs all 12 files, 001 to 013. The red run `40482555500` (`2a2f2bd`) stops at
  `999_probe.sql` with the quoted error and exit 3. The run after the revert (`3f8222d`) is green.
  `ci.yml` has not changed since `bdf6ba0`. Secret `SCRAPER_READ_TOKEN` exists.
- The changelog gives the wrong belief, the cost, the new belief and the evidence, and says what
  an expired-token red looks like. One ticket. Docs: 37 lines, with 1.9.36, ARCHITECTURE and
  FILE_TREE updated. Check 5 (render) is N/A: no app code changed, and `.dockerignore` keeps
  `migrations/` out of the image.

**R1 — the changelog says draft PR #2 "is closed unmerged". It is open** (`gh pr view 2`:
`OPEN`, draft). It is also an ordering trap. Once master is pushed with these commits, GitHub
marks an open PR as *merged*, and the sentence stays false in the record. Unblock: close PR #2
before merging. The docs need no change.

**R2 — ARCHITECTURE migration rule 7 overstates what green means for the next author.** "Applies
every migration to a copy of `core.*` before you do" and "green means names and types resolve"
are true only (a) against `core.*` *at the pin*, which nothing re-bumps when the scraper moves,
and (b) if the migration reaches a PR before anyone applies it to live: branch pushes run no CI
(TODO says so). The author of 014 inherits this sentence, and for them it fails in exactly the
case this ticket exists for. Unblock: one clause each, e.g. "resolve against `core.*` at the
pinned scraper ref" and "only once the file is in a PR".

**Not verified:**
- **The `push` to master path.** Every run so far is a `pull_request` event, so acceptance 4
  (green on master, linked) can only be met after the merge. Secrets are available on push, so
  it should behave the same, but nothing has run it.
- **The expired-token red.** "Fails before any SQL runs" follows from the step order. No run
  showed it. The expiry date (2027-10-27) is as Paulo stated it. `gh secret list` cannot show it.
- **A future migration with a `GRANT` to a live role.** The baseline is `--no-privileges` and
  has no app roles, so it would be red in CI and fine on live. None of the 12 has one today.

No ROUTED_CHECKS entry: `deploy: none`, nothing in production changes.

VERDICT: BLOCKED — R1, R2

### Re-review — 2026-10-27, `f347d7b`

- **R1 resolved.** PR #2 is `CLOSED` and `mergedAt` is null (`gh pr view 2`). The changelog's
  "closed unmerged" is now true, and pushing master can no longer flip it to merged.
- **R2 resolved.** Rule 7 now says CI runs only once the file is in a PR or on `master`, and
  that green means resolve "against `core.*` at the pinned scraper ref, which is bumped by hand
  and can lag live". Both clauses are what the next migration author needs.
- `ci.yml` is unchanged since the green run. The fix is a docs-only diff. The docs total stays
  at 37 lines.

**Not verified:** unchanged from above. The `push` to master run is the developer's to link at
merge (acceptance 4).

VERDICT: APPROVED
