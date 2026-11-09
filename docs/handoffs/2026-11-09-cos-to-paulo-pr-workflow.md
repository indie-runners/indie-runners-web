# CoS → Paulo, 2026-11-09: every write to master is a PR; the developer merges

Answering `2026-11-09-paulo-to-cos-pr-workflow.md`.

**Ruling: applied.** The rule lives once, README § Boundaries ("Nothing
reaches `master` except by a merged pull request"); `CLAUDE.md`,
`developer.md` steps 7–8 and its checklist, `pm.md` § Outbound and
§ "Then write it to the ticket", `/dev-ticket` §2/§5/§6, `/review` and
`/cos` §3 point to it. The public rule now covers PR bodies and comments.

**1. The developer merges**, `gh pr merge --merge`, after the approving
line. Merging deploys nothing, so it is not the production decision;
`deploy:` and migrations are, and stay yours. Your click on a `batched`
ticket would add a step that decides nothing. The PM's comment is the
gate by convention only — GitHub cannot see it.

**2. One PR per session** for the PM (`pm/<date>-<slug>`) and for this
seat (`cos/…`), merged by whoever opened it once `build` is green. The
board never had a reviewer; the PR adds the trail without inventing one.
A PR per edit would multiply question 3 for nothing.

**3. Whoever opened the PR** brings it up to date: `git merge
origin/master`, push, wait for `build`. Not a rebase — the PM read those
commits. `gh` here is 2.45, which has no `gh pr update-branch`.
Expect conflicts in `BACKLOG.csv`, where a ticket branch and a PM
session edit neighbouring lines.

**4. Not yet**, as you say. No comment has needed resolving so far.

Two things the old rule did that your list did not name:
- `done` was committed to `master` after the merge. It is now the
  branch's last commit before merging; an operator ticket's `done` is
  a one-commit `done/W-###` PR.
- The PM's verdict in the ticket `.md` and `ROUTED_CHECKS.md` were
  direct commits. They go in the PM's session PR.

For you: `deploy.sh` refuses a dirty tree but not a `master` behind
`origin`, so it can build a stale image. The recipes now pull first; a
guard in the script would be a developer ticket, if you want one.
