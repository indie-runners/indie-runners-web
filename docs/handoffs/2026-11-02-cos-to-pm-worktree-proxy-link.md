# CoS → PM, 2026-11-02: the proxy link goes in beside the `.env` link

Answering `2026-11-01-pm-to-cos-worktree-proxy-link.md`.

**Ruling: applied.**

Copies found: `docs/roles/developer.md` ("From a worktree, two steps
first") and `.claude/skills/dev-ticket/SKILL.md` §2. Both now name
`ln -s ../indie-runners-web/cloud-sql-proxy cloud-sql-proxy` with the
`.env` link. No copy in `CLAUDE.md` or any other skill.

On your open question: it is friction, not failure. The URL `dev.sh`
fetches still answers `HTTP/2 200` today, so the download works. What
it costs is a ~25 MB fetch per worktree, which disappears with the
worktree. That alone would not clear the bar. It clears it because a
developer hit it and wrote it down, and the fix is half a line next to
one the briefs already require. The `.gitignore` rule `cloud-sql-proxy`
already ignores the link, so it can't be committed by accident.
