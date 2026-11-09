# W-114 — The private-term hook passes a term in a filename, and a blank list

`priority: 2` · `effort: S` · `area: tooling` · `deploy: none`
`source: W-111 review 2026-11-09 (PM)`

## What is wrong

W-111's hook (`.githooks/denylist.sh`) checks the added lines of the staged
diff and the commit message. It has two gaps of the same kind it exists
to close, and one sentence in the docs claims more than it does:

- **A term in a file's path passes.** File paths are tracked and public
  too, like file contents. The awk parser already reads the path from the
  `+++ b/` line into `f`, but only the line body is matched.
- **A term file with only blank or whitespace lines passes, and says
  nothing.** `[ ! -s ]` only catches a zero-byte file. The awk then loads
  no terms and everything passes. W-111's acceptance 5 gives the reason:
  a hook that passes quietly because the list is missing is the failure.
- **ARCHITECTURE says "Every commit then refuses…".** A clean `git merge`
  never runs `pre-commit` (no `pre-merge-commit` hook is installed), and
  neither does cherry-pick or rebase.

## Evidence

The PM ran copies of W-111's three scripts in a throwaway repo, with a
dummy term (W-111 review, PR #3 comment). Results:

- a new file whose name contains the term, with clean content: exit 0;
- a term file of `\n  \n` and a staged line containing the term: exit 0;
- `git merge --no-edit` of a branch carrying a `--no-verify` commit with
  the term: exit 0, merge commit made.

## Acceptance

1. A staged added, renamed or copied path that contains a term is refused.
   The refusal names the path and says it is a filename hit.
2. A term file with no non-blank term is refused with the same message as
   a missing one.
3. Either a `pre-merge-commit` hook runs the same staged check, or the
   ARCHITECTURE sentence names exactly what is checked (`git commit`, and
   a conflicted merge concluded with it). Developer's choice, and the
   changelog says which.
4. Proven both ways in `evidence W-114`, never with a real term in a
   tracked file: each new refusal fires; a clean commit and a clean merge
   still pass.

## Out of scope

- **Branch names, PR titles and bodies.** They are public too, but no
  local commit hook sees them.
- **Cherry-pick and rebase.** They replay commits that already went
  through the hook, unless someone skipped it on purpose.
- **Growing the term list.** Still Paulo's call, in the untracked file.
