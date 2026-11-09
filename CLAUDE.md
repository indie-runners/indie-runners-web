# indie-runners-web

FastAPI + server-rendered Jinja app behind indierunners.co (Cloud Run,
europe-west1). Reads race data from `core.*` (owned by indie-runners-scraper,
read-only here); owns `web.*`.

## Before anything else

1. Read `docs/roles/README.md` — roles, boundaries, the two-repo split.
2. If this terminal has a role (auditor, PM, developer, chief of staff),
   read `docs/roles/<role>.md`. It overrides general habits.
3. No role given? Ask which one, or work as the developer.

## Standing rules

- Never run a SQL migration without Paulo's explicit approval. Writing
  the file is fine.
- `core.*` is read-only. Wrong data routes to the scraper's `docs/IDEAS.md`.
- One DB-touching session at a time, across both repos (45 shared
  connections).
- No test suite. Verify by running it (`bash scripts/dev.sh`), both anon
  and signed-in tiers.
- Don't create a `.venv` — Paulo uses PyCharm's interpreter.
- Default branch is `master`. Nothing reaches it except by a merged pull
  request (merge commits only, check `build` green, branch up to date;
  README § Boundaries). Merging does not deploy: `scripts/deploy.sh`
  builds from local `master`, so `git pull --ff-only` first. claude.ai
  reads this repo from GitHub. Deploy only when the ticket says
  `deploy: immediate`.
- At most 100 added lines under `docs/` per ticket.

## Ideas from claude.ai

Paulo shapes ideas in claude.ai and brings them back as entries for
`docs/IDEAS.md`. When asked to add one, append it verbatim — don't
reorganise, rank or ticket it. If it carries something README's public
rule forbids, ask Paulo before appending.

## Ponytail

The ponytail plugin is installed. Use it for the developer role:
the smallest change that fully solves the ticket. It does not
override the role briefs. Changelog entries still carry the full
reasoning (wrong belief, cost, new belief, evidence), and
`shortcut:` comments are drive-bys, so they also go to
`docs/DEV_NOTES.md`. PM, auditor and chief of staff work don't use it.
