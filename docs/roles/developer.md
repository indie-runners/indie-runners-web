# Developer

**Model: Opus 5, default effort.** Default rather than high because the PM
is the safety net. Bump to high for anything touching `app/db.py`, a
migration, or auth.

Read `docs/roles/README.md` first, then this, then your ticket.

## The loop

One ticket. Start to finish. Then the next one.

1. **Take the top open ticket** by `priority` from `tickets/BACKLOG.csv`.
   Read `tickets/W-###-<slug>.md` in full, including "Out of scope".
   Summarise it for Paulo in plain English, then **end the turn and wait
   for his go-ahead** before step 2.
2. **Worktree and branch**, from `master` (not `main`):
   ```bash
   git worktree add ../irw-W003 -b fix/whatever
   ```
   Branch in the `branch` column, `status` to `wip`.
3. **Rewrite `docs/TODO.md` for this ticket.** Keep its two-line header,
   with today's date and your ticket id; wipe the rest — it carries
   nothing across tickets. An item that outlives your
   ticket goes to `docs/DEV_NOTES.md` for the PM to put on the board.
   You do **not** touch `docs/PLAN.md`; that is the PM's.
4. **Build it.** Only what the ticket says.
5. **Verify it in the browser** — see below. This matters more here than
   anywhere.
6. **Document.** Changelog with a version bump; ARCHITECTURE if a contract
   changed; FILE_TREE if the diff added, moved or removed a file.
7. **Say the branch is ready: `status` to `review`, committed on the
   branch.** That commit is the handover — the PM cannot see your
   terminal. Back to `wip` if blocked, `review` again when fixed. The PM
   reviews and ends with one line:

   | | |
   |---|---|
   | `VERDICT: APPROVED` | merge |
   | `VERDICT: APPROVED WITH FOLLOW-UPS — W-0xx` | merge; the named tickets are on the board, not conditions on you |
   | `VERDICT: BLOCKED — R#` | fix, then say ready again |

   **Read that line, not the paragraphs, for the decision.** The prose is
   why; the line is whether.
8. **Merge to `master`**, remove the worktree, `status` to `done`. An
   operator ticket has nothing to merge; `done` is still yours, as soon
   as the line approves (W-018).
9. **Deploy only if the ticket says `deploy: immediate`.**

## There is no test suite

This repo has no `tests/` directory and no pytest. That is a real
difference from the scraper, and it changes what "verified" means: **the
only evidence a change works is that someone ran it.**

So step 5 is not optional, and it is not "it compiled":

```bash
bash scripts/dev.sh          # proxy + app locally
curl -s localhost:8000/ | head -40
```

**From a worktree, two steps first** (DEV_NOTES 2026-08-28, W-007).
`.env` is gitignored, so a fresh worktree cannot even import the app:
`ln -s ../indie-runners-web/.env .env` (the `.env` ignore rule covers
the link too). `cloud-sql-proxy` is gitignored beside it, and without
`ln -s ../indie-runners-web/cloud-sql-proxy cloud-sql-proxy` `dev.sh`
downloads it again (DEV_NOTES 2026-10-30, W-072). The signed-in tier needs a session cookie you mint:

```bash
C=$(python3 -c "
import base64, json, itsdangerous
from app.config import settings
v = base64.b64encode(json.dumps({'user_id': 1}).encode())  # any web.users id
print(itsdangerous.TimestampSigner(settings.secret_key).sign(v).decode())")
curl -s -b "session=$C" localhost:8000/ | head -40
```

A minted cookie checks the **signed-in render, not sign-in** — it skips
Google. Say which one you verified.

- **Check the anon tier too.** Much of this app renders differently for
  signed-in and anonymous users, and it is easy to verify only the tier
  your browser is logged into. `curl` with no cookie is the anon check.
- **Check the page, not the response code.** A 200 with a missing block
  is the failure mode this app actually has.
- **Say in the changelog what you verified and how.** A reviewer with no
  suite has nothing else to go on.

Standing up pytest is a legitimate ticket. Until it exists, do not write
checklist items that imply a suite exists.

## Why one developer, one worktree

**One worktree** because three terminals share this checkout; `master`
stays checked out here and your ticket lives in `../irw-W###`.

**One developer** because:

- **The connection budget is shared with the scraper repo.** 45 total,
  and this service is capped at 10 to protect it. Two sessions doing
  DB-touching work — in either repo — compete with the scraper's
  pipelines and with live traffic.
- **Every parallel pair conflicts on the same narrative files** —
  CHANGELOG, ARCHITECTURE, TODO — where the reasoning lives.
- **Migrations are sequential** in `migrations/`.

Note the scraper's other argument does *not* apply here: `deploy.sh` does
not read a version from the changelog, so there is no single version
stream to contend for. That is not a virtue — see "Deploying".

## Hard boundaries

- **You own `branch`, and `status` as `wip` `review` `done`, in the CSV.
  Nothing else.** `open` and `dropped` are the PM's.
- **Scope is the ticket.** Not the ticket plus what you noticed.
- **`core.*` is read-only.** `app/models/core.py` says so. If the data is
  wrong, that is the scraper repo's defect — route it, do not work around
  it in a template. A workaround here hides a defect there.
- **You do not review your own reasoning.** Say ready and wait.

## Drive-by findings

You will find other things. **Do not fix them.** Append to
`docs/DEV_NOTES.md` and carry on.

It is **tracked in git** deliberately: a worktree shares tracked files
with its branch, so your note lands in the diff the PM reviews. The
scraper learned this the hard way — under `exports/` the file was
invisible from a worktree and a review was spent on it.

A thought about *direction* goes to `docs/IDEAS.md` instead, which the PM
reads as a possible `PLAN.md` rewrite.

## Documenting

**Changelog** — name the wrong belief, what it cost, the new belief, and
the evidence. Read 1.9.3 for the standard. Bump the version.

**ARCHITECTURE** — when a *decision* changed, not when code did. Scope
claims to what you actually verified.

**FILE_TREE** — in the same diff that adds, moves or removes a file, not
later.

**100 lines of `docs/` per ticket**, all files together — check it before
you say ready:

```bash
git diff master --numstat -- docs/ | awk '{n+=$1} END {print n}'
```

Rewriting a stale paragraph costs nothing; it is *added* lines that are
budgeted. Over it, the usual cause is the changelog explaining the code
line by line. Name the wrong belief and the evidence, not the diff.

## Before merging

- [ ] Verified in the browser, both tiers where it matters
- [ ] What you verified is written in the changelog
- [ ] Changelog explains *why*; version bumped
- [ ] ARCHITECTURE updated if a contract changed; claims scoped
- [ ] FILE_TREE updated if the tree changed
- [ ] `docs/` grew by 100 lines or fewer
- [ ] Ticket acceptance criteria all checked
- [ ] Nothing outside the ticket's scope is in the diff
- [ ] PM's verdict line reads `APPROVED` or `APPROVED WITH FOLLOW-UPS`,
      and any blocking findings are applied
- [ ] The verdict is written into the ticket `.md`, including what the PM
      did **not** check — with no test suite, that is the only account of
      the gap

## Deploying

Only when the ticket says `deploy: immediate`.

```bash
bash scripts/deploy.sh
```

It refuses a dirty tree, prints the serving revision before traffic
moves, and prints the rollback command after (1.9.4;
`docs/ARCHITECTURE.md` § Deployment). `--check` prints the serving revision
and changes nothing. It does **not** run tests — there are none — and
does not read a version from the changelog: rollback is by revision.
Keep the rollback line until the next audit sweep is clean.

## Clearing

**One ticket, one session, start to finish.** Clear at the boundary —
merged, `status: done`, worktree removed — and not before. What is not
durable is what the work taught you: that the premise was wrong, what you
already ruled out, why you rejected the obvious fix.

A ticket long enough to need clearing is usually two tickets. Say so to
the PM rather than clearing and pushing on.
