# CoS → PM, 2026-11-09: tracked files are public; a ticket quotes what the rule allows and names the rest

From Paulo, directly: the repo is going public. A cleaned copy with
fresh history becomes the working repo, so every tracked file is public.
The rule is in `docs/roles/README.md` § Boundaries.

**What changes for you:**

- **Tickets.** Quote the evidence the rule allows. Name the rest as
  `AUDIT_<ts> F<n>`, never by path, and state what was checked and the
  result. The crew slugs, user ids, counts and log rows stay in the
  gitignored report. You do the redacting, when you cut the ticket. The
  auditor's report is private and still pastes everything.
  (`tickets/README.md` § Evidence, `pm.md` § Writing a ticket, `/triage`
  §3.)
- **Routed checks.** Same rule. A signature names the query and the
  shape of the row, never a slug, an id or a count (header, "What an
  entry must contain"). The audit flagged existing entries
  (ROUTED_CHECKS 829-830, 978, 1138). Cleaning those is part of making
  the copy, not this note.
- **Cross-repo routes: unchanged.** Keep quoting inline into the
  scraper's and infra's `docs/IDEAS.md`. Both repos are private, and
  the README now says so as the condition. If either goes public, the
  route needs a new home. Bring it here.
- **The developer reads from a worktree.** The report is in the main
  checkout, the first line of `git worktree list`. Name the report and
  finding so it can be found.

**Why `exports/` and not somewhere new:** the reports already live
there, it is already gitignored, and the README already says a finding
survives its report being deleted, because the sweep can be re-run. A
ticket that says what was checked and the result is enough to re-run it.

**`docs/IDEAS.md` goes public too** (Paulo, 2026-11-09). It stays
tracked, the rule applies to it, and an idea that breaks the rule is
asked about before it's appended (`CLAUDE.md`).
