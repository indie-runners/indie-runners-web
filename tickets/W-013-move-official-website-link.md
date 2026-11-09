# W-013 — Move the official-website link out of the hero, above the buttons

**Priority:** 4 · **Effort:** S · **Area:** templates · **Deploy:** batched
**Source:** `docs/IDEAS.md` 2026-08-28 — Paulo

## What is wrong

Nothing is broken; this is a placement request, and it is filed as one.
The requested change is exactly:

> the event page shows the link to the official website within the hero
> image of the race. I would like this link to be moved out of the hero
> and be placed right after the events summary and before the buttons.

Today the link is the last child of `.event-hero-inner`
(`app/templates/event.html:65-69`), sitting on top of the hero photo.
The destination is inside `.event-action-bar` (`:74`), between the
`short_description` paragraph — the "events summary" — and the
`.event-attendance` block that holds the buttons.

## The one thing that makes this more than a cut and paste

**The link is styled for a photo, not for a card.** `static/css/main.css:1201`:

```css
.event-website-link {
  display: inline-block;
  font-size: 13px;
  font-weight: 500;
  color: #fff;
  border-bottom: 1px solid rgba(255,255,255,0.6);
}
```

`color: #fff` and a white underline are white-on-dark-photo styling. Moved
into the action bar unchanged, the link is white text on the card
background — invisible or near-invisible depending on that card's colour.
**A pure template move produces a page that looks correct in the diff and
is broken in the browser**, which is precisely the failure mode the
render check exists to catch. Restyle it for its new surface.

## Acceptance

1. The link renders inside `.event-action-bar`, after the
   `short_description` paragraph and before `.event-attendance`.
2. It is **gone from the hero** — moved, not duplicated.
3. **Legible on the card.** Checked in the browser against the actual
   rendered colours, not judged from the CSS.
4. **Renders when there is no summary.** `short_description` is present on
   353 of 356 events (measured 2026-08-28, `docs/ARCHITECTURE.md`), so
   three events have no summary paragraph. The link must not be nested
   inside the `{% if event.short_description %}` block or it disappears
   for exactly those three. Verify on one of them, named in the close-out.
5. **Anon and signed-in both checked.** The action bar renders different
   children per tier (`Sign in to join` vs the Going/Interested buttons),
   so "before the buttons" is a different DOM neighbourhood in each. Both
   must look right.
6. **Renders when there is no hero photo.** `tile_image_url` is
   conditional at `:21`; confirm nothing in the move depended on the photo
   being there.
7. Mobile checked — `.event-action-bar` has its own padding rule at
   `main.css:1621` and this adds a row to that card.

## Out of scope

- **The second website link, at `event.html:115`.** The TBC locked panel
  has its own "Visit the official website →" call to action, styled as a
  button (`attendance-btn locked-panel-cta`). It is a different element on
  a different surface serving a different purpose, and Paulo's request is
  about the hero. **Do not unify the two, do not move it, do not delete
  it.** If having both starts to look wrong once the hero one relocates,
  that is a `docs/IDEAS.md` note.
- **Anything else in the hero.** The badge, title, meta row and photo
  credit stay as they are.
- **The link's text, target or `rel`.** `target="_blank"` and
  `rel="noopener noreferrer"` move with it unchanged.
- **Re-thinking the action bar's layout.** One element is being inserted
  into an existing card, not redesigned around.

## Verdict

**VERDICT: APPROVED** — 2026-10-27. One commit (`c643538`) against current
master. The link is a sibling between the summary `{% if %}` and
`.event-attendance`, and it's gone from the hero. Restyled `--forest-mid`
(#2d4430) on the `#fff` card. `.event-website-link` is used nowhere else,
so nothing that still sits on a photo inherits the new colour. The render
was checked by someone who ran it, both tiers, with and without a summary,
at 1280 and 390 px. The `/proc/<pid>/cwd` check shows `dev.sh` was serving
this worktree (W-009), and a header with 0 links couldn't come from
master's code anyway. Docs: 39 lines, 1.9.39. Routed check 26.
`deploy: batched`.

**Not verified:** the signed-in state where the user is already going or
interested (`attendance-status`, "You are going · Change · Remove"). Only
the Going/Interested buttons were rendered. The link sits outside
`.event-attendance`, so the risk is spacing only. Also not verified: a hero
with no `tile_image_url` from the data, because none was found. The one
390 px shot where the photo failed to load is accidental evidence, not a
test. An event with a website but no summary rendered the link as the
card's first child (`marcs_backyard_ultra/2027`); a non-TBC event with no
summary was not rendered.
