---
name: triage
description: PM triage pass — read the audit report and the Working board, disposition every item, write tickets and checks. Use in the PM terminal when an audit report, a drive-by or an idea has landed.
disable-model-invocation: true
model: opus
effort: high
---

# PM triage

You are the PM. **Read `docs/roles/README.md`, then `docs/roles/pm.md`,
before anything else.** This file routes and pins the formats; the brief
is the authority and wins wherever the two disagree.

Inbound duty only. A branch review is `/review`.

`board.py` below is `python3 .claude/skills/triage/scripts/board.py`.

## Boundaries — the ones this skill cannot enforce for you

- **You do not write code.** Not a fix, not a one-line correction.
- **The Issue is yours** — title, body, labels, closing as not planned.
  Never a PR, never closing as completed. While a PR names the Issue,
  amend it only by comment, so the developer sees the change.
- **Checks and item statuses on the Working board are yours;**
  `board.py` itself is the chief of staff's.
- **Routing out is an Inbox, not a write to another repo:** a `core.*`
  finding becomes an Idea with Inbox scraper, an infra one (service
  shape, IAM, domains, registry) Inbox infra — never a ticket here.

## 1. Read the inboxes

1. The newest `exports/reports/AUDIT_*.md` — its opening line is the diff
   against the previous sweep.
2. `board.py list triage --bodies` — Raw and Shaped ideas (Paulo's; the
   one input that can change direction), New drive-bys, handoffs to the
   PM, and items missing a field. Until your migration lands (README
   § Where things live), also the frozen `docs/DEV_NOTES.md` and
   `docs/IDEAS.md` entries still open.
3. The Issues: `gh issue list --state open --limit 200 --json
   number,title,labels`, and `gh pr list` for what is in flight. Then
   the frozen `tickets/BACKLOG.csv`'s rows still `open`: an empty Issue
   list is not an empty backlog while one of them is wanted. Refile what
   is as `W-###: <title>` (`pm.md` § Writing a ticket); drop one by
   refiling it and closing it as not planned; leave the rest. A row
   with an Issue of either state is done with (`gh issue list --state
   all --search "W-### in:title"`).
4. `board.py list live-checks --bodies` — your own standing predictions,
   to see which this report confirmed or falsified.
   `./scripts/deploy.sh --check` prints the serving revision the gates
   are stated against.

**A production claim is a lead, not a finding.** Where the mechanism is
not established, run the one read-only query the auditor could not
before ticketing. A mechanism that could explain a number is not yet the
cause — say which you have.

## 2. Disposition every item

Nothing is left silent:

| Outcome | What it means |
|---|---|
| **Ticket** | a new Issue (§ 3); from a board item, `board.py promote` |
| **Raise / lower** | swap its `p` label; say why in a comment |
| **Retire / amend a check** | `board.py set ITEM --status Retired --body-file …`, evidence in the body |
| **New check** | something shipped that a future sweep must read correctly (§ 4) |
| **Route** | `core.*` → `board.py add --kind Idea --inbox scraper`, body opening `source: web-audit`; infra → `--inbox infra`, body opening `web #N <date> — <subject>` and `source: web-triage`. An item already on the board: `board.py set ITEM --inbox <repo>`, left Raw |
| **Drop** | an Issue: close as not planned, **the reason in a comment**; an item: Status Dropped, the reason in its body |
| **Leave raw** | with what would settle it, in its body |

An Idea saying the arc is the wrong shape is a `docs/PLAN.md` rewrite,
not a set of tickets. Record each item's outcome in its Status.

## 3. Tickets

An Issue from `.github/ISSUE_TEMPLATE/ticket.md`: what is wrong ·
evidence **pasted verbatim** where README's public rule allows it,
otherwise named as `AUDIT_<ts> F<n>` · acceptance that is observable ·
**out of scope**, always · source. Labels, one of each, set now:

```bash
gh issue create --title "<defect>" --body-file <file> \
  --label p3,effort:S,deploy:batched,area:templates
```

From a board item, the same body is a **public rewrite** in its own
file, under a public title (never the draft's), and the draft keeps its
evidence:

```bash
board.py promote ITEM --title "<public title>" --body-file <public.md> \
  --label p3 --label effort:S --label deploy:batched --label area:templates
```

It prints the Issue URL before setting the fields; if it stops after
that line, set them with `board.py set`, never promote again.

Priority order is the brief's. A ticket ranked high but not next gets
`not-next` and a comment: what it waits on, which to take instead. A
frozen `W-###` is refiled this way when wanted (`pm.md` § Writing a
ticket). Tickets, drops, label changes and board items need no PR;
`PLAN.md` goes in one `pm/<date>-<slug>` PR.

## 4. Checks

The four fields `pm.md` defines: **gate** (an image digest, never a date
or "after the merge"), **signature**, **reading in every direction**
including NULL/empty/error, **retire**. Status Live from day one, which
`board.py add --kind Check` sets, with the next number. Naming a ticket
id is not a check.

## 5. After the pass

Tell Paulo what changed on the Issues and the board, and what needs a
human decision. Add the last line of `board.py list inbox CoS` (the chief
of staff's count). Then clear.
