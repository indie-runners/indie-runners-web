# Plan: Crew growth

> The PM's plan of record. Rewritten 2026-11-17. The previous arc, Crews
> v1 (2026-10-31, complete 2026-11-04), is in git history. Between the two
> arcs the board ran on the Issues' labels.

## Why this arc

Paulo chose it at triage on 2026-11-17, from three candidates: crew
growth, GPX courses (shaped on the board, waiting on a page design from
claude.ai) and sign-in without a Google account. Its inputs are a
marketing session's ideas (board, 2026-11-17) and founder feedback
carried by the scraper analyst (2026-11-16).

Growth so far has come crew by crew. Almost every new user arrives
through a crew invite link pasted into a group chat, and the second crew
was started, unprompted, by a member of the first who also runs with
another group. **Goal: more crews of five or more members, started by
someone other than Paulo.**

The outcome, when the arc is done: a person handed an invite link sees
which crew it is before Google asks for their account; we can count which
links and invites bring people in; and a member who runs with another
group is invited to start a crew for it.

## Order

One at a time, in this order. Each step ships on its own.

| # | Ticket | Why here |
|---|---|---|
| 1 | **#51** growth numbers | Baseline first: numbers taken after the invite page ships cannot show what it changed. Read-only, nothing to deploy. |
| 2 | **#52** invite page before sign-in | The main entrance. Paulo, 2026-11-17: name, member count and planned races, link previews included. |
| 3 | **#53** signup source | Ties each signup to a link or an invite. The arc's only migration. Extends #51 with the split by source. |
| 4 | create-a-crew entry point | Raw on the board, two entries that are one decision. Ticketed when #52 ships, once Paulo names the placement. |

The arc's tickets are `p2`, so they come before the open `p3`s. Two
exceptions. **#35** (OAuth `state`) touches the same callback as #53:
whichever goes second reads the first's diff before starting. **#50**
(commit label) is `not-next`, waiting on infra I-016's apply. **#54**
(a stale ARCHITECTURE line) is docs-only and fits between steps.

## What this arc excludes

- **Email of any kind:** the crew digest, an email on Going, a magic-link
  sign-in. All three need one sender first (provider, DNS records, the
  privacy page), and none has been chosen.
- **Sign-in without Google:** the likely next candidate. It is not a cap
  emergency, because the consent screen is in Production (Paulo,
  2026-11-17; #54).
- **A shareable season page:** a hand-made test in group chats comes
  first, then Paulo's yes to a public, opt-in exception to anonymous
  profiles.
- **GPX courses, a homepage redesign, a race map, a featured-races page,
  short links:** raw on the board, each with what would settle it.
- **Registration status for signed-out visitors:** dropped. Paulo keeps
  every race detail behind sign-in.

## Standing rules this arc keeps

- **`deploy: batched`** unless Paulo says otherwise on a ticket. Crews
  v1's every-step-immediate rule was his word for that arc and is not
  carried over.
- **#53's migration is written by the developer and applied by Paulo**,
  before the deploy that writes to it. Any other step that needs DDL was
  mis-scoped.
- **The arc's measure stays out of the repo.** #51 prints user and crew
  counts. They go to `evidence #N`, never into a PR, a changelog or an
  Issue (README § Boundaries).
- **What the app shows or stores changes twice:** #52 shows crew facts to
  people who are not signed in, and #53 stores a source on the account.
  Each updates `docs/ARCHITECTURE.md` and, for #53, `privacy.html` in the
  same PR.
- **One connection budget, two repos.** **No test suite.** Each ticket is
  verified by running it, signed out and signed in.
- **Close-out:** the changelog carries the wrong belief, its cost, the new
  belief and the evidence; FILE_TREE for new files.
