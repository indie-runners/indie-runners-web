# CoS → Paulo, 2026-10-23: each role now opens with a skill, plus /cos

Answering `2026-10-23-paulo-to-cos-open-each-role-with-a-skill.md`.

**Ruling: applied, with three differences.**

**Added** `.claude/skills/{audit,triage,review,dev-ticket,cos}/SKILL.md`
and `cos/scripts/inbox.py` (copied unchanged). Each reads the README and
its brief first, says the brief wins, and restates the boundaries it
cannot enforce. Frontmatter as requested: `disable-model-invocation`,
auditor `sonnet`/`medium` without `Edit`, PM `opus`/`high`, developer
`opus` with no effort pinned (the brief bumps it for `db.py`, migrations
and auth). Ownership: the README's roles table, `chief-of-staff.md`
§ "What it owns" and `docs/FILE_TREE.md`.

**Ported to this repo's facts:** `master`, `W-###`, no pytest (verify
with `scripts/dev.sh`, anon and minted-cookie), the 100-line `docs/`
budget, migrations only on your word, Ponytail for the developer only,
the seven checks in `pm.md` rather than the scraper's six, and the two
summaries for you at the top of `/dev-ticket` as a gate.

**Differences:**

1. **The request's deploy fact was stale, and so were three briefs.**
   `scripts/deploy.sh` has refused a dirty tree and printed a rollback
   line since 1.9.4 (`e101216`). `developer.md` § Deploying, `pm.md`
   § deploy and `chief-of-staff.md` still said "no guards". All three are
   corrected, and `/dev-ticket` uses the script's own guards rather than
   a stop of its own.
2. **Not ported:** `sweep.py` (`auditor.md` already pins the connect
   recipe and queries; a script would be a second copy), the
   ROUTED_CHECKS filter agent (the file is 188 lines), the scraper's
   batch-bound and PM migration-apply steps (deploys here follow the
   ticket's flag; migrations follow you), caveman (a scraper-side choice
   nothing here asks for), `/analysis` (no seat), and `docs/prompts/` (it
   does not exist here).
3. **Added one thing:** `/dev-ticket`'s verify step checks which
   checkout is serving `:8000` — W-009's failure, which has already
   happened here once.

**`/cos` and `docs/handoffs/`: kept.** This request had no reader until
you opened the seat by hand, which is the scraper's six-week failure in
miniature. `/triage` now ends with `inbox.py --count`.
