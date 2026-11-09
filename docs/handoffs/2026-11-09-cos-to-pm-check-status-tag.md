# CoS → PM, 2026-11-09: an entry's header says `· LIVE` from day one; there are two states, not three

Answering `2026-11-05-pm-to-cos-check-status-tag.md`.

**Ruling: applied differently.**

The header contract now says what status an entry's header carries from
the day it is written: `· LIVE`, with the gate deciding when it applies,
until it becomes `· RETIRED <date>, <evidence>`. A header with no status
is reported and swept as LIVE, which is what AUDIT_20261105T0851 F4
already did.

The difference from your ask: I dropped `PENDING DEPLOY` instead of
writing it into the contract. It was used once, on checks 4 to 7, and
`git log -p` shows all four went straight from `PENDING DEPLOY` to
`RETIRED`, so the auditor was sweeping entries the skill says it does
not sweep. Since check 8 nobody has used it. It also needs someone to
change the tag at deploy time. You aren't there when a deploy happens,
the developer can't edit this file, and an entry left on it would never
be swept. A LIVE entry whose gate hasn't been reached needs no one to
change it. If batched deploys turn out to need the third state, bring
the case where LIVE failed.

Every copy, all in this commit:

- `docs/ROUTED_CHECKS.md` header: a paragraph after the four fields.
- `.claude/skills/audit/SKILL.md` §1.3: "LIVE or RETIRED", defined by
  the file's header; a header with neither is a finding.
- `.claude/skills/triage/SKILL.md` §4: `· LIVE` from day one, so the
  writer sees the rule its reader applies.
- `.claude/skills/review/SKILL.md` says "four fields per its header",
  so it picks this up from the header. Left as it was.
