# W-086 — The hub never invites a member to add their own races

`priority: 2` · `effort: S` · `area: templates` · `deploy: immediate`
`source: Paulo 2026-10-31 (terminal, after the W-077 review)`

**Crews arc.** After W-077 is merged, before W-078 (Paulo 2026-10-31). See `docs/PLAN.md`.

## What is wrong

The hub lists races members have already marked. The only path to marking
a new one is the empty state's "Find a race" link, which disappears as soon
as the crew has one mark. A member looking at a populated hub has to work
out for themselves that races are added from the index, then find their
way there.

## Evidence

Paulo, 2026-10-31: *"Something that is missing is a possibility and
invitation for members to search for their own events. Without them having
to figure out that they have to go back to index."*

`crews_detail.html` on `fix/crew-hub-agenda`: the `/` link sits only in
the `{% else %}` branch of `{% if agenda %}`.

The index already searches: `GET /?search=<term>` matches event name,
display name, race location and terrain (`race_service.py:231-240`), the
same input as `index.html:16`.

## Acceptance

1. Every hub render, populated or empty, carries one line of invitation
   and a search box: a plain `<form method="get" action="/">` with an
   input named `search`. Submitting lands on the index filtered by the
   term. No JS, no new route.
2. The invitation says what to do there, in one sentence: find the race,
   mark Going or Interested, and it shows up on the hub.
3. The empty state keeps its message and loses its now-duplicate link (or
   the two merge); no page shows two "find a race" prompts.
4. It sits at the top of the agenda column, so it's above the fold at 375px
   too.
5. Verified signed in, at desktop and 375px, on a populated hub and on the
   empty state; a search for a term from a live event lands on a filtered
   index.

## Out of scope

- Search results inside the hub, autocomplete, or marking from the hub:
  each needs a route or JS; the index already does the work.
- Getting back to the hub after marking: W-078's Crews nav link.
- The toggle on agenda rows: W-079.

## Verdict

**VERDICT: APPROVED** — 2026-10-31. One template change, no route, no read.
The 1.9.52 entry names the wrong belief (the empty-state link was a path) and
why it stopped holding the moment one mark existed. The verification served
this worktree (`/proc/<pid>/cwd`, so not the W-009 trap): signed in, populated
(`<crew>`, 8 rows) and empty state (`<crew-b>?view=going`), 1280 and 375 px.
The form is a plain GET with `name="search"`, so a submit is literally the
`/?search=Kullamannen` the developer fetched: one tile against 60. Anon gets the
401 that W-085 covers. Docs: 32 lines. No contract change, so ARCHITECTURE is
untouched; no new file.

No routed check: the hub runs the same reads as under check 38, and nothing
here can 5xx that check 38 doesn't already catch.

**Not verified:** the form was never clicked. The screenshots are headless
Chrome on fetched HTML, and the submit is inferred from GET semantics.
`type="search"` on iOS Safari, where the native search appearance can override
`.filter-input`'s border and radius, was not seen (Chrome only). A search term
that matches nothing lands on the index's existing empty result, which is
outside this ticket and was not looked at.
