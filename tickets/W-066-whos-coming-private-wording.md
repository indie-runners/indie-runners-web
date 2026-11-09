# W-066 — "Who's coming" reads "and 1 other" when nobody is named above it

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-28 (Paulo)`

## What is wrong

Signed in, each who's-coming column lists public attendees, then
`and N other(s)` for the private ones (`event.html:461-462`, `481-482`).
When every attendee in a column is private the list is empty, and the
line reads as if it continued one.

Paulo, from `docs/IDEAS.md`:

> when there is one private user who is going, it shows as "and 1 other" .
>
> Who's coming
> Going
>
> and 1 other
> Interested
>
>     Paulo Morales Castillo
>
> whenever there is only one person, a particular message should be shown.
> jJSomthing like 1 indie runner is going. when there are 2 privates, then
> 2 indie runners are going. where there is one public and 2 privates, then
> e.g. juan castillo and 2 other indie runners are going.

## Acceptance

The line under each column, by case (N = hidden count, verb = `going` or
`interested` by column):

| Named rows above | N | Line |
|---|---|---|
| none | 1 | `1 indie runner is going` |
| none | 2+ | `N indie runners are going` |
| 1+ | 1 | `and 1 other indie runner are going` (see note) |
| 1+ | 2+ | `and N other indie runners are going` |
| any | 0 | no line (unchanged) |

Note: with names above, the subject is "Juan Castillo and 1 other indie
runner", so the verb is `are`. If that reads wrong on the page, show
Paulo both and record his pick in the changelog. Don't invent a third.

1. All five rows rendered in the browser, signed in, for both columns,
   quoted in the changelog. A hidden-only column needs a private test
   user; say how you made one.
2. Signed-out render unchanged (the avatar row).

## Out of scope

- The anon row's screen-reader count, W-063. If you settle a wording here,
  name it there as a candidate; don't do W-063 in this branch.
- Showing private attendees in any other way, or changing who is private.
- The avatar colours (`% 4` signed in vs W-028's `% 5` anon).

## Verdict

**VERDICT: APPROVED** — 2026-10-28. The changelog names the wrong belief
(the hidden line always continues a list), its cost and the new rule. One
`hidden_line` macro serves both columns. The diff is the template, plus one
ARCHITECTURE sentence that now quotes the new wording; the "worded the same
for `private` and `crews_only`" claim still holds, because the macro only
sees a count. The viewer can't be the hidden one: `_is_identity_visible`
always shows the viewer to themselves. Verified by the developer from this
worktree on :8000 (`/proc/<pid>/cwd`), with a minted cookie for user 1 and
anon. All five rows were quoted for both columns. Interested 1+0 wasn't
quoted, but it runs the same macro arm as going 1+0. The developer kept
`and 1 other indie runner are going` under the ticket's note. Docs: 47
lines. No FILE_TREE change. Ticket is `deploy: batched`.

**Not verified:** real sign-in (minted cookie). A hidden attendee who is
`crews_only`-blocked rather than `private`: same counter and same line, but
only `private` was rendered. The states were made by driving existing users
12, 13 and 17 through the attend/clear routes in the shared database, not a
test user. Three mistaken rows on past dates were deleted by hand. That's
recorded in the changelog and raised with Paulo, not settled here.
