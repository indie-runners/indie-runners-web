# PM → chief of staff: five gaps in files you own

2026-11-13 · from the triage pass · none of these is ticketed here: the files are yours

**1. `/dev-ticket` § 5 tells the developer to run `gh pr edit`, which fails.**
DEV_NOTES 2026-11-10 (while on W-114): `gh pr edit 24 --body-file …` exits 1
on GitHub's Projects (classic) deprecation error and leaves the body unchanged.
`gh api -X PATCH repos/indie-runners/indie-runners-web/pulls/<N> -F body=@<file>`
worked. Same error for this seat today on `gh issue view --comments`
(`repository.issue.projectCards`); `gh api …/issues/<N>/comments` and
`gh api -X PATCH …/issues/<N> -F body=@<file>` work.

**2. README says every skill opens a role; `/unsplash-round` does not.**
DEV_NOTES 2026-11-10 (while on W-115): `docs/roles/README.md` § "A skill is how
a role is opened" has an exception since W-115, Paulo's own command. FILE_TREE
says so; the README line is yours.

**3. Nobody is named to open the PR after an Unsplash round.**
IDEAS 2026-11-13, Paulo's question: *"after an unsplash round, who is meant to
take care of opening a PR and handling all that jazz?"* `/unsplash-round`
step 4 says the two files go "through a PR" without an owner. Two rounds sat
uncommitted (#26; the 2026-11-11 one for two days). A deploy from `master`
before the PR merges bakes the old manifest. The 2026-11-11 round merged at
08:27Z today; the serving revision `00097-8bs` was built 2026-11-11 12:17Z,
before it.

**4. The scraper's write-preview rule, ruled "Both repos" by Paulo.**
Carried by the scraper PM in PR #28 (not merged yet, now conflicting with
`master`): *"Nothing writes to the database before Paulo has seen it and said
yes"*, covering typed statements, migration applies and scripts that write
through code. The entry asks this seat to word it for this repo's skills.
This repo's `CLAUDE.md` covers migrations only.

**5. `pm.md` calls ARCHITECTURE's read model nine weeks stale, "worth a
ticket early".** That was W-002, done. The paragraph still reads as an open
instruction to this seat. The count went stale again since, and is now read
by routed check 59 instead of a ticket.
