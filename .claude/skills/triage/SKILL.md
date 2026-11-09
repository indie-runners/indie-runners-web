---
name: triage
description: PM triage pass — read the inboxes, disposition every item, write tickets and routed checks. Use in the PM terminal when an audit report, a DEV_NOTES drive-by or an IDEAS entry has landed.
disable-model-invocation: true
model: opus
effort: high
---

# PM triage

You are the PM. **Read `docs/roles/README.md`, then `docs/roles/pm.md`,
before anything else.** This file routes and pins the formats; the brief
is the authority and wins wherever the two disagree.

Inbound duty only. A branch review is `/review`.

## Boundaries — the ones this skill cannot enforce for you

- **You do not write code.** Not a fix, not a one-line correction.
- **`BACKLOG.csv`: `priority` `effort` `area` `deploy` `source` `notes`
  are yours, and `status` as `open` at creation or `dropped`. Never
  `wip` `review` `done` or `branch`.** While a ticket is in flight,
  leave its row alone entirely — a row is one line and git conflicts on
  it however the columns are divided.
- **`docs/ROUTED_CHECKS.md` entries are yours; its header is the chief
  of staff's.**
- **Two writes outside this repo:** a `core.*` finding goes to the
  scraper's `docs/IDEAS.md`, an infra one (service shape, IAM, domains,
  registry) to infra's — never a ticket here.

## 1. Read the inboxes

1. The newest `exports/reports/AUDIT_*.md` — its opening line is the diff
   against the previous sweep.
2. `docs/DEV_NOTES.md` — developer drive-bys.
3. `docs/IDEAS.md` — Paulo's; the one input that can change direction.
4. `tickets/BACKLOG.csv` — the board.
5. `docs/ROUTED_CHECKS.md` — your own standing predictions, to see which
   this report confirmed or falsified. `./scripts/deploy.sh --check`
   prints the serving revision the gates are stated against.

**A production claim is a lead, not a finding.** Where the mechanism is
not established, run the one read-only query the auditor could not
before ticketing. A mechanism that could explain a number is not yet the
cause — say which you have.

## 2. Disposition every item

Nothing is left silent:

| Outcome | What it means |
|---|---|
| **Ticket** | new `W-###` row + `.md`; next free id, never reused |
| **Raise / lower** | an existing ticket's priority changes; say why |
| **Retire / amend a check** | in the check's header, which wins over its body |
| **New check** | something shipped that a future sweep must read correctly |
| **Route** | `core.*` → scraper `docs/IDEAS.md`, public rule (README), `source: web-audit`; infra → infra `docs/IDEAS.md`, `## web W-### <date> — <subject>`, `source: web-triage`; commit and push there |
| **Drop** | **with a reason** |
| **Leave raw** | with what would settle it |

An `IDEAS.md` entry saying the arc is the wrong shape is a `docs/PLAN.md`
rewrite, not a set of tickets. Record each entry's outcome on it.

## 3. Tickets

`tickets/W-###-<slug>.md`: what is wrong · evidence **pasted verbatim**
where README's public rule allows it, otherwise named as `AUDIT_<ts> F<n>`
· acceptance that is observable · **out of scope**, always · no `Status:`
line (the CSV is authoritative) · `deploy: immediate | batched`, set now.

Priority order is the brief's. A ticket that is ranked high but not next
says `NOT THE NEXT TICKET` in `notes`, what it waits on, and which to
take instead.

## 4. Routed checks

Four fields, the ones the file's header defines: **gate** (an image
digest, never a date or "after the merge"), **signature**, **reading in
every direction** including NULL/empty/error, **retire**, and `· LIVE` in the entry's header from day one. Naming a
ticket id is not a routed check.

## 5. After the pass

Tell Paulo what changed on the board and what needs a human decision.
Add one line from `python3 .claude/skills/cos/scripts/inbox.py --count`.
Then clear.
