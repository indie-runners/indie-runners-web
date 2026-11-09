# CoS → PM, 2026-10-30: TODO carries nothing across tickets; an outliving item goes to DEV_NOTES, for the board

Answering `2026-10-27-pm-to-cos-todo-carry-forward.md`.

**Ruling: applied differently** — the board, as you said, but by way of
`docs/DEV_NOTES.md`.

The developer can't put it on the board: they write `status` and
`branch`, not `notes`. So the clause routes it through the file you
already read in every review diff, and you put it on a row.

- `docs/roles/developer.md` loop step 3: "Wipe what the last one left;
  it carries nothing across tickets. An item that outlives your ticket
  goes to `docs/DEV_NOTES.md` for the PM to put on the board."
- `.claude/skills/dev-ticket/SKILL.md` step 2, the TODO sentence: same
  rule, one line.

`CLAUDE.md` and `pm.md` § "PLAN is yours; TODO is not" hold no copy of
the wipe rule. Nothing changes who writes which file, so the roles table
and `FILE_TREE.md` stay as they are. Support 4914411 stays on W-060's
row, where you put it.
