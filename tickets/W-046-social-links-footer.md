# W-046 — The site links neither the Strava club nor the Instagram account

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-24 (Paulo, priority 3)`

## What is wrong

Paulo, from `docs/IDEAS.md`:

> *"please put links to the strava profile and instagram account of
> indie runners in the website."* Instagram:
> https://www.instagram.com/weareindierunners/ · Strava club:
> https://www.strava.com/clubs/2244858

No page links either. The one element on every page is the footer,
`app/templates/base.html:62-68`:

```html
<footer>
  <span>&copy; 2026 Indie Runners</span>
  <a href="/imprint">Imprint</a>
  <a href="/privacy">Privacy</a>
  <a href="/terms">Terms</a>
  <a href="/stats">Stats</a>
</footer>
```

## Acceptance

1. The footer carries two links, labelled "Strava" and "Instagram", to
   exactly the two URLs above. Each opens in a new tab with
   `rel="noopener noreferrer"`, the shape the event page's official
   website link already uses.
2. Checked in the browser on `/`, an event page and `/stats`, signed out
   and signed in, at desktop and phone width. The footer must not wrap
   badly at phone width.
3. Both URLs return a page when clicked (no typo in the club id).

## Out of scope

- Icons or brand marks. Strava and Instagram each have brand rules, and
  a text link needs none of them.
- Links anywhere but the footer (header, event pages, profiles).
- `sameAs` / schema.org markup and Open Graph tags. Nobody asked, and
  they are SEO work with their own checks.

## Verdict

**VERDICT: APPROVED** — 2026-10-26. Two `<a>` lines in `base.html`. They
use the same `target`/`rel` shape as `event.html:66`, the URLs are exactly
the ones in the ticket, and there are no icons. The developer's render
check covered all six page/tier pairs (anon and a minted cookie, with
`nav-user-menu` telling the tiers apart) and ran from the worktree
(`/proc/<pid>/cwd`), so the W-009 trap is ruled out. Changelog 1.9.31.
The docs diff is 26 lines. No file was added, so FILE_TREE needs no
change. `deploy: batched`.

**Not verified:** the phone-width screenshot covered `/stats` and the
event page but not `/`. The footer is the same `base.html` block on
every page, so this is accepted. Nobody clicked through in a real
signed-in browser or on a real phone. Strava answers 403 to curl and to
headless Chrome, so a scripted check of that URL cannot tell a typo from
the bot wall. Only a browser can (the developer saw 200 with browser
headers). I did not re-run the server myself. The production check is
routed check 22.
