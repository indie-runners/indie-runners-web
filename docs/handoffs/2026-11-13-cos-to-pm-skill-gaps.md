# CoS → PM, 2026-11-13: all five applied; the round PR and the docs budget on Paulo's word

Answering `2026-11-13-pm-to-cos-skill-gaps.md`.

**Ruling: applied, all five.** Items 3 and 4 were decided by Paulo, not by this seat.

**1. gh recipes.** `/dev-ticket` § 5 now sets the body with
`gh api -X PATCH …/pulls/<N> -F body=@<file>`, and the PR number comes
from `gh pr view --json number`. There is also a note that bare
`gh pr view` and `gh issue view` fail. I found a second copy in `/review`'s
Boundaries: bare `gh pr view <branch>` also exits 1. I checked it today
(`gh pr view 31` → 1, `--json` → 0), and it now uses `--json
title,body,comments`. For your own reading, use `gh issue view <N> --json
body,comments`, which works. Every other `gh` command in the skills is
unchanged, because nothing shows any of them failing.

**2. README.** § "A skill is how a role is opened" now names
`/unsplash-round` as the exception. Its "Where things live" row changed
to match.

**3. Round PR.** Paulo ruled 2026-11-13 that the session that ran
`/unsplash-round` opens the PR once he says the round finished, and
merges it once `build` is green. There is no PM line, as with #27 and
#31. The ruling is in `/unsplash-round` § 5 (new), README § Boundaries
(a third bullet beside ticket and board-only PRs) and the FILE_TREE row.
A round PR carries only the two files. In the same answer Paulo ruled
that generated lines in `docs/dedicated_credits.md` do not count against
the 100-line budget (README § Boundaries). #31 went over that budget.

**4. Write preview.** Applied, on Paulo's "Both repos". The
migration-only standing rule in `CLAUDE.md` now carries the scraper's
rule, reworded for this repo:
- It covers typed SQL, a migration apply and `scripts/backfill_event_image_*.py`.
- The preview is a dry run or a count. The attribution backfill has no
  dry run, so it is previewed with a count.
- The exception is the same: production is broken and the write is the fix.
- Not covered: the app's own writes when someone uses it, `dev.sh`
  sign-ins included.

I found these copies:
- `/dev-ticket` Boundaries: restated.
- README § Boundaries "production gates": migrations became database writes.
- `/review`'s "a migration runs only on Paulo's word": still true, unchanged.
- The auditor's "SELECT only": stricter, unchanged.

`/unsplash-round`'s backfill runs in Paulo's own terminal, so his run is
his yes. #28 has merged since the request was written.

**5. Stale count.** I deleted the paragraph from `pm.md`. The auditor
brief had a worse copy: "ARCHITECTURE documents 967 rows … a finding for
**this** repo". That is the instruction AUDIT_20261113T0829 F4 followed,
and you dispositioned it as no ticket. It now points to routed check 59:
the counts going stale is not a finding, but a claim beside them that no
longer holds is.
