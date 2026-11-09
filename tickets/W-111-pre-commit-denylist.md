# W-111 — Nothing stops a private term from being committed to a public repo

`priority: 2` · `effort: S` · `area: tooling` · `deploy: none`
`source: docs/handoffs/2026-11-09-cos-to-pm-public-rule-all-repos.md (Paulo)`

## What is wrong

Every tracked file and every commit message is public
(`docs/roles/README.md` § Boundaries). The only thing between a crew slug
or a real name and a public push is someone noticing it. A person reading
their own diff misses things, and once a commit is pushed, deleting it
doesn't take back what was published. Nothing in the repo refuses a commit
that contains a term known to be private.

## Evidence

- The pre-publication audit of 2026-11-09 (untracked, `public-audit-2026-11-09`
  in the main checkout's `exports/`) found crew slugs, user ids, a real
  name and GCP identifiers in tracked files. They were found by a one-off
  `grep` for a fixed list of terms, run by hand at the copying step
  (its step 7). That list is the starting term list here. It is not quoted:
  the list itself is the private data.
- `.github/workflows/ci.yml` can't do this job. CI runs after the push,
  when the term is already public, and a list stored in CI would need to
  live somewhere tracked or in a secret nobody can review.
- There is no git hook in the repo today, and `core.hooksPath` is unset.

## Acceptance

1. A hook script, tracked in the repo (e.g. `.githooks/`), wired up with
   `git config core.hooksPath`. The one-time setup command goes in
   `docs/` where a new clone would look for it.
2. It reads its terms from an **untracked** file, one per line, matched
   as fixed strings, ignoring case. The file lives in the main checkout's
   `exports/` (already gitignored), and the hook finds it from a worktree
   too: developers commit from worktrees, and `exports/` isn't in them.
   Resolve it through `git rev-parse --git-common-dir`, not a hard-coded
   path.
3. It refuses the commit when an **added line** of the staged diff, or
   the **commit message**, contains a term. It does not scan whole files:
   existing lines aren't the hook's job, and scanning them would block
   unrelated commits.
4. The refusal names the file and line (or "commit message") and the term
   it matched, so the person can fix it. It prints only to the local
   terminal.
5. With no term file it refuses and says where the file goes. A hook that
   quietly passes because the list is missing is the failure this ticket
   exists to stop. `git commit --no-verify` remains the deliberate way
   out. Default, veto at review: refuse rather than warn.
6. **Seed the list** from the terms in the audit's §6 step 7 grep (the
   list that had to reach zero hits), minus:
   - anything the README says is public on purpose: the project ID, the
     project number, service account names (the `gserviceaccount` term)
     and the Cloud SQL region;
   - Paulo's surname, in either form the grep uses. It is in `LICENSE`,
     so every commit touching it would be refused.

   What's left is crew terms and a first name. **Before a crew term goes
   on the list, confirm it doesn't match any `core.*` race slug**, using
   the hook's own rule (case-insensitive substring, so a crew term inside
   a longer race slug counts). Otherwise every commit naming that race is
   refused. A term that matches is left off and reported at review. This
   is a read-only query, so the one-DB-session rule applies. Record the
   query, and per term the hit or no hit, in `evidence W-111`. The terms
   never go in the ticket, the changelog or a commit message.
7. Proven both ways and recorded in `evidence W-111`, never in the
   ticket: a commit that adds a listed term (in a file, and separately in
   the message) is refused; a clean commit passes; both from a worktree.
8. No new dependency: shell plus git, or the standard library's
   `python3`.

## Out of scope

- **Growing the list past the seed.** Adding terms later is Paulo's call,
  made in the untracked file, so no review sees it.
- **Counts, and anything that isn't a fixed string.** The hook can't tell
  a user count from a race count. That stays with the person writing the
  line and with the public rule.
- **The scraper and infra repos.** They are going public too. Each needs
  its own hook and list, and that's their PM's to ticket. The script can
  be copied as-is.
- **Making it unskippable.** A local hook can always be bypassed, and
  W-110 rejected one for that reason. That's acceptable here: the hook
  doesn't replace care, it catches what care misses. GitHub push
  protection only covers secret formats, not names (audit step 10).
- **Scanning history.** The cleaned copy starts with fresh history, and
  the audit's step 7 scan covers it.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-114** — 2026-11-09. Acceptance
1–8 met. On top of the developer's cases, the PM ran copies of the scripts
in a throwaway repo: `commit -a` and `commit <path>` are refused; a
conflicted merge concluded with `git commit` is refused. A term in a
filename passes, and so does a term file of blank lines (W-114). No
ROUTED_CHECKS entry: `deploy: none`, and nothing in production changes.

**Not verified:** a clean `git merge` doesn't run the check (no
`pre-merge-commit`, W-114 acceptance 3). Locally the only merge is
`origin/master`, which is already public. The seed terms were checked
against `core.*` slug columns only, not event or race name columns. A
name match would only show up as a false refusal, which `--no-verify`
gets past; it can't leak anything. Until this merges and the main checkout
pulls, `core.hooksPath` points at a directory `master` doesn't have, so
commits there are not checked.
