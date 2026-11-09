# W-060 — Nothing records the GitHub settings the public flip depends on

`priority: 2` · `effort: S` · `area: infra` · `deploy: none`
`source: claude/WEB_GO_PUBLIC.md (Paulo, 2026-10-27)`. This is P-3 of
the go-public prep.

**Gate: P-4 to P-7 aren't filed yet.** This file lists the settings
those tickets set, so it can't be written before they exist. Don't start
until their W-ids are named here.

## What is wrong

Nothing in the repo records what the GitHub settings are, so the flip
could happen with force pushes allowed and no scanning on.

## Evidence (PM, 2026-10-27)

At triage the PM's token couldn't read org settings:

```
$ gh api orgs/indie-runners
{"message":"Not Found" ... "status":"404"}
$ gh api repos/indie-runners/indie-runners-web/environments
gh: This API operation needs the "admin:org" scope.
```

So some read-back commands may need a scope the default `gh auth`
doesn't have. Each line in the file says which scope it needs.

## Acceptance

1. `docs/REPO_SETTINGS.md`, under 40 lines. For each setting that P-4
   to P-7 set: the setting, its required value, the ticket that sets it,
   and the `gh api` command (with `--jq`) that reads it back. Note any
   scope beyond the default.
2. Each command has been run once, and its output quoted in this ticket.
   Before Paulo changes anything, the output shows the current value. If
   a command fails, the ticket quotes the error, not a guess.
3. The developer changes no settings. The file is the record; Paulo
   makes the changes.
4. `docs/FILE_TREE.md` lists the file, plus the CHANGELOG entry.

## Note for the PM, at review

The auditor reads its previous report and `docs/ROUTED_CHECKS.md`, never
a doc it isn't pointed to (`auditor.md:104-106`). "So the auditor can
check them in a sweep" only works if the review adds a routed check that
points at `REPO_SETTINGS.md`. That check is the PM's to write, not the
developer's.

## Out of scope

- Changing any setting (P-4 to P-7, done by Paulo).
- Settings on the scraper or infra repos.
