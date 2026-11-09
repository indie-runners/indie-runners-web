# W-067 — The footer has no GitHub link

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-28 (Paulo)`

## What is wrong

Paulo, from `docs/IDEAS.md`:

> next to the strava, instagram symbols, include github and the link to our
> github organization: https://github.com/indie-runners

The footer's social row is `app/templates/base.html:68-71` (W-050).

## Decision — settled

**Paulo, 2026-10-28: ship it with the next batched deploy.** An empty org
page until the public flip is fine. The paragraph below is the context.

At triage (2026-10-28) the org page answers 200 and lists **0 public
repositories** (`GET api.github.com/orgs/indie-runners/repos?type=public`
→ `[]`). This repo stays private until W-060's settings and GitHub Support
4914411 are done. Linking now sends visitors to an empty org page. Paulo
chose the first of: ship with the next batched deploy, or wait for W-060's flip.

## Acceptance

1. A third link in `.footer-social`, after Instagram:
   `href="https://github.com/indie-runners"`, `target="_blank"`,
   `rel="noopener noreferrer"`, `aria-label="Indie Runners on GitHub"`,
   `<img src="/static/icons/github.svg" alt="" aria-hidden="true" width="24" height="24">`,
   as its two neighbours do.
2. The glyph is GitHub's own mark, from GitHub's logo page
   (https://github.com/logos), unmodified, in a colour that page allows.
   Name the URL in the changelog.
3. `GET /static/icons/github.svg` returns `200 image/svg+xml` locally.
4. Checked in the browser on `/` and one event page, signed out and signed
   in, desktop and phone width.

## Out of scope

- Strava and Instagram links (unchanged).
- A README or anything on the GitHub side. The public flip is W-058 to
  W-060.

## Verdict

**VERDICT: APPROVED** — 2026-10-30. All four acceptance items met.
`static/icons/github.svg` is byte-identical to `GitHub_Invertocat_White.svg`
in https://brand.github.com/GitHub_Logos.zip (sha256 `ccd84c89…d47b`,
fetched at review). Markup matches its two neighbours attribute for
attribute. Browser check: `/` and an event page, anon and signed in (minted
cookie), 1280 and 390 px, this worktree's server confirmed via
`/proc/<pid>/cwd`. Docs 27 added lines. `deploy: batched`. Routed check 34.
The file is committed `100755`. `StaticFiles` ignores the mode, so nothing
to fix.

**Not verified:** a real click through to github.com, and hover/focus state
in a real browser (screenshots were headless). The org page shows no
public repository until W-058 to W-060; Paulo accepted that on 2026-10-28.
