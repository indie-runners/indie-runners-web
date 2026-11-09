# Paulo → chief of staff, 2026-10-23 — open each role with a skill, as the scraper does

**Written from a scraper session on Paulo's behalf, at his request.** His
words: *"I like this setup with the roles and skills."* He wants the same
here. How it is shaped is yours to decide; this says what exists next
door and what it learned.

**This file also creates `docs/handoffs/`.** The web repo has no tracked
place for a role-to-role message. Keep the directory, or move this file
to wherever you rule such requests go.

## What the scraper has

Each role is opened by a slash command, `.claude/skills/<name>/SKILL.md`,
read with `../indie-runners-scraper/.claude/skills/` from this checkout:

| Skill | Role | What it pins |
|---|---|---|
| `/audit` | auditor | the sweep's steps, `scripts/sweep.py` running the SQL checks on one connection, the report format |
| `/triage` | PM | the three inboxes, the disposition table, ticket and routed-check fields |
| `/review` | PM | six checks on a ready branch, ending in the one verdict line |
| `/dev-ticket` | developer | choosing the next ticket, worktree, before-merge checklist, merge and deploy |
| `/cos` | chief of staff | answer each unanswered handoff, with a reply file per request |
| `/analysis` | analyst (a fifth seat there only) | recipes for one question from Paulo |

Commits with the reasoning: `0dc1825` (/audit), `e7ba572` (/triage),
`2bd18a6` (/dev-ticket), `679e701` (/review), `92a266a` (/cos, /analysis).

## The rules that made it work

From the scraper's `docs/roles/README.md` § "Where things live":

- **A skill is how a role is opened, not what it decides.** Each one
  starts by reading `docs/roles/README.md` and the role's brief. It says
  the brief is the authority and wins where they disagree. It holds no
  rule of its own; it holds recipes, formats and bundled scripts, the
  things each fresh session otherwise rediscovers.
- **A skill cannot enforce a boundary.** The auditor needs `Write` for
  its report, the same tool that edits code. The line stays in prose.
  Each skill carries a "Boundaries — the ones this skill cannot enforce
  for you" section restating them.
- **Frontmatter:** `disable-model-invocation: true`, so only Paulo opens
  a role, and the role's model and effort (`model: opus`, `effort: high`;
  the auditor `sonnet`/`medium` with `disallowed-tools: Edit,
  NotebookEdit`).
- **The skills, `docs/prompts/` and `CLAUDE.md` are the chief of staff's**,
  for the reason `docs/roles/` is: they describe how the work is done.
  Here your brief owns `docs/roles/*` only, so this needs the owner
  column in `docs/roles/README.md` to say so.
- **`docs/FILE_TREE.md` changes in the same diff.**

## What broke there, so you can skip it

- **An instruction at the end of a step gets dropped.** Paulo asked
  `/dev-ticket` to open and close each ticket with a plain-English
  summary for him. The instruction sat at the end of step 1, and a
  session went straight to work without it (scraper handoff
  `2026-10-22-paulo-to-cos-dev-ticket-summaries-not-shown.md`; fixed
  in `b402526`). Put what must happen first at the top, as a gate.
- **A seat nobody opens has an inbox nobody reads.** Six requests to
  the scraper's chief of staff waited six weeks. `/cos` plus
  `inbox.py --count`, printed at the end of every `/triage`, is the
  fix. It applies here only if handoffs become a thing here.
- **A large file belongs to an agent, not the session.** `ROUTED_CHECKS.md`
  there is ~7400 lines; `/audit` and `/triage` hand it to an agent with
  a fixed prompt (`docs/prompts/routed-checks-filter.md`) and read back
  the live entries only. Yours is smaller; port this when it is needed.

## What differs here

The skills were written against the scraper's facts; these are the web
repo's own, from its `CLAUDE.md` and briefs:

- **No test suite.** `/dev-ticket`'s test step becomes `bash
  scripts/dev.sh`, checked as both anon and signed-in.
- **`master`, not `main`; `W-###`, not `T-###`.**
- **The 100-line `docs/` budget** belongs in the developer's checklist.
- **Migrations run only on Paulo's word**, and `scripts/deploy.sh` has
  no guards, so the deploy step needs its own stop.
- **Ponytail is for the developer only**, which `/dev-ticket` can say.
- **No analyst seat here.** `/analysis` does not port unless you add the
  seat.

## What is wanted

`/audit`, `/triage`, `/review` and `/dev-ticket` for this repo, each
routing to its brief, and the ownership and layout rows that go with
them. Whether to add `/cos` and `docs/handoffs/` is yours to rule.
