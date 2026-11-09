# W-022 — A user cannot delete their own account, and the privacy page says a button is coming

`priority: 2` (raised from 3 by Paulo, 2026-10-22) · `effort: M` · `area: services` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-21 (Paulo), "Let a user delete their own profile"`

## What is wrong

There is no self-serve way out. GDPR Art. 17 is met today by email, and
the privacy page says so (`privacy.html:104-109`):

> To request access to your data or deletion of your account, email
> paulo@indierunners.co. We will respond within 30 days.
> A self-service deletion button on your profile is planned but not yet
> available; until it ships, email is the mechanism.

So nothing is broken. It was p3, and Paulo raised it to p2 on 2026-10-22. But the page already promises
the button, and it says "a full account deletion request removes" past
attendance rows (`:85-90`). This ticket has to deliver exactly that.

## What the developer must settle (name each choice and why)

1. **What goes.** `web.users` row, `auth_identities`, `attendance`
   (**past rows included**, per the privacy page) and crew memberships.
   The model declares `ondelete="CASCADE"` on those FKs
   (`app/models/web.py:40, 96, 130`). **Verify the database actually
   carries those constraints** (`information_schema`, one read-only
   session). Do not trust the Python declaration; W-007 is the precedent.
2. **Crews the user created.** `web.crews.created_by` is a plain
   `Integer` with **no FK** (`web.py:82`), so a deletion leaves it
   dangling. Choose between deleting their crews, keeping them ownerless,
   or blocking deletion until ownership moves, and say what other
   members see.
3. **Guarded, because it is destructive and irreversible.** A POST, a
   confirmation step the user must complete (not a JS `confirm()` alone),
   and the session cleared afterwards. **The app has no CSRF token on any
   POST today** (grep finds none). The session cookie's SameSite setting
   is the only cross-site guard, so state what it is and whether it is
   enough for an irreversible action. Only the signed-in user can delete themselves:
   no user id from the request.
4. **One transaction.** A half-deleted user (identity gone, row present)
   is the data-loss shape to rule out.

**If any of this needs DDL** (for example an FK on `created_by`), write
the migration and **stop for Paulo's approval**. Do not run it. Per
PLAN, a ticket that needs DDL is a signal to say so out loud.

## Acceptance

1. A signed-in user can delete their account from settings or profile,
   through a confirmation step.
2. Afterwards: signed out; their profile URL 404s; no row in any `web.*`
   table references their id; their avatar is gone from every attendance
   strip and crew page.
3. Signing in again with the same Google account creates a **new** user,
   not a resurrected one.
4. A second user's data is untouched. Check with a real second account,
   not by reading the code.
5. The privacy page's §8 paragraph is updated in the same diff. It
   currently says the button does not exist.
6. Verified on a **dev/throwaway user only**, never one of the real
   users. Say which.
7. Changelog entry with the reasoning.

## Out of scope

- Data export (Art. 20). It is a different ticket if anyone asks.
- Admin deletion of *other* users. That is the back-office entry in
  IDEAS, still raw.
- Soft-delete or a grace period. Nobody asked for one, and the privacy
  page promises removal.

## Amended at review (2026-10-23)

**Acceptance 2, "their profile URL 404s", was wrong.** A missing user
renders the private placeholder, the same as an id that never existed,
so a 404 would reveal which ids are real (ARCHITECTURE § visibility).
The developer disproved it in TODO and left the code alone, which was
correct. Acceptance 2 now reads: *their profile URL renders the same
placeholder as a never-existing id.*

## Verdict

**VERDICT: BLOCKED — R1** — 2026-10-23, on `d9f1c54`. The board still
says `wip`; reviewed on Paulo's word that it is handed over.

The engineering is not in question. Run from the worktree with
`/proc/<pid>/cwd` checked. Throwaway users 23/24 only. Real users' rows
hashed before and after. All six user columns enumerated. Cascades read
from `pg_constraint`. Both soft refs handled, and it refuses rather than
leaving one dangling.

**R1 — the new privacy §8 sentence promises more than is true.** It says
deletion removes the data "immediately and permanently". The instance
(`indie-runners-db`, project `indie-runners-dev-470411`, the one holding
the real users) keeps 7 automated backups and 7 days of point-in-time
logs (`gcloud sql instances list`, 2026-10-23). So a copy survives up to
7 days. **Unblock:** the sentence stops claiming more than the live
database, or it names where copies remain and when they expire. **Which
wording is Paulo's call**: it is a legal page in his voice. §6's silence
on backups predates this branch and is not part of R1. `settings.html`'s
"cannot be undone" is true for the user and stays.

On re-review, only that sentence is in question (`git diff d9f1c54..`).
W-031 (the other POSTs' Origin check) goes on the line as a follow-up.
Merge order: W-025 is approved and also claims 1.9.14, and both branches
touch `main.py`'s imports, so whichever lands second renumbers and
resolves.

**Not verified:**
- A real Google re-sign-in after deletion. The developer called
  `get_or_create_user_from_google` directly.
- `/privacy` rendered anon after the edit, and the new settings section
  seen in a browser. The 400 path proves `settings.html` renders.
- Production `Host` matching `Origin`. Inferred: the canonical-host
  middleware reads the same `Host`, so W-017's redirect working in prod
  implies this works (routed check 6, still pending deploy). If it is
  wrong, every delete returns 403: fail-closed, no data lost.
- A request without `Origin` passes the check by design; SameSite still
  guards it.
- The leftover-reference refusal (a 500, rolled back). Unreachable
  today: no route lets a creator leave their crew. **A future "leave
  crew" or "remove member" ticket makes it reachable** and must hand
  over `created_by` itself.

## Re-review verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-031, W-032** — 2026-10-23, on
`7249f25`. The branch row says `review`. Read `git diff d9f1c54..7249f25`
only: privacy §8, the changelog and the row.

**R1 resolved.** §8 now says the live rows go immediately and backup
copies last up to 7 days. Checked against the instance, not the
changelog. `gcloud sql backups list --instance indie-runners-db` shows 7
backups, all `AUTOMATED`, 2026-10-17 to 2026-10-23. Retention is
`retainedBackups: 7` (COUNT), and PITR is on with
`transactionLogRetentionDays: 7`. The worst case is a deletion right
after the 03:00 backup, which lasts until 7 such backups follow it:
just under 7 days. So "up to 7 days" holds. The changelog says the
wording is Paulo's, which I take as stated. Docs budget across the
branch: 80.

**W-032 (follow-up, not a blocker):** the sentence is true today but
will not stay true. ARCHITECTURE migration rule 4 takes a manual
snapshot before every destructive migration, and an on-demand backup
never expires. A restore inside the 7 days also resurrects deleted
accounts. Both are about operator procedure, not this branch.

Merge order is unchanged: W-025 also claims 1.9.14, so whichever
merges second renumbers.

**Not verified** (adds to the first verdict's list, which still stands):
- `/privacy` rendered after this edit. The change is plain text inside
  an existing `<p>`.
- That no copy exists outside Cloud SQL: a local `pg_dump`, or a GCS
  export from the scraper side. Grepping both repos found no export
  script. I did not list buckets.
