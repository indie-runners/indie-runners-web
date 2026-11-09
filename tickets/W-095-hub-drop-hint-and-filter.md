# W-095 — Crew hub: drop the small-crew hint and the Going-only filter

`priority: 2` · `effort: S` · `area: crews` · `deploy: immediate`
`source: docs/IDEAS.md 2026-11-02 (Paulo), two entries`

## What is wrong

Paulo asked for two things off the crew hub, both on 2026-11-02:

> "Small crews may reveal who is going — larger crews give more
> anonymity." Remove that please.

> Going and interested / Going only filter button on crew hub, that can go.

## Evidence

```
app/templates/crews_detail.html:42  <div class="crew-view" role="group" aria-label="Agenda filter">
app/templates/crews_detail.html:43    <a href="/crews/{{ crew.slug }}" ...>Going and interested</a>
app/templates/crews_detail.html:44    <a href="/crews/{{ crew.slug }}?view=going" ...>Going only</a>
app/templates/crews_detail.html:116   Small crews may reveal who is going — larger crews give more anonymity.
app/main.py:794                       going_only = view == "going"
app/main.py:801                       "agenda": svc.list_agenda(crew.id, current_user.id, going_only),
```

`going_only` also gates the legend's Interested chip, the row's
interested chips and the empty-state copy in the same template.
`docs/ARCHITECTURE.md:205` documents `?view=going`; `:209` documents the
hint and already allows for removing it.

## Acceptance

1. The hub shows no filter links and no small-crew hint, at any member
   count.
2. Going and interested members both show on every row, with both
   legend chips. The empty state reads "No races on the crew's calendar
   yet."
3. `going_only` and the `view` parameter are gone from the route and
   from `list_agenda`. `/crews/<slug>?view=going` renders the full hub
   (the parameter is ignored), not an error.
4. ARCHITECTURE :205 and :209 say what the page does now. The
   small-crew leak paragraph keeps its reasoning and says the hint was
   removed on Paulo's word.
5. Verified signed-in as a member of a crew under 4 members. Anon: the
   crew URL still behaves as before (W-085's territory, unchanged here).

## Out of scope

- The leak itself: removing the hint does not change what a count
  reveals. ARCHITECTURE already says so.
- The members box, invite, leave and remove (W-080 to W-082).

## Verdict

**VERDICT: BLOCKED — R1, R2** — 2026-11-03. Branch
`fix/hub-drop-hint-and-filter` (`d4c7ad7`), changelog 1.9.62.

The code is right and complete. No caller of `list_agenda`, `going_only`,
`.crew-view` or `.crew-small-hint` survives. `member_count` in
`profile.html` is a separate loop variable. Verified from the worktree
(`/proc/<pid>/cwd`), signed in to two crews under 4 members, and
`?view=going` gives a byte-identical body. Docs diff is 37 lines. It is
one ticket. The block is on the record, not the change.

**R1. The changelog's wrong belief and the new ARCHITECTURE sentence
misattribute where both features came from.** The changelog says "Both
were W-077 design, not asks". ARCHITECTURE:209 says the hint was shown
"from W-077 to 1.9.61". Neither is true:

- The filter was Paulo's ask. His Crews v1 spec (IDEAS § Crews v1) reads:
  `Toggle: "Going only" / "Going and interested". Default is going and
  interested.` W-077 built what the spec said.
- The hint predates W-077. It shipped in phase 3 PR3 (`f777c87`,
  2026-07-17), and ARCHITECTURE has documented it as a design choice
  since.

So the wrong belief is not "W-077 added things nobody asked for". It is
Paulo's own spec item and a July design choice, both judged unneeded once
the hub was in use. "A page whose agenda rarely has enough rows to filter"
is also stated without a count: measure it or drop it. A reader in three
months would take the current text as evidence that W-077 overreached.
Fix: rewrite the changelog's first bullet and ARCHITECTURE:209's date
range to the history above.

**R2. TODO line 9 says "Anon: 307 to Google as before".** The code raises
401 in `get_required_user`, and the changelog says 401 correctly. A
verification line that names a result nobody got is the artefact a review
reads. Fix it to 401 in the same commit.

**Not verified:**
- The empty state. No crew has zero marked races, so "No races on the
  crew's calendar yet." has not rendered since its branch was removed.
- The render was checked by HTML in curl, not looked at in a browser, at
  desktop or 375px. The change only removes a block and its CSS.
- ARCHITECTURE:205 still says an anon visitor "bounces to Google". That
  is pre-existing and already W-085's, not this branch's.

**Routed check:** none at this verdict. Written when it is approved.

## Verdict (re-review)

**VERDICT: APPROVED** — 2026-11-03. Branch `fix/hub-drop-hint-and-filter`
(`d4c7ad7`, `b36e439`), changelog 1.9.62. Docs diff 39 lines.
`deploy: immediate`. Routed as check 46.

R1 resolved. The changelog credits the filter to Paulo's Crews v1 spec
and the hint to phase 3 PR3 (`f777c87`, 2026-07-17). ARCHITECTURE:209
dates the hint the same way. The unmeasured "rarely has enough rows"
claim is gone. R2 resolved. The TODO's anon result now reads 401, which
matches `get_required_user`. No code changed since the block.

**Not verified:** unchanged from the first verdict. The empty state has
not rendered, and the hub was read as HTML in curl, not looked at in a
browser.
