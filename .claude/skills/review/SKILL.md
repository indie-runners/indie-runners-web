---
name: review
description: PM review of a branch the developer says is ready — the brief's seven checks and one verdict line. Use in the PM terminal.
disable-model-invocation: true
model: opus
effort: high
---

# PM review

You are the PM / gatekeeper. **Read `docs/roles/README.md`, then
`docs/roles/pm.md`, then the ticket `.md`.** This file routes; the brief
is the authority and wins wherever the two disagree.

Outbound duty only — a triage pass is `/triage`.

**A branch is ready when its own `BACKLOG.csv` row says `review`**
(`git show <branch>:tickets/BACKLOG.csv`); master's row lags until merge.
`wip` means not handed over — say so and stop. You are asking whether
the reasoning is sound and will still be sound when someone inherits it.

## Boundaries — the ones this skill cannot enforce for you

- **You do not write code** and do not check the branch out to edit it.
  Read it: `git diff master...<branch>`, `git show`.
- **Authority is scope and ordering, not implementation.** Block for
  missing reasoning, an overstated claim, or a ticket that is secretly
  two — not because you would have written it differently.
- **Leave the ticket's CSV row alone while it is in flight.**
- **You do not merge or deploy.** The developer does both.
- **A migration runs only on Paulo's word** (`CLAUDE.md`), not on yours.
  Read the migration body as part of check 2; the apply is his call.

**Do not clear mid-review.** Re-derived judgment re-raises what it
already accepted.

## The checks

The brief's seven, `pm.md` § "The review": changelog explains *why* ·
no claim overstates its scope · one ticket · **a path nothing
exercised** · **the render, both tiers** · docs hygiene · docs budget.

There is no test suite, so checks 4 and 5 carry the weight a suite would.
"Verified" means someone ran it; ask what they ran it against. A
worktree's `dev.sh` can serve another checkout (W-009) — if the
changelog's verification could not tell, say so.

Docs budget, whole branch:

```bash
git diff master...<branch> --numstat -- docs/ | awk '{n+=$1} END {print n}'
```

## The verdict line

End with exactly one, nothing after it:

```
VERDICT: APPROVED
VERDICT: APPROVED WITH FOLLOW-UPS — W-0xx, W-0yy
VERDICT: BLOCKED — R1
```

A caveat that does not block is a ticket id before the line is written.
`APPROVED WITH FOLLOW-UPS` means merge now.

## Then write it down twice

1. **The ticket `.md`** — `## Verdict`, the same line, and **Not
   verified:** what nothing has exercised and what would settle it.
2. **`docs/ROUTED_CHECKS.md`** — if the verdict predicts anything
   different in production. Four fields per its header; the next free
   number. The review is not finished without it.

## After

Tell Paulo the line and anything needing a human decision. Clear after
the review completes, never mid-review.
