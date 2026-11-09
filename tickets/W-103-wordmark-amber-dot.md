# W-103 — The header wordmark's "i" has a white dot; the brand mark's is amber

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-11-04 (Paulo, up in priority)`

## What is wrong

Paulo, from `docs/IDEAS.md`:

> the letter i in the header logo should have its dot in the yellow
> colour, just like the logo in `static/brand/`.

```
app/templates/base.html:24   <span class="logo-name">Indie Runners</span>
static/css/main.css:58-61    .logo-name { font-family: 'Fraunces', serif; font-size: 22px; font-weight: 700; ...
```

The brand amber is `--accent`, `#e8a44a`. The only lowercase i in the
wordmark is the one in "Indie".

## Acceptance

1. In the header, the dot of the "i" in "Indie" is amber and its stem is
   white, on desktop and at 375px. Screenshot both in the changelog.
2. The page text stays "Indie Runners": copy-paste, the accessible name
   and search all read it unchanged.
3. Default, veto at review: the entry's option 1 (colour only the top of
   that letter). The developer names the cut-off and how it scales with
   the font size.
4. Header colour only: the footer's "© 2026 Indie Runners" and the
   `<title>` are unchanged. Both tiers render.

## Out of scope

- An SVG wordmark (option 3), and any change to `static/brand/`.
- Where the main logo goes on the page (IDEAS 2026-10-21, still raw).

## Verdict

**VERDICT: APPROVED** — 2026-11-04. Reviewed `4db3832`. Option 1 as
defaulted, cut-off 0.48em named with its measurement and how it scales. No
media query changes the wordmark's 22px, so "every width" holds. Both tiers
rendered from the worktree, `/proc` cwd checked. Screenshots match the claim.
Reviewer re-rendered the wordmark in Chrome with `--force-high-contrast`: the
"i" takes the forced link colour like the rest, so it does not vanish. Docs
39 lines. Ticket is `deploy: batched`. Routed check 54.

**Not verified:**
- Firefox and Safari. Only Chrome rendered the clipped gradient. One look at
  the header in each would settle it.
- The fallback serif, if Fraunces fails to load: the dot may straddle the
  cut-off. Both colours read on the forest green, so it stays legible.
- Copy-paste and page search by hand; `textContent` is the evidence.
