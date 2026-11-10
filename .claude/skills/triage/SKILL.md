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
- **The Issue is yours** — title, body, labels, closing as not planned.
  Never a PR, never closing as completed. While a PR names the Issue,
  amend it only by comment, so the developer sees the change.
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
4. The board: `gh issue list --state open --limit 200 --json
   number,title,labels`, and `gh pr list` for what is in flight. Then
   the frozen `tickets/BACKLOG.csv`'s rows still `open`: an empty Issue
   list is not an empty board while one of them is wanted. Refile what
   is as `W-###: <title>` (`pm.md` § Writing a ticket); drop one by
   refiling it and closing it as not planned; leave the rest. A row
   with an Issue of either state is done with (`gh issue list --state
   all --search "W-### in:title"`).
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
| **Ticket** | a new Issue (§ 3) |
| **Raise / lower** | swap its `p` label; say why in a comment |
| **Retire / amend a check** | in the check's header, which wins over its body |
| **New check** | something shipped that a future sweep must read correctly |
| **Route** | `core.*` → scraper `docs/IDEAS.md`, public rule (README), `source: web-audit`; infra → infra `docs/IDEAS.md`, `## web #N <date> — <subject>`, `source: web-triage`; commit and push there |
| **Drop** | close as not planned, **the reason in a comment** |
| **Leave raw** | with what would settle it |

An `IDEAS.md` entry saying the arc is the wrong shape is a `docs/PLAN.md`
rewrite, not a set of tickets. Record each entry's outcome on it.

## 3. Tickets

An Issue from `.github/ISSUE_TEMPLATE/ticket.md`: what is wrong ·
evidence **pasted verbatim** where README's public rule allows it,
otherwise named as `AUDIT_<ts> F<n>` · acceptance that is observable ·
**out of scope**, always · source. Labels, one of each, set now:

```bash
gh issue create --title "<defect>" --body-file <file> \
  --label p3,effort:S,deploy:batched,area:templates
```

Priority order is the brief's. A ticket ranked high but not next gets
`not-next` and a comment: what it waits on, which to take instead. A
frozen `W-###` is refiled this way when wanted (`pm.md` § Writing a
ticket). Tickets, drops and label changes need no PR; `PLAN.md`,
IDEAS outcomes and routed checks go in one `pm/<date>-<slug>` PR.

## 4. Routed checks

Four fields, the ones the file's header defines: **gate** (an image
digest, never a date or "after the merge"), **signature**, **reading in
every direction** including NULL/empty/error, **retire**, and `· LIVE` in the entry's header from day one. Naming a
ticket id is not a routed check.

## 5. After the pass

Tell Paulo what changed on the board and what needs a human decision.
Add one line from `python3 .claude/skills/cos/scripts/inbox.py --count`.
Then clear.
