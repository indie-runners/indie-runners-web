# W-033 — Nobody knows why migration rule 4 exists, and it now conflicts with the privacy page

`priority: 3` · `effort: S` · `area: docs` · `deploy: batched`
`source: Paulo, 2026-10-23, at the W-022 re-review ("I am not sure in what circumstances it came in")`

## What is wrong

`docs/ARCHITECTURE.md:468`, migration safety rule 4:

> **Take a manual backup snapshot** via the Cloud SQL console before
> running any destructive migration on production, even if automated
> backups exist.

Paulo does not remember why it was added. Since W-022, following it
breaks a promise. Privacy §8 says backup copies expire within 7 days,
and a manual Cloud SQL backup never expires (W-032).

**What the history shows.** All five rules came in together in
`4116ab3` (2026-06-17, "doing migration of event ids in attendance").
That commit also adds `migrations/002_attendance_event_id.sql`. Its step
2 backfills `event_id` with an `UPDATE ... FROM` join, and step 3 runs
`DELETE FROM web.attendance WHERE event_id IS NULL`. If the join
matched nothing, step 3 deletes every row. Rules 1, 2, 3 and 5 each
answer that exact shape: inspect before deleting, split backfill from
delete, check the join keys, stop on unmatched rows. The header says
"Migrations that delete rows have destroyed production data before".
So the likely reading is that 002 lost attendance rows, or nearly did,
and rule 4 is the restore path.

**What it does not show.** Whether rows were actually lost, whether a
manual snapshot was ever taken, and whether rule 4 was copied from the
scraper repo (a grep of its docs finds no such rule). No `ON_DEMAND`
backup exists today: `gcloud sql backups list`, 2026-10-23, shows 7
`AUTOMATED` backups only.

**What changed since June.** The instance now keeps 7 automated daily
backups and 7 days of point-in-time recovery
(`pointInTimeRecoveryEnabled: true`, `transactionLogRetentionDays: 7`).
If PITR was on in June, it already covers the restore rule 4 asks for,
without leaving a copy that outlives §8. Whether it was on then is part
of what this ticket settles.

## Acceptance

1. Rule 4 is kept, changed or deleted, and the reason is written next
   to it in one or two lines. That means what happened in June, if
   anyone can establish it, or that nobody can.
2. If it is kept, it says when the manual snapshot is deleted. W-032
   then only has the restore half left.
3. Rules 1–3 and 5 are left alone unless the same reading shows they
   are wrong. Say so if they are.

## Out of scope

- The restore procedure and §8's wording. Those are W-032.
- Rewriting the migration rules as a whole.

## Order

Before W-032: what rule 4 becomes decides half of W-032.

## Verdict

**VERDICT: APPROVED** — 2026-10-26. The ticket's premise ("nobody can
say why") was falsified, which is the best result this ticket could
have, and the changelog says so as its wrong belief. The instance's
operation list shows nothing. Cloud Audit Logs show the June restore
into a side instance. I re-ran that read myself, read-only, with no DB
connection: `create` + `restoreBackup` on `indie-runners-db-restore` at
2026-06-17T16:39Z, a second `restoreBackup` at 16:56Z, deletes at 17:42Z
and 17:44Z. PITR was turned on at 2026-07-27T08:50Z (`True` in the
request body). `4116ab3` is 17:29Z. All of it matches, apart from the
second restore call, which the changelog leaves out and which changes
nothing.

Rule 4 now points at PITR instead of a manual snapshot. That keeps
§8's 7-day promise true without touching the legal page, so it also
settles W-032's acceptance 1 (amended there). The new rule's restore
window is 7 days, where a manual snapshot's was unbounded. That is not
a gap: a longer window than 7 days is exactly what §8 forbids. Rules 1–3
and 5 are left alone, with a reason. Docs: 50 lines.

One phrase goes past the evidence: "a restore was needed that day". The
logs show a restore was *made*, not why. Nothing rests on it (rule 4's
reading holds either way, and the changelog says row loss is unknown),
so no action.

**Not verified:** whether migration 002 lost rows. That needs a DB
query the ticket did not ask for, and no rule depends on it. No routed
check: this is a docs change and predicts nothing in production.
