# TODO: W-114 — The private-term hook passes a term in a filename, and a blank list

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-10_

- [ ] Path check: `git diff --cached --name-only --diff-filter=ACR` (a pure rename or a binary file has no `+++` line)
- [ ] A term file with no non-blank term refuses like a missing one
- [ ] `pre-merge-commit` hook -> same staged check (chosen over narrowing ARCHITECTURE)
- [ ] Prove in a throwaway repo with a dummy term: filename hit, blank list, merge hit refuse; clean commit and clean merge pass -> evidence W-114
- Unsure: does `pre-merge-commit` see the merge result in `--cached`? Measure it.
