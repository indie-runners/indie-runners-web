# W-048 — Nothing notices when the view drifts from `core.py`

`priority: 4` · `effort: S` · `area: tooling` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-25 (Paulo, at W-014)`

## What is wrong

Paulo, from `docs/IDEAS.md`:

> W-014 is a one-off audit, true on the day it ran. The scraper owns the
> view and keeps changing it (a 55th column on 2026-09-09; this repo
> found out only because a ticket needed it). Proposal: a small script
> that runs W-014's `information_schema` query, compares it to
> `Race.__table__.columns`, and exits non-zero on a missing column, a changed
> type or an unmapped one. It needs no test suite, so it doesn't wait on W-003. It could
> run from `deploy.sh`, or whenever the scraper changelog mentions the view.

The baseline, from the W-014 verdict:

> One `information_schema.columns` query found that 54 of 55 mapped types
> match. `occurrence_id` (`text` in the view, declared `Integer`) is now
> `Text` / `Mapped[str | None]`.

The cost of drift is known here: W-007's `mv_id` mismatch was a latent
500 on an event page, and its quieter half (a `uuid.UUID` under a `str`
annotation) went unseen for 18 days.

## Acceptance

1. A script under `scripts/` reads `information_schema.columns` for
   `core.v_denormalized_event_data_upcoming` in one read-only session,
   compares it with `Race.__table__.columns`, and prints each difference
   by name: a mapped column the view no longer has, a type that no
   longer matches, and a view column with no mapping.
2. Exit status is non-zero on the first two. An unmapped view column is
   printed but exits zero: the ORM selects only mapped columns, so it
   breaks nothing (the W-014 changelog says so).
3. Run against production today, it exits zero, because W-014 left
   nothing to report. Paste that output in the changelog.
4. Shown failing once: edit one `mapped_column` type locally, run it,
   paste the non-zero output, revert. That is the script's self-check.
5. `docs/FILE_TREE.md` lists it, and one line says when to run it: after
   a scraper changelog entry that touches the view.

AMENDED 2026-11-04 (triage), on Paulo's call of 2026-11-03 (DEV_NOTES):

6. The script reads its database URL from the environment, so the same
   script runs against production by hand and against CI's database.
7. One step in `.github/workflows/ci.yml`'s `migrations` job runs it
   after the MV refresh. That job already builds `core.*` from the
   scraper's `baseline.sql` at a pinned ref (`aad6a87`, scraper 0.80.4),
   so a pin bump to a release that changed the view fails CI until
   `core.py` follows. Paste the step's green run.
8. Owner of the by-hand production run: the developer, when the PM
   tickets it for a scraper entry that touches the view, and in every
   ticket that bumps the CI pin. CI cannot see drift between the pin and
   production; the by-hand run is for that.

## Out of scope

- Running it from `deploy.sh`. A deploy opens no DB connection today.
  Adding one makes every deploy a DB-touching session under the
  one-session rule. CI cannot reach the production database, and should
  not; it runs against its own throwaway one (acceptance 7).
- Bumping the CI pin. That is its own ticket, and it runs the by-hand
  check (acceptance 8).
- The other three `core.*` objects this repo reads (W-044), and
  `app/models/web.py`.
- Nullability. W-014 recorded it, but a nullable change cannot 500 a
  page the way a type can.
