# Paulo → chief of staff, 2026-11-09 — GitHub now enforces PRs on master

Ruleset `protect master` is active on the default branch, bypass list
empty: a PR is required (0 approvals), merge commits only, status check
`build` must pass on an up-to-date branch, no force push or deletion.
Squash and rebase merging are off; head branches are deleted on merge.
A direct push was rejected with GH013; PR #1 went the full way (CI
green, merge commit `9664fef`, branch deleted). Until the briefs change,
every session's push to `master` is rejected, this change included.

Change: `CLAUDE.md`'s "push master after every merge"; `/dev-ticket`
opens a PR with `gh pr create --base master` instead of merging locally,
body = ticket id + "Verified" summary, private detail to evidence;
`/review` reads the PR's diff and CI result and leaves its verdict as a
PR comment (it cannot approve: same account). Keep `fix/<slug>`. Name
the check `build` (the job), not `ci` (the workflow). Only this repo has
the ruleset; scraper and infra `docs/IDEAS.md` appends stay as they are.

To decide: (1) who clicks merge, Paulo or the developer after the PM
approves; (2) the PM's board-only edits, same rule or lighter, such as
one PR per PM session; (3) who brings a PR up to date when another
merges first; (4) later: "require conversation resolution".

(The message arrived pasted with several lines cut mid-sentence; this
file keeps only what was unambiguous.)
