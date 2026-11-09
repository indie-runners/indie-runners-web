# W-024 — No favicon

> **Split 2026-10-22 (PM).** Paulo's elaboration of use 3 (IDEAS,
> 9daa5db) landed after this ticket and needs no asset pack: inline SVG,
> CSS only. The avatar half is now **W-028**, unblocked. This ticket is
> the favicon alone. **Unblocked 2026-10-22, see below.** Struck text below is
> kept so the split is readable.

`priority: 4` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-21 (Paulo), "New Indie Runners logo assets", use 2 (use 3 moved to W-028)`

## What is wrong

- **No favicon.** `base.html` has no icon link.
- ~~The stock avatar~~ — moved to W-028.

A logo pack now exists, so the favicon has a real asset to use.

## Unblocked 2026-10-22 — the pack is in `static/brand/`

Paulo committed the whole pack in `fc1fc5a`, served at
`/static/brand/...`. Two things in it are wrong for this repo:

- **Its README's `<head>` tags point at `/static/favicon/`**, as does
  `favicon/site.webmanifest` (`/static/favicon/icon-192.png`, `-512`).
  The files are at `/static/brand/favicon/`. Use the brand path in both.
  Do not copy files to a second location.
- **Its README suggests a `/favicon.ico` redirect route.** Take it: the
  root path is what browsers request, and acceptance 1 needs it. Use
  `methods=["GET","HEAD"]` per W-005's contract.

`build_assets.py` stays as committed. Do not run it.

## Acceptance

1. A favicon is served and referenced from `base.html`, using the
   README's suggested **icon and manifest** tags, with paths corrected.
   `GET /favicon.ico` stops 404ing (check the logs before and after).
2. ~~Stock avatars~~ — moved to W-028.
3. Verified in the browser, anon and signed-in: the tab shows the icon.
4. `docs/FILE_TREE.md` lists `static/brand/`. Changelog entry.

## Out of scope

- **Use 1, the main logo placement.** "Where is open" is Paulo's call,
  and the IDEAS entry stays raw for it.
- `og-image.png` and the README's `og:` / `twitter:` meta tags. Nobody
  asked, and they overlap W-010's SEO territory. The file sitting in
  `static/brand/social/` is not a request.
- Real-user avatars (Google photos). Unchanged.
- Stock / anonymous avatars: W-028.

## Review — 2026-10-22 (PM)

Branch `feat/favicon` at `e568f8c`.

**Sound, and within scope.** Four `<head>` tags in `base.html`, at the
brand path. The manifest is corrected in place, not copied. There is a
`/favicon.ico` route with `GET`+`HEAD` per W-005. The `og:` and
`twitter:` tags are left out as the ticket said. Leaving out
`theme-color` is the developer's own call, and the reason given is
right: it recolours mobile browser chrome, and nobody asked for that.
The changelog has a measured cost: 69 `/favicon.ico` 404s in 7 days.
All six assets and the manifest were checked with their content types,
on four pages, in both tiers. FILE_TREE is updated. Docs: 43 lines.
Merges cleanly.

**The redirect is a 307** (`RedirectResponse`'s default). That is fine
for an icon, and it keeps the route trivially reversible.

**Follow-up, not blocking:** the pack's generator and README still say
`/static/favicon/`. Regenerating and copying would reintroduce the
broken manifest. That is **W-030** (p5).

**Not verified:** the icon in a real browser tab. Nobody has looked at
one, and that is Paulo's to do after the deploy. The production 404
count is `docs/ROUTED_CHECKS.md` entry 7.

**VERDICT: APPROVED WITH FOLLOW-UPS — W-030**
