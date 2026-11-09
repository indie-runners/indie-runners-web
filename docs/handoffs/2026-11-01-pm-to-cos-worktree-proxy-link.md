# PM → chief of staff, 2026-11-01 — a fresh worktree also needs the proxy binary

From `docs/DEV_NOTES.md`, 2026-10-30, while on W-072:

> `cloud-sql-proxy` is gitignored beside `.env`, so `scripts/dev.sh` from a
> fresh worktree tries to download it again. `ln -s
> ../indie-runners-web/cloud-sql-proxy cloud-sql-proxy` fixes it; the
> developer brief and `/dev-ticket` name only the `.env` link.

Both places name the `.env` link only: `docs/roles/developer.md:62-63`
and `.claude/skills/dev-ticket/SKILL.md:62`. What it needs is the second
`ln -s` beside the first, in both. Not verified by the PM: whether
`dev.sh`'s download succeeds anyway, which would make this friction
rather than a failure.
