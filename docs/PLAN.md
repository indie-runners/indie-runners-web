# Plan: The race list

> The PM's plan of record. Rewritten 2026-11-25. The previous arc, crew
> growth (2026-11-17), is complete: #51, #52, #53 and #64 shipped. It is
> in git history.

## Why this arc

Paulo chose it at triage on 2026-11-25, over sign-in without a Google
account and GPX courses. Its input is his idea of the same day, which
answers an earlier one from founder feedback (both on the board).

The list puts races with people going or interested first. That worked
for a handful of races; now enough have activity that the list is no
longer in date order, and the large photos leave few races on a screen.

The outcome, when the arc is done: the list reads in date order, a reader
can narrow it to races where people are going or interested, and a
signed-in reader can see it as compact rows.

## Order

One at a time, in this order. Each step ships on its own.

| # | Ticket | Why here |
|---|---|---|
| 1 | **#85** date order and activity filter | One Issue: only 60 events show, so in date order a later race with people going leaves the page, and the filter is how it is found. |
| 2 | **#86** List/Cards toggle | Draws the results #85 decides. `not-next` until #85 merges. |

Both are `p3`. The other open Issues run on their labels and fit between
steps.

## What this arc excludes

- **Remembering the view per user.** Paulo, 2026-11-25: cards is the
  default and `?view=list` is the list. Nothing is stored, so no
  migration and no privacy-page change.
- **The toggle for signed-out visitors:** they always see cards.
- **Paging, or a limit other than 60.**
- **"Recently added" and "hot races" carousels:** when activity is dense
  enough to change weekly.
- **Sign-in without Google, and email of any kind:** a magic link, the
  crew digest and an email on Going need one sender first (provider, DNS
  records, the privacy page).
- **GPX courses:** waiting on a page design from claude.ai.
- **A shareable season page, a race map, a featured-races page:** raw on
  the board, each with what would settle it.

## Standing rules this arc keeps

- **`deploy: batched`** unless Paulo says otherwise on a ticket.
- **Who is counted and who is named do not change.** A count includes
  every attendee; visibility decides only the names. A compact row shows
  no name its card would not.
- **No migration.** A step that needs DDL was mis-scoped.
- **One connection budget, two repos.** No new query per tile or row.
- **No test suite.** Each ticket is verified by running it, signed out
  and signed in, at phone and desktop width.
- **Close-out:** the changelog carries the wrong belief, its cost, the new
  belief and the evidence; FILE_TREE for new files.
