# W-004 — Delete the stray `=3.1.0` file in the repo root

`priority: 5` · `effort: S` · `area: hygiene` · `deploy: batched`
`source: repo inspection 2026-08-28`

**Written 2026-09-08, at review time.** W-004 was filed notes-only, on
the reasoning that a `git rm` needs no spec. That was right about the
work and wrong about the record: a verdict has to land somewhere
tracked, and the board's `notes` column is not where a review belongs.
The body below is the original ticket, restated.

## What is wrong

A file named `=3.1.0` sits in the repo root. It is **tracked** — a
`git ls-files` match — so it is in every clone and reads as a real
artefact. 1213 bytes, dated 2026-06-10.

The defect is not the disk it occupies. It is that a file with that name
**cannot be dismissed at a glance**: it reads as a pinned constraint or
a lockfile fragment, so each new reader spends the same minute
establishing that it is not load-bearing. It survived three months for
exactly that reason.

## Premise correction — 2026-09-08, from the branch

The original notes recorded the botched command as
`pip install psycopg[binary]>=3.1.0`. **It was not.** The log inside is
a `jinja2` install, and `requirements.txt` carries `>=3.1.0` on both
lines (`psycopg[binary]`, `jinja2`), which is how the wrong one was
picked when the ticket was filed. Found by the developer, who read the
file rather than trusting the ticket. It changes nothing about the fix.

## Acceptance

- The file is removed with `git rm` and no longer tracked.
- Nothing in the tree references it as a path.
- `docs/FILE_TREE.md` — checked; it never listed the file, so nothing
  to remove there.
- Changelog entry with a version bump.

## Out of scope

- Pinning or unpinning anything in `requirements.txt`. The `>=3.1.0`
  constraints are correct and unrelated.
- Any other untracked or stray file in the tree.

## Verdict

**VERDICT: BLOCKED — R1** — 2026-09-08.

The deletion itself is right and the changelog is better than the
ticket deserved: it names why a file like this survives three months
(each reader pays the same minute to establish it is inert), and it
corrects my own ticket's premise — the log is a `jinja2` install, not
`psycopg` — rather than quietly shipping around a detail the file
contradicts. That correction is the developer doing the job properly and
is recorded above so the ticket stops carrying the wrong command.

**R1 — the changelog's inertness evidence is false, and the tree
contradicts it.** The 1.9.8 entry states:

> `grep -rn '3\.1\.0'` across the tree returns only the two
> `requirements.txt` constraint lines — nothing reads `=3.1.0` as a
> path.

Both halves are wrong. `.dockerignore:12` is the line `=3.1.0` — the
deleted file's name, as a path, in a file that exists to name paths:

```
11	cloud-sql-proxy
12	=3.1.0
```

**Why this blocks rather than becoming a follow-up.** The stale line is
operationally harmless: after the deletion it is an ignore pattern
matching nothing, and the image builds identically. If that were the
whole finding it would be a judgment call. What blocks is that **the
false sentence is in this diff**, so no follow-up ticket can fix what
ships — and in a repo whose changelog carries the reasoning, an evidence
claim the tree disproves is the defect the review exists to catch. A
reader who later greps on the strength of that sentence finds the thing
it says is not there.

**Worth noting in the fix:** `git log -S` dates the `.dockerignore`
line to `673af7d` ("deployment"). The artefact was **noticed and
accommodated in June rather than removed** — someone hit it, added an
ignore rule, and moved on. That is the ticket's own "each reader spends
the same minute" cost, already paid once, and it is the strongest
argument the changelog could make for why the file mattered.

**What unblocks:** two lines on the branch. Remove `.dockerignore:12` —
an ignore rule for a deleted file is the other half of the same cleanup
— and correct the evidence sentence to what a fresh `grep` actually
returns. No re-review of the deletion itself is needed.

**Not verified:**

- **No Docker image was built**, before or after. The conclusion that
  the `.dockerignore` line is operationally inert comes from reading the
  file and reasoning about pattern matching, not from comparing two
  builds. If removing line 12 is expected to change the image at all,
  that expectation is untested here.
- **`docs/FILE_TREE.md` was checked by grep only** — it contains no
  `3.1.0` match, confirming the developer's "no doc line goes with it".
- **Nothing was run.** There is no runtime path to a file nothing names,
  so there is no browser check to make; the changelog correctly says so
  rather than implying one was performed.

**VERDICT: BLOCKED — R1**

## Re-review — 2026-10-22 (PM)

R1 is resolved at `a15524f`. `.dockerignore:12` is removed, and the
evidence sentence now says what an unfiltered grep returns. It also
says why the first grep was narrower than its claim. The deletion was
not re-reviewed, as the R1 note said it need not be. Docs: 63 lines.

**This sat approved-in-waiting for six weeks.** The fix landed 13
minutes after the block and nobody re-reviewed it. So the branch no
longer merges cleanly: `CHANGELOG`, `TODO`, `BACKLOG.csv` and this
ticket (add/add) all conflict. These are mechanical, not a finding.
Keep `master`'s copy of this ticket, which holds both reviews, and the
`master` board rows, setting only `status`/`branch`. `1.9.8` is still
the free slot between 1.9.9 and 1.9.7 on `master`, so the version
stands.

**Not verified:** as in the first review. No Docker build, and nothing
run. There is no runtime path.

**VERDICT: APPROVED**
