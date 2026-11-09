# PM → chief of staff, 2026-10-26 — add `indie-runners-infra` as a second route out

Paulo, 2026-10-26, in the PM terminal: *"please communicate with infra
directly by writing to her ideas file"*, then *"write a handoff to cos to
add infra as a route"*.

I did it once on his word: `indie-runners-infra` `7ac6e71`, an entry in
its `docs/IDEAS.md` answering its I-002 (W-053, hold `gcr.io` for
rollback). The briefs still allow only one outside write, so the next PM
would either refuse or cross a line. The places that say so:

- `docs/roles/pm.md:14-16`: "the scraper's `docs/IDEAS.md` — the one
  write you make outside this repo."
- `docs/roles/README.md:12`, the PM row: "appends to the scraper's
  `docs/IDEAS.md`."
- `docs/roles/README.md` § The other repo: it names two repos only. Infra
  now owns the service's shape (`indie-runners-infra/web/`, I-006), its
  domain mappings and its registry (I-002).
- `.claude/skills/triage/SKILL.md:26-27` and its `Route` row (`:55`).

Traffic already runs both ways. Infra's PM writes to our `docs/IDEAS.md`
(I-006, and the `gcr.io` entry this triage ticketed as W-053), and
infra's IDEAS header says "the PM here reads both". So far the only
route back has been "Paulo routes it", for example W-008's labels.

What the route would need to say:

- **What goes there:** Cloud Run shape, IAM grants, domain mappings,
  registries, and anything in `indie-runners-infra/web/`. Fixed by a
  plan in that repo, never by a hand grant here.
- **Format:** the one infra already uses for incoming entries:
  `## web W-### <date> — <subject>`, then a `source: web-triage` line,
  evidence quoted inline, and "commit and push there".
- **Who writes it:** the PM only, like the scraper route.

Whether the developer and auditor may route there directly, or only
through the PM, is your call.
