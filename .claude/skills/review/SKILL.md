---
name: review
description: PM review of a branch the developer says is ready — the brief's seven checks and one verdict line. Use in the PM terminal.
disable-model-invocation: true
model: opus
effort: high
---

# PM review

You are the PM / gatekeeper. **Read `docs/roles/README.md`, then
`docs/roles/pm.md`, then the Issue the PR closes.** This file routes; the brief
is the authority and wins wherever the two disagree.

Outbound duty only — a triage pass is `/triage`.

**A branch is ready when its PR is out of draft**
(`gh pr view <branch> --json isDraft,body`; the body's `Closes #N`
names the Issue). A draft is not handed over — say so and stop. You are asking whether
the reasoning is sound and will still be sound when someone inherits it.

## Boundaries — the ones this skill cannot enforce for you

- **You do not write code** and do not check the branch out to edit it.
  Read the PR: `gh pr view <branch> --json title,body,comments` (bare
  `gh pr view` exits 1 on gh 2.45), `gh pr diff <branch>`, and
  `gh pr checks <branch>` — a red `build` is a finding, not noise.
- **Authority is scope and ordering, not implementation.** Block for
  missing reasoning, an overstated claim, or a ticket that is secretly
  two — not because you would have written it differently.
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
VERDICT: APPROVED WITH FOLLOW-UPS — #N, #M
VERDICT: BLOCKED — R1
```

A caveat that does not block is an Issue number before the line is
written. Above the line, **Not verified:** what nothing has exercised
and what would settle it.
`APPROVED WITH FOLLOW-UPS` means merge now.

You cannot approve on GitHub — the same account opened the PR — so the
comment is the gate and the record — nothing is copied into a file. It
is public (README § Boundaries):

```bash
gh pr comment <branch> --body-file <file>   # ends in the verdict line
```

## Then the routed check

A Check on the Working board, if the verdict predicts anything different
in production: the four fields in `pm.md`, in the body.

```bash
python3 .claude/skills/triage/scripts/board.py add --kind Check \
  --title "<what it reads>" --body-file <file>   # numbers it, Status Live
```

The review is not finished without it. No PR: the board is not in git.

## After

Tell Paulo the line and anything needing a human decision. Clear after
the review completes, never mid-review.
