# CoS → PM, 2026-11-09: the public rule covers routes out; detail that isn't an audit finding goes to `evidence W-###`

From Paulo, directly: the scraper and infra repos are going public too.
Follows `2026-11-09-cos-to-pm-tracked-files-are-public.md`.

**What changes for you:**

- **Routes out.** No more evidence quoted inline into the scraper's or
  infra's `docs/IDEAS.md`. The entry says what was checked, how to see
  it from their side, and the result, and cites `web AUDIT_<ts> F<n>`.
  They can't read our `exports/`, so the citation only points back to
  us; the entry has to stand on its own. `core.*` race data can still be
  quoted, user data never. (README § The other repo, `auditor.md`
  § Routing, `/triage` outcome table.)
- **Your own measurements.** A count or a row you took yourself goes to
  `exports/evidence/W-###.md` in the main checkout, as a dated section
  you append and never edit, cited `evidence W-###`. The developer
  does the same with "Verified" output (`/dev-ticket` §4).
- **Names.** "user A", "crew A" in prose, `<crew-a>` in a URL or slug.
  Letters are per file.
- **The cost.** That file has no history, isn't in a worktree, can't be
  read by claude.ai, and is gone if the machine is. Write the tracked
  file so it reads without it.

**A ticket for you to rank: a pre-commit denylist.** Paulo proposes a
hook that reads private terms from an untracked file (so the list is
never committed) and refuses a commit containing any of them. It's code,
so it's yours to ticket, like the status check. It would catch a crew
slug or a name that a person misses. It can't catch a count. The
copying step's `grep` in the public audit is a starting term list.
