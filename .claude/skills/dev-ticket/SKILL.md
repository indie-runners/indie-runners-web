---
name: dev-ticket
description: Take the top ready ticket and work it to "branch ready" — worktree, build, verify in the browser both tiers, document, before-merge checklist. Use in the developer terminal.
disable-model-invocation: true
model: opus
---

# Developer — one ticket

**Read `docs/roles/README.md`, then `docs/roles/developer.md`, then your
ticket.** This file routes and pins the recipes; the brief is the
authority and wins wherever the two disagree.

## Gate — before any command

**Two messages are for Paulo, not the PM: your first after reading the
spec, and the last of the ticket.** Each opens with three to five
sentences of plain English — what is broken (or was), who notices it (a
runner, a signed-in user, the bill), what the fix changes. No ticket ids,
column names or spec vocabulary. If he would have to open the ticket to
follow a sentence, rewrite it.

**Ponytail is on at `full`** (`CLAUDE.md`). It shapes the fix, never the
scope, and does not override the brief. Its `shortcut:` comments also go
to `docs/DEV_NOTES.md`.

**Bump to high effort** for `app/db.py`, a migration, or auth.

## Boundaries — the ones this skill cannot enforce for you

- **Scope is the ticket.** Drive-bys go to `docs/DEV_NOTES.md`; a
  thought about direction to `docs/IDEAS.md`.
- **The PR is yours, and closing an operator ticket's Issue. Not the
  Issue's body or labels** (the PM's). Not `docs/PLAN.md`.
- **`core.*` is read-only.** Wrong data routes to the scraper; a template
  workaround hides it.
- **Nothing writes to the database before Paulo has seen it and said
  yes** (`CLAUDE.md`): a migration apply, typed SQL, a backfill. Show
  the exact SQL or command and what it touches, then wait. Writing the
  file is fine.
- **One DB-touching session across both repos.**
- **You do not review your own work.** Say ready and wait.

## 1. Take the ticket

The lowest `p` label among open Issues that no PR names, skipping
`not-next` (its comment says what to take instead):

```bash
gh issue list --label p1 --json number,title,labels   # then p2, p3…
gh pr list --search '"Closes #<N>" in:body'           # empty = untaken
```

A frozen `W-###` in `tickets/` is not a ticket until the PM refiles it
as an Issue; do not improvise a spec.

Read the spec in full, including "Out of scope". **Stop: your next
message is Paulo's summary**, then these fields — ticket, defect,
evidence (quoted), acceptance, out of scope, deploy flag and whether it
carries a migration, and why this one if a higher row was skipped.
**Then end the turn and wait for his go-ahead** — no worktree, PR or
other command until he replies.

## 2. Worktree

On Paulo's go-ahead:

```bash
git pull --ff-only          # master moves only on GitHub now
git worktree add ../irw-<N> -b fix/<slug-of-the-defect>
cd ../irw-<N> && ln -s ../indie-runners-web/.env .env
ln -s ../indie-runners-web/cloud-sql-proxy cloud-sql-proxy
```

Rewrite `docs/TODO.md` for this ticket, keeping its header with the date and ticket id updated — steps, what you must measure, what you are unsure of, and later
what the work disproved. Nothing carries across tickets: an item that
outlives yours goes to `docs/DEV_NOTES.md`, for the board. A false premise is told to the PM, not silently
rescoped. Commit it, then open the draft — that is `wip`:

```bash
git push -u origin fix/<slug>
gh pr create --draft --base master --title "<title>" --body "Closes #<N>"
```

## 3. Build, then verify by running it

No test suite. The recipes — `bash scripts/dev.sh`, the anon `curl`, the
minted session cookie for the signed-in tier — are in the brief under
"There is no test suite". Check the page, not the status code.

**Confirm you are serving this worktree** (W-009): a uvicorn from another
checkout may already hold `:8000`, and `dev.sh` will not say so.

```bash
ss -ltnp | grep :8000        # then: ls -l /proc/<pid>/cwd
```

## 4. Document

Changelog with a version bump — wrong belief, cost, new belief, evidence,
**and what you verified and how**; output with user data or counts goes
to `evidence #N` (README § Boundaries). ARCHITECTURE if a decision changed,
claims scoped to what you ran. FILE_TREE in the same diff if a file was
added, moved or removed.

## 5. Before saying ready

Run the brief's "Before merging" list as a gate and report each line.
Docs budget, from the worktree:

```bash
git diff master --numstat -- docs/ | awk '{n+=$1} END {print n}'   # ≤ 100
```

Then the PM's block: believed → found · changed, by file · verified,
which tier and how · version · migration and deploy flag. Push, put
that block in the PR body under `Closes #N`, and mark it ready —
**out of draft is the handover**, not the message; the PM reads the
PR, not your terminal.

```bash
git push && gh pr ready && gh api -X PATCH \
  repos/indie-runners/indie-runners-web/pulls/$(gh pr view --json number -q .number) \
  -F body=@<file> >/dev/null
```

Not `gh pr edit`: it exits 1 on GitHub's Projects (classic) deprecation
and leaves the body unchanged (2026-11-10, gh 2.45). Bare `gh pr view` and
`gh issue view` fail the same way; add `--json`.

**The body is public**: output with user data or counts goes to
`evidence #N`, cited by name.
If `master` moves before the merge, bring it in yourself — `git fetch
origin && git merge origin/master && git push`, never a rebase — and
wait for `build` again.
After a `BLOCKED` line, `gh pr ready --undo` while you fix, `gh pr
ready` again. **Then wait.
Do not clear while waiting.** Read the verdict line, not the paragraphs.

## 6. After an approving verdict

The verdict is the last line of the PM's comment on the PR. The merge
closes the Issue:

```bash
gh pr checks --watch && gh pr merge --merge   # GitHub deletes the branch
cd ../indie-runners-web && git pull --ff-only
git worktree remove ../irw-<N> && git branch -D fix/<slug>
```

An operator ticket has no branch: close its Issue when the line
approves, `gh issue close <N> --comment "<what was done>"`.

**Deploy only if the ticket says `deploy: immediate`.** A migration goes
before the image, and only on Paulo's word. `deploy.sh` builds local
`master`, so the pull above comes first.

```bash
./scripts/deploy.sh --check   # serving revision, changes nothing
./scripts/deploy.sh           # refuses a dirty tree; prints the rollback line
```

No test gate — there is no suite. Keep the printed rollback line until
the next audit sweep is clean, and say in the terminal that you deployed.

**The last message opens with Paulo's summary** — what was wrong, what
changed, what he will notice (or why nothing). Then `merged as <version>
— deployed <revision> | not deployed (batched)`. Then clear.
