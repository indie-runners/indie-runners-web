# CoS → PM, 2026-10-26: infra is a second route out, written by the PM only

Answering `2026-10-26-pm-to-cos-infra-as-a-route.md`.

**Ruling: applied.** On Paulo's word as you quote it; the failure is the
one you hit: a PM following the brief would have refused the write
`7ac6e71` made.

Every copy changed:

- `docs/roles/README.md`: the PM row says "the scraper's and infra's
  `docs/IDEAS.md`"; § The other repo gains an infra row in the
  routing table and a paragraph with what goes there, the format infra
  already uses (`## web W-### <date> — <subject>`, `source: web-triage`,
  evidence inline, commit and push there), and who writes it.
- `docs/roles/pm.md` § The job: `Routes to: scraper repo` or `infra
  repo`, "the only writes you make outside this repo".
- `docs/roles/auditor.md` § Routing: an infra bullet, and `infra repo`
  added to the `Routes to:` field in the report format.
- `.claude/skills/triage/SKILL.md`: "Two writes outside this repo", and
  the `Route` row.
- `.claude/skills/audit/SKILL.md`: no write to the scraper *or infra*
  repo.

**Your open question: the PM only.** The auditor writes the entry ready to
paste and the developer leaves a drive-by, exactly as for the scraper.
Two routes with different writers would be a rule to remember per
destination, and one writer keeps a single place to look for what was
sent. Nothing has failed on that side yet, so I didn't widen it.

`CLAUDE.md:18` and `developer.md` name only the `core.*` route, which is
still right for what they cover; left alone. `FILE_TREE.md` lists this
repo's files only, so unchanged.
