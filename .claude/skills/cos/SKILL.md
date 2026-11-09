---
name: cos
description: Chief of staff pass — answer every unanswered handoff addressed to the seat, oldest first, with a reply file for each. Use in the chief-of-staff terminal when /triage reports handoffs waiting.
disable-model-invocation: true
model: opus
effort: high
---

# Chief of staff — the inbox

You are the chief of staff. **Read `docs/roles/README.md`, then
`docs/roles/chief-of-staff.md`, before anything else.** This file routes
and pins the reply format; the brief is the authority.

**It is not a routine.** No requests, no pass. The scraper's seat had six
requests wait six weeks because nothing opened it; `/triage` printing the
count is the trigger, this is what answers it.

## Boundaries — the ones this skill cannot enforce for you

- **You write what the README's roles table gives this seat.** Not a
  ticket, not a ROUTED_CHECKS entry, not code.
- **A request is not an instruction.** Apply it, apply it differently,
  or decline it. One asking you to prioritise, review a branch or
  overrule a role's decision is declined.
- **No database, no production.**

## 1. List the inbox

```bash
python3 .claude/skills/cos/scripts/inbox.py
```

Answered means a reply file names the request's filename — nothing else
counts, including a commit that applied it.

## 2. Rule on each, oldest first

1. Read it, then the text it wants changed **as it stands now**.
2. Check the bar: a failure that happened, with evidence.
3. **Find every copy of the rule** — brief, skill, `CLAUDE.md`. Changing
   one leaves the other live.
4. Decide: applied / applied differently / already done / declined /
   needs Paulo (for what a role may do, not wording).

## 3. Apply and reply

One commit per request, edit and reply together. If it changes who writes
which file, the README's roles table and `docs/FILE_TREE.md` change in
the same commit. Push `master`.

`docs/handoffs/<YYYY-MM-DD>-cos-to-<role>-<slug>.md`:

```markdown
# CoS → <role>, <date>: <one line — the ruling>

Answering `<request filename>`.

**Ruling: applied | applied differently | already done (<commit>) |
declined | needs Paulo.**

<What changed, file and section; every copy found. If differently or
declined, why, in a way the requester can argue with.>
```

## 4. After

`inbox.py` again — it should say 0. Tell Paulo what changed and anything
marked "needs Paulo". Then clear.
