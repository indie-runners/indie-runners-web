# W-058 — `docs/FEEDBACK.md` holds private messages, in the tree and in history

`priority: 2` · `effort: S` · `area: docs` · `deploy: none`
`source: claude/WEB_GO_PUBLIC.md (Paulo, 2026-10-27)`. This is P-1 of the
go-public prep. **Take it before W-057** (Paulo: go-public prep comes
before sequence 8 continues).

## What is wrong

`docs/FEEDBACK.md` (20 821 bytes) holds pasted WhatsApp messages, with
timestamps and the full names of real people who wrote to Paulo
privately. It must not be published. `git rm` would leave it in every
past commit. Paulo's scan found the rest of the history clean, so this
file is the only reason to rewrite history.

## Evidence (PM, 2026-10-27)

```
$ git log --all --format='%h %s' -- docs/FEEDBACK.md
b4d7a56 <message names a sender>       # touches 1 file: FEEDBACK.md only
b36db79 include feedback document     # touches 2 files, 2026-07-02
$ git rev-list --count b36db79..master
388                                    # of 422; every one gets a new SHA
$ git ls-remote --heads origin | wc -l
4
$ git ls-remote origin | grep -c pull
2                                      # refs/pull/1/head, refs/pull/2/head
```

Only `docs/FILE_TREE.md:71` cites the file, in this repo, infra and the
scraper.

## Three corrections to the paste

1. **The commit count drops by one.** `b4d7a56` changes nothing but
   this file. `filter-repo` prunes a commit that ends up empty, and that
   removes its message, which names a sender. Expect 421, not 422.
   Keeping it with `--prune-empty never` would publish the name, so
   don't.
2. **A force push to `master` alone leaves the file public.** A rewrite
   on a fresh clone touches every branch it fetched. Force-push all
   four remote heads, or delete the ones that are merged. GitHub's
   `refs/pull/1/head` and `refs/pull/2/head` are read-only, and both
   contain the file. No push removes them. Neither do the old SHAs,
   which stay reachable by URL until GitHub garbage-collects them.
   GitHub's sensitive-data procedure covers this: a GitHub Support
   request to remove the cached views and PR refs. **Don't make the
   repo public until Support confirms**, and quote the confirmation
   here.
3. **No written rule forbids force pushes.** `CLAUDE.md` and
   `docs/roles/` don't mention them. The exception still needs Paulo's
   word in the session, because the push rewrites shared history.
   It's a single push, and nothing in the repo becomes a rule.

## Acceptance

1. Before anything else, Paulo keeps a private copy of the file outside
   the repo, and says so here.
2. On a fresh clone, run
   `git filter-repo --path docs/FEEDBACK.md --invert-paths`. Then
   force-push every remote branch once, on Paulo's explicit word in the
   session. Branches already merged are deleted instead.
3. `git log --all -- docs/FEEDBACK.md` is empty on a new clone.
   `git rev-list --all --count` on master's history is 421. Quote
   both.
   **Amended at re-review (2026-10-27):** the real run also quotes the
   0-hit name check from the dry run (counts only, never the names),
   and `git diff <pre-rewrite master> <rewritten master> --stat`
   names only `docs/FEEDBACK.md` and `.idea`. The count is whatever the
   real run gives; 421 predates the pseudonym and `.idea` scope.
4. GitHub Support is asked to purge the PR refs and the cached commit
   views, and its answer is quoted here (correction 2).
5. After the push, every other checkout is re-cloned, and the ticket
   lists them. Check `../iri-I005` and `../irs-T022` for web
   worktrees; at triage the only worktree is the main checkout. Paulo's
   PyCharm checkout is one of them.
6. `docs/FILE_TREE.md` no longer lists the file. Nothing else cites it.

## Out of scope

- **Any other history change.** Paulo scanned for secrets and found
  none.
- **Stale SHAs.** 388 commits get new SHAs, so every SHA cited in
  tickets, `docs/` and the other repos' files (for example infra
  IDEAS' "answered in web IDEAS (`2dfe0c1`)") points at nothing. That
  is accepted, not fixed. A citation still names its ticket. Rewriting
  them would be a second history-wide change.
- Making the repo public. That's Paulo's act, after acceptance 4.

## Review — 2026-10-27 (PM), branch `fix/feedback-file-in-history` at `1660c1b`

The branch is sound. The changelog names the wrong belief and the
evidence. The dry run is real (fresh clone, blob absence, tree
identical but for the file). Its correction of the count (425 → 424,
not 422 → 421) is right. "Never push this branch" is the right call:
a PR would add a third `refs/pull/N/head`. All three remote branches are
merged into master with 0 unique commits, and all contain the file, so
deleting them is safe. No app code reads the file, so there's no render
to check. Docs added: 40.

The blockers are in what runs **after** the merge. That step is the one
you can't undo: a force push plus a Support purge.

**R1 — The rewrite as written leaves sender names in history.** I
grepped the tree and every commit message for the first names of the
file's ten senders:

- `tickets/W-058-…md:20` (mine): the evidence quoted `b4d7a56`'s
  message, which names a sender. I redacted it on master today. The old
  line stays in history from `4cd069b` on, and
  `--path docs/FEEDBACK.md` doesn't touch it. **The rewrite has to add
  `--replace-text` for that exact string. Not optional.**
- `docs/IDEAS.md:417,420` ties two senders, by first name, to what they
  asked for. `docs/BRIEF.md:240-243` uses three senders' first names,
  one marked "(private)", in a worked example, there since the initial
  commit (2026-06-09). **This is Paulo's call:** publish as they are
  (first names, no messages), or replace them in the same rewrite.
  Decide before the rewrite. A second rewrite means a second force push
  and a second Support request.
- The photographer credits (`dedicated_credits.md`,
  `dedicated_manifest.json`) match on first names only. They're public
  Unsplash credits, so they're fine.

**Unblocked by:** Paulo's answer on the IDEAS and BRIEF names, recorded
here. The `--replace-text` list (the ticket line, plus the names if he
says replace). And a rerun of the dry run that shows
`git log --all -p | grep -ciE '<names>'` at 0 for every replaced
string.

**R2 — The re-clone recipe loses data.** The TODO says "copy `.env` and
`exports/` back, delete the old dir". The main checkout holds more that
is ignored, so a fresh clone won't have it:

```
237 app/imaging/   (source photos, inputs/dedicated/*.jpg)
  1 .idea/          (PyCharm's interpreter config)
  1 imports/   1 sandbox/   1 cloud-sql-proxy   1 .env   1 exports/
```

**Unblocked by:** the recipe copying back everything
`git status --ignored --porcelain` lists, not two named paths. The old
directory is deleted only after a diff of the ignored set comes back
empty. The worktree `../irw-W058` is removed first (it's the branch
under review).

## Verdict

**VERDICT: BLOCKED — R1, R2** — 2026-10-27. Neither concerns the
branch's diff. Both concern the post-merge rewrite in its TODO, which is
the part that can't be retried.

**Not verified:** the force push itself. The dry run pushed nothing, and
master has no protection (developer: API 404). Not verified either:
whether GitHub Support purges `refs/pull/*` on request, or what it
asks for. And whether claude.ai's GitHub sync keeps its own copy of
the old tree. That copy is private to Paulo's account, so it isn't a
publishing risk, but it is a copy. No routed check: nothing changes in
production.

## Re-review — 2026-10-27 (PM), branch at `8f0fe63`

**R1 resolved.** Paulo chose pseudonyms. The BRIEF example and the IDEAS
entry now use invented names, and the same pseudonym stands for the
same person in both. The wider scan turned up a path the review had
missed: `.idea/workspace.xml` was tracked until `48e04f7` and logged
every commit message, the pruned one included. So `.idea` comes out
of history too. The replacement list is in `~/indierunners-private/`
(0600, I checked) and kept out of the repo, because it holds the names.
The dry run reports 0 hits for each replaced name across
`log --all -p` and every message, and leaves the photographer credits
alone. The count went 431 → 428, with the three pruned commits named.

The dry run was **431 commits: master at `04a3482` plus the branch**.
It didn't include `80b9455`, the first review. That commit's diff
carries the sender line this ticket's evidence used to quote. The
branch's copy of the ticket still has it (line 20), and master's
redaction lands at merge. `--replace-text` works on file contents
across all of history, so the real run on merged master covers it. I've
added the name check to acceptance 3 so the real run shows it.

**R2 resolved.** The re-clone copies back every ignored path and
deletes the old directory only after the ignored sets compare equal.

Docs added: 54.

## Verdict (re-review)

**VERDICT: APPROVED** — 2026-10-27. Merge locally, push master only,
never this branch. The rewrite and the force push still need Paulo's
word in the session (acceptance 2).

**Not verified:** the real rewrite, on a history that includes the
review commits; acceptance 3 as amended settles it. The force push. The
Support purge of `refs/pull/1-2/head`. Whether claude.ai's GitHub sync
holds the old tree, which would be a private copy, not a publishing
risk. No routed check: nothing changes in production.
