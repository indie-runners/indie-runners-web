# W-050 — The footer names Strava and Instagram in words, wanted as their logos on a row of their own

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-26 (Paulo, after W-046 merged)`

## What is wrong

Paulo, from `docs/IDEAS.md`:

> "could we show the actual instagram and strava simbols instead of saying
> strava instragram? I would like for them to go below the indie runners
> imprint privacy terms"

W-046 (1.9.31) put two text links at the end of the one footer row,
`app/templates/base.html:62-70`:

```html
<footer>
  <span>&copy; 2026 Indie Runners</span>
  <a href="/imprint">Imprint</a>
  ...
  <a href="https://www.strava.com/clubs/2244858" target="_blank" rel="noopener noreferrer">Strava</a>
  <a href="https://www.instagram.com/weareindierunners/" target="_blank" rel="noopener noreferrer">Instagram</a>
</footer>
```

W-046 left out icons on purpose, because both companies publish brand
rules. Paulo now wants the icons, so this ticket has to follow those rules.

## Acceptance

1. The two links sit on their own row **below** the existing footer row,
   and each shows its company's glyph instead of the word. The hrefs,
   `target` and `rel` are exactly as W-046 shipped them.
2. Each glyph is used unmodified, from the company's own brand-resource
   page, in a colour that page allows. Name both source URLs in the
   changelog. The Strava path in `mockup_reference.html:21` is a
   candidate, but check it against Strava's page. The repo has no
   Instagram glyph: `static/brand/instagram/` holds our own profile
   picture.
   *PM amendment 2026-10-26, at review:* Strava publishes no bare mark
   (DEV_NOTES 2026-10-26, while on W-050). Paulo chose route (a),
   according to the developer's TODO: ship the CC0 Simple Icons chevron
   and name the gap in the changelog. For Strava, this replaces
   "unmodified, from the company's own page".
3. Each link keeps an accessible name ("Indie Runners on Strava", "…on
   Instagram"), via `aria-label` or visually hidden text, and the SVG is
   `aria-hidden`. Each tap target is at least 24×24 CSS px.
4. Checked in the browser on `/`, an event page and `/stats`, signed out
   and signed in, at desktop and phone width.

## Out of scope

- Other networks, and links anywhere but the footer (as in W-046).
- Restyling the first footer row.
- The brand pack (`static/brand/build_assets.py`). W-030 owns that.

Routed check 22 (W-046, pending deploy) reads the hrefs and `rel`, and
this ticket keeps both, so 22 stays valid whichever ships first. Don't
retire 22 on the strength of this ticket.

## Verdict

**VERDICT: APPROVED** — 2026-10-26. The hrefs, `target` and `rel` are
byte-for-byte W-046's, so check 22 holds. Read in the diff: `footer` is
already `flex-wrap: wrap`, so `flex-basis: 100%` puts the row underneath.
The `<img>`s are 24×24 and `display: block`, so each `<a>` target is
24×24. White on `--forest`. Instagram is Meta's file, `cmp`-identical,
loaded through `<img>`, so its embedded `.cls-1` style can't leak.
Changelog 1.9.33 names the wrong belief (the ticket's) and both sources.
FILE_TREE is updated. Docs 39 lines. `deploy: batched`. Routed check 24.

Acceptance 2 was falsified for Strava and re-decided, not rescoped
silently: amended above. The changelog cites "DEV_NOTES 2026-10-26" for
Paulo's choice, but that entry only asks the question. The answer is in
the TODO. I annotated the note on master.

**Not verified:**
- Meta's size and colour rules for the glyph. Its brand page
  (fetched 2026-10-26) states neither and links them from "Brand
  Elements", which I did not open. If that sets a minimum above 24 px,
  the size is wrong.
- That the footer counts as Meta's "Follow us on…" exception to
  "Don't mention other social networks in the same spot". It has no such
  words. I read an icon lineup as that call to action, the way the
  changelog does.
- A screen reader (developer, said). A signed-in screenshot: the
  markup was compared, and `base.html` is shared.
- Whether Strava objects to a third-party chevron. That risk was
  accepted by Paulo's choice, not removed.
