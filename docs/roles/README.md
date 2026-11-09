# Three roles, three terminals

Ported from `indie-runners-scraper`, where the split was adopted after
three consecutive releases turned out to be corrections to the one before
— and in every case the defect was in the *reasoning*, not the
implementation. The author of a justification is the wrong person to test
its scope.

| Terminal | Brief | Model | Writes |
|---|---|---|---|
| Auditor | [auditor.md](auditor.md) | Sonnet 5, medium | `exports/reports/` only |
| PM / gatekeeper | [pm.md](pm.md) | Opus 5, high | `tickets/`, `docs/PLAN.md`, `docs/ROUTED_CHECKS.md`, `exports/evidence/`; appends to the scraper's and infra's `docs/IDEAS.md` |
| Developer | [developer.md](developer.md) | Opus 5, default | code, `docs/`, `exports/evidence/`, CSV `status` `wip` `review` `done` and `branch` |
| Chief of staff | [chief-of-staff.md](chief-of-staff.md) | Opus 5, high | `docs/roles/`, `.claude/skills/`, `CLAUDE.md`, the `ROUTED_CHECKS.md` header, replies in `docs/handoffs/` |

The fourth is not a peer of the other three. They do the work; it works
on **the thing that does the work** — the briefs, the boundaries, the
handoffs. It does not review branches, prioritise, or implement. These
briefs were **ported** from the scraper repo rather than grown here, so
expect this seat to be busier at first: a ported brief carries assumptions
from the repo it came from.

## Where things live

```
exports/reports/AUDIT_<date>T<time>.md   auditor findings   GITIGNORED
exports/evidence/W-###.md                private detail     GITIGNORED
docs/IDEAS.md                            Paulo's inbox      tracked
docs/DEV_NOTES.md                        developer drive-bys tracked
docs/ROUTED_CHECKS.md                    PM -> auditor      tracked
tickets/BACKLOG.csv                      the board          tracked
tickets/W-###-<slug>.md                  the spec the developer works from
docs/CHANGELOG.md                        where a release is declared
docs/ARCHITECTURE.md                     why a decision was made
docs/FILE_TREE.md                        what lives where
docs/handoffs/<date>-<from>-to-<to>-<slug>.md  one message   tracked
.claude/skills/<name>/SKILL.md           how each role is opened tracked
```

**A skill is how a role is opened, not what it decides.** `/audit`,
`/triage`, `/review`, `/dev-ticket` and `/cos` each start by reading this
file and the role's brief, and say the brief wins where they disagree.
They hold recipes and formats, never a rule of their own — a rule that
lives only in a skill is a brief that has drifted. A skill cannot enforce
a boundary either (the auditor's `Write` is the same tool that edits
code), so each restates the ones it cannot.

**Any role may write a handoff**: one message, read once, about the
process rather than the work. Routine coordination belongs in a durable
file instead.

**Tickets are `W-###`** so a cross-repo reference is unambiguous — the
scraper's board numbers `T-###` and findings travel between the two.

**Only the audit reports are gitignored.** A finding survives its file
being deleted: re-run the sweep. The two cross-session inboxes are
tracked, and `DEV_NOTES.md` is tracked for a reason learned the hard way
next door: under `exports/` it was invisible from a worktree, so a note
written while working never reached the branch or the reviewer.

## Single-writer per column

`tickets/BACKLOG.csv` is written by two roles:

| Column | Owner |
|---|---|
| `id` `title` `priority` `effort` `area` `deploy` `source` `notes` | PM |
| `status`: `open` at creation, `dropped` when dropping | PM |
| `status`: `wip` `review` `done`; `branch` | Developer |

`status` is split by value, so each value still has one writer: the row's
creator is the only role there to write `open`. A conflict on this file
means someone crossed the line.

## Boundaries

- **The auditor never edits `app/`.** It reads production and reports.
- **The PM has no write access to the branch it reviews.** A gatekeeper
  that can fix what it finds is a second developer whose own work nobody
  reviews.
- **One developer, one ticket, one branch.**
- **A review ends in one line.** `VERDICT: APPROVED` /
  `APPROVED WITH FOLLOW-UPS — <ids>` / `BLOCKED — <finding>`, nothing
  after it. A caveat that does not block is filed as a ticket and named
  on the line, never left as prose for the operator to weigh.
- **A verdict that predicts production is not delivered until it is in
  `docs/ROUTED_CHECKS.md`.** The auditor reads their previous report and
  that file — never a ticket verdict. A prediction left in the ticket
  reaches nobody who will look for it.
- **100 lines of `docs/` per ticket.** Whoever writes documentation —
  developer, PM, chief of staff — adds at most 100 lines under `docs/` in
  one diff: `git diff master --numstat -- docs/`, first column summed.
  `docs/` is 4886 lines and nobody reads that much; a change that needs
  more prose than that is usually two changes, or one being explained
  twice. Over budget, cut — replacing existing lines is free.
- **Nothing reaches `master` except by a merged pull request** — ruleset
  `protect master` since 2026-11-09, no bypass, Paulo included. Merge
  commits only; check `build` (workflow `ci`) green on a branch up to
  date with `master`. Every write: `git pull --ff-only` on `master`,
  branch, commit, push, `gh pr create --base master`.
  - **A ticket** (`fix/<slug>`) merges on the PM's approving line, which
    is the gate: GitHub cannot record it as an approval, the same
    account opens every PR. The developer runs `gh pr merge --merge`.
    Paulo's production gates stay `deploy:` and migrations.
  - **Board-only work** — one PM session's tickets, specs and
    `ROUTED_CHECKS.md`; one CoS pass; an operator ticket's `done` — is
    one PR (`pm/<date>-<slug>`, `cos/<date>-<slug>`, `done/W-###`),
    merged by whoever opened it once `build` is green. Nobody reviewed
    these before; a PR per edit would only multiply the next item.
  - **Behind `master`**, whoever opened the PR runs `git fetch origin &&
    git merge origin/master && git push`, then waits for `build`. Merge,
    not rebase: rebased commits are not the ones the PM read.
  - The scraper's and infra's `docs/IDEAS.md` still take direct pushes
    until those repos get the ruleset.
- **Tracked files, PR bodies and PR comments are public, in all three
  repos.** Never write into a tracked file: real user names, crew names or slugs, user IDs tied to
  privacy settings, user/signup/traffic counts, visitor logs or search
  terms, pasted IAM policy or registry output, descriptions of unfixed
  privilege weaknesses, local machine paths, or any line tying a
  person's email to an admin/Owner role. GCP project ID, Cloud SQL name,
  bucket and service account names are public on purpose and may stay,
  and so does `core.*` race data. The tracked file says what was checked
  and the result; the detail goes to one of two gitignored files in the
  main checkout's `exports/`, cited by name, never by path:
  - an audit finding: `reports/AUDIT_<ts>.md`, cited `AUDIT_<ts> F<n>`;
  - anything else, such as a developer's "Verified" output or a PM's
    measurement: `evidence/W-###.md`, cited `evidence W-###`. Whichever
    role holds the detail appends a dated section and never edits one.

  From a worktree, the main checkout is the first line of
  `git worktree list`. **Names:** "user A", "crew A" in prose,
  `<crew-a>` in a URL or slug; letters are per file, the same letter
  for the same one throughout it. **The cost, accepted:** a gitignored
  file has no history, is not in a worktree's tree, cannot be read by
  claude.ai or the other repos, and is gone with the machine. So the
  tracked file must stand on its own; the private one is for checking
  again, not for understanding.
- **Deploy is a decision, not a reflex** — `deploy: immediate | batched`,
  set when the ticket is written. This service is public.

## The other repo

`indie-runners-scraper` owns `core.*` — **schema and content**. This
service reads four objects — `core.v_denormalized_event_data_upcoming`,
`core.mv_denormalized_event_data`, `core.events`,
`core.event_occurrences` (`app/main.py`, `ProfileService`) — and never
writes to any (`app/models/core.py`, marked READ ONLY). This repo owns
`web.*`.

| Finding | Fixed by |
|---|---|
| `core.*` content or shape wrong | **the scraper repo** — always |
| This app misreading correct data | here |
| `web.*` schema or behaviour | here |
| Cloud Run shape, IAM, domain mappings, registries | **the infra repo** |

**This repo is the best-placed observer of `core.*` and the least able to
fix it.** It reads the serving view on every page load. So a `core.*`
finding is routed to the scraper repo's `docs/IDEAS.md` with
`source: web-audit` — never ticketed here, where no developer will do it.

**The public rule holds across the boundary.** The other repos cannot
read this one's `exports/`, so a cited `web AUDIT_<ts> F<n>` is only a
pointer back to us. The entry must stand on its own: what was checked,
how to observe it from their side, and the result. `core.*` race data
(events, ids, values) may be quoted; user data never.

**`indie-runners-infra` is the second route out.** It owns this service's
shape (`indie-runners-infra/web/`), its grants, domain mappings and
registry, fixed by a plan there, never by a hand grant here. The entry
goes to its `docs/IDEAS.md` as `## web W-### <date> — <subject>`, then
`source: web-triage`, under the same rule; commit and push there. Its
PM already reads ours, so traffic runs both ways.

**Only the PM writes to either repo.** The auditor marks the finding
`Routes to:` with the entry ready to paste; the developer leaves a
drive-by. One writer means one place to look for what was sent.

**One connection budget, two repos.** 45 connections serve the scraper's
pipelines, this service, and anything an operator runs. "Only one session
runs DB-touching work at a time" is a rule across **both** repos.

## When to clear a session

Clear when the durable files hold everything that matters; do not when
they do not.

| Role | Clear | Never clear |
|---|---|---|
| Auditor | every sweep | — |
| PM | per triage pass; after a review | mid-review |
| Developer | per ticket | mid-ticket |

**A long context is not itself a reason to clear.** Drift is — a session
answering from what it remembers rather than what it just read.
**`/loop` does not clear**: it re-sends the prompt while context keeps
growing, so a looping role still needs clearing by hand.
