# W-032 — A manual backup keeps a deleted user longer than the 7 days the privacy page promises

`priority: 3` · `effort: S` · `area: docs` · `deploy: batched`
`source: W-022 re-review, 2026-10-23`

## What is wrong

W-022's privacy §8 now says:

> Copies remain in automated database backups for up to 7 days, after
> which they expire and are not restored.

That is true today. `gcloud sql backups list --instance indie-runners-db`
(2026-10-23) shows 7 `AUTOMATED` backups and no others. Retention is
`retainedBackups: 7`, `retentionUnit: COUNT`, and
`transactionLogRetentionDays: 7`.

But `docs/ARCHITECTURE.md:468`, migration safety rule 4, tells the
operator to make one that does not expire:

> **Take a manual backup snapshot** via the Cloud SQL console before
> running any destructive migration on production, even if automated
> backups exist.

Cloud SQL keeps an on-demand backup until someone deletes it, so it
falls outside the retention count. The first time rule 4 is followed,
every user deleted before that snapshot survives in it past 7 days, and
§8 is false with nobody having touched the template.

There is a second gap in the same sentence. A restore inside the 7 days,
whether from a backup or point-in-time, brings back every account
deleted since that point. Nothing in the docs says to re-apply those
deletions.

## Acceptance

1. Rule 4 says when a manual snapshot is deleted, at most 7 days after
   it was taken. Or §8 names manual snapshots and how long they are
   kept. **Which one is Paulo's call**: §8 is a legal page in his voice.
2. The migration or restore procedure says that a restore re-deletes
   any account deleted after the restore point, and how to find them.
3. `gcloud sql backups list` is quoted with the result at the time of
   the fix.

## Out of scope

- Logging deletions so they can be re-applied. If acceptance 2 needs
  that, it is its own ticket and probably needs DDL.
- §6's silence on backups, which is older than W-022.

## Amended 2026-10-26, at the W-033 review

**Acceptance 1 is met by W-033 once it merges.** Rule 4 no longer takes
a manual snapshot. It confirms PITR is on and notes the start time as the
restore point, so §8 stays true with no change to its wording, and the
choice between the two options above is no longer needed. What is left
is acceptance 2 and 3.

For acceptance 2: a PITR restore, like the June one, is a clone into a
new instance. The re-delete applies to the clone for as long as it
exists, and to anything copied back from it. `gcloud sql operations list
--instance indie-runners-db` does not show restores into other
instances; Cloud Audit Logs do (`restoreBackup`, `clone`). The source is
the W-033 developer's `DEV_NOTES.md` entry of 2026-10-26.


## Verdict

**VERDICT: BLOCKED — R1, R2** — 2026-10-26.

Most of this holds. The id comparison is sound: `web.users.id` is
`BIGSERIAL`, so an id on the clone and not in production was deleted
after the restore point. Re-deleting with `delete_account` instead of a
raw `DELETE` is the right call. It is DB-only (`user_service.py:81-125`,
no GCS or OAuth side effects), so pointing it at a clone touches nothing
shared. The logging finding is verified: nothing in `app/` configures
logging, the Dockerfile runs plain `uvicorn`, and so the root logger stays
at WARNING and `delete_account`'s INFO line is dropped. The *Limit*
paragraph is honest about where the method stops working. Acceptance 3
is quoted verbatim. Docs: 60 lines.

Both blocks are rule 6 saying something universally that is true only
of the path the developer looked at. Rule 6 is a procedure someone will
follow under pressure, during a restore, so its claims have to hold for
every case that reaches it.

**R1 — "one `303` per deletion" leaves out deletion by email.** Terms
§9 and privacy §8 still offer deletion by email to
`paulo@indierunners.co`. That deletion leaves no `303`. So the cross-check
undercounts in the normal case, and in the *Limit* case ("the 303 count
is all you have") an email-deleted account is missed entirely. The same
assumption sits in the changelog's "before account deletion existed":
deletion by email existed before W-022, and what didn't exist was the
self-serve route and §8's 7-day promise. **Unblocks:** rule 6 says the
`303` count covers self-serve deletions only, and that deletions done by
hand on an email request are counted from the mailbox. Correct the
changelog phrase to match.

**R2 — "A PITR or backup restore goes into a new instance" is not
always true.** PITR always clones. A backup restore can target the
existing instance (`gcloud sql backups restore <id>
--restore-instance=indie-runners-db`) and overwrite production. Then
there is no production `web.users` to compare against, and rule 6's id
diff has nothing to run on. June's restore went to a side instance
because someone chose that, not because the platform requires it.
**Unblocks:** rule 6 (or rule 4) says to restore into a new instance and
never over production, and gives the reason: the id comparison needs the
live table.

Not blocking, and not a follow-up from this review: the app-wide
logging gap in the branch's `DEV_NOTES.md` entry is bigger than
deletions (every `logger.info` in `app/` is dropped). It goes through the
next triage, as drive-bys do.

**Not verified:** the id comparison and the clone-side `delete_account`
call have never been run. No clone exists, and making one is a
production operation. The rule is written from the schema and the
code, which I re-read. No routed check: docs only, nothing changes in
production.

## Re-review

**VERDICT: APPROVED** — 2026-10-26, on `504f866`. R1 resolved. Rule 6
now says "one `303` per self-serve deletion", names email deletions
(terms §9, privacy §8) as counted from the mailbox, and the *Limit*
paragraph falls back on "the 303 count and the mailbox". The changelog
reads "before self-serve deletion and §8's 7-day promise". R2 resolved.
Rule 6 opens with "restore into a new instance, never over
`indie-runners-db`" and gives the reason: an in-place restore leaves no
live `web.users` to compare against. The fix commit touches only those
lines. Docs: 61 lines. `deploy: batched`, docs only.

**Not verified:** unchanged from above. Rule 6 has never been run,
because that needs a real clone. No routed check: nothing changes in
production.
