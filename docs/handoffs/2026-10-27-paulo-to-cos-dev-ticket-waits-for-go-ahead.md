# Paulo → chief of staff, 2026-10-27 — dev-ticket must wait for his go-ahead

Paulo's practice in all three repos: after `/dev-ticket` reads a new
spec, the developer gives him a plain-English summary of what it plans to
do, and **he gives the go-ahead before any work starts**. The web
developer has been going ahead without waiting.

None of the three `.claude/skills/dev-ticket/SKILL.md` files says to
wait. Step 1 only says the next message is the summary:

- scraper (step 1): "Then stop: your next message is the opening summary,
  before the worktree, `BACKLOG.csv` or any other command." Explicit
  about what comes next, which is probably why it holds.
- web and infra (step 1): "**Stop: your next message is Paulo's
  summary**, then these fields…". This can be read as "post the summary,
  then carry on in the same turn". Infra may hold only because of its
  "apply only on Paulo's word" gate (unverified).

What it needs, in all three repos (web, infra, scraper), step 1 and the
Gate: after the summary and fields, **end the turn and wait for Paulo's
go-ahead**. No worktree, `BACKLOG.csv` edit or other command until he
replies. Check whether `docs/roles/developer.md` should say it too, since
the brief wins over the skill.

Same handoff posted in each repo's `docs/handoffs/`; this copy is for **indie-runners-web**.
