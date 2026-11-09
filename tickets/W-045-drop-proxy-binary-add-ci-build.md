# W-045 — Drop the tracked proxy binary and add CI that builds the image

`priority: 2` · `effort: S` · `area: infra` · `deploy: none`
`source: claude/CICD_TERRAFORM_PLAN.md step 1 (Paulo, 2026-10-25)` —
sequence 2 (web) of that plan. Highest priority on the board (Paulo,
2026-10-25): take it next.

## What is wrong

`cloud-sql-proxy`, 24 MB, is tracked in git (added in `5ca3754 layer 1
done`) though `.dockerignore:11` excludes it from the image:

```
$ git ls-files cloud-sql-proxy
cloud-sql-proxy
$ ls -la cloud-sql-proxy
-rwxrwxr-x 1 paulo paulo 24750281 May 21 22:35 cloud-sql-proxy
```

The scraper deleted its copy in its 0.24.0. There is no CI (`.github/`
does not exist). Once there is, every checkout pays for the binary.

**Correction to the plan's wording:** it says `.gitignore` and
`.dockerignore` "keep their entries". Only `.dockerignore` has one.
`.gitignore` does not list `cloud-sql-proxy`, so this ticket **adds** it.
Without that line, the developer's own local copy is back in the tree with
the next `git add .`.

Both scripts already fetch the binary if it is missing, so neither needs a
code change:

- `scripts/dev.sh:14-21`: `PROXY_BIN="$ROOT_DIR/cloud-sql-proxy"`, wget
  if `! -f`.
- `scripts/db_proxy.sh:10-17`: the same check, but on a **relative**
  path, `cloud-sql-proxy`. It only finds the repo-root copy when run from
  the repo root, which is how ARCHITECTURE:515 documents running it.

## Acceptance

1. `cloud-sql-proxy` is out of the index: `git ls-files cloud-sql-proxy`
   prints nothing. Use `git rm --cached`, so Paulo's working copy stays on
   disk.
2. `.gitignore` gains `cloud-sql-proxy`. `.dockerignore` keeps its entry.
   Check: with the local binary present, `git status --short` does not
   list it.
3. `bash scripts/dev.sh` still starts the proxy with the local copy
   present. Then move the copy aside: it downloads one and starts. Run it
   from the repo root, the way it is documented.
4. `.github/workflows/ci.yml` runs on `pull_request` and on `push` to
   `master`. It does `docker build` of the existing `Dockerfile` and
   nothing else. No `secrets.*`, no GCP auth action, no push to a
   registry. Check: `grep -n 'secrets\|google\|gcloud\|auth' ci.yml`
   comes back empty.
5. The workflow has run green on GitHub at least once. Link the run in
   the changelog entry.
6. `docs/FILE_TREE.md` lists `.github/workflows/ci.yml`, and still lists
   `cloud-sql-proxy` only if it marks it as untracked and downloaded on
   demand.
7. A changelog entry. No version bump is needed for app behaviour, but
   follow the file's convention.

## Out of scope

- **A test suite** (W-003).
- **The migration check** (plan sequence 7).
- **Rewriting history to shrink the repo.** The binary stays in past
  commits. A fresh clone still downloads it. Only the working tree and
  future diffs get smaller.
- **The proxy version.** Both scripts download the legacy v1 binary
  (`cloud_sql_proxy.linux.amd64`, `-instances=` flag). Once the tracked
  copy is gone, a fresh checkout depends on that URL still serving. If it
  does not, say so in `docs/DEV_NOTES.md`; moving to v2 is its own ticket.
- **CI building the same image as `scripts/deploy.sh`.** `COPY app/` picks
  up the gitignored `app/imaging/inputs/**/*.jpg` locally but not in CI.
  CI shows that the tracked tree builds. It does not show that the
  deployed image matches it.
- **Deploying from CI.** `deploy.sh` stays the only path to production.

## Verdict

**VERDICT: APPROVED** — 2026-10-25. Reviewed `git diff master...fix/drop-proxy-binary-add-ci`
(3 commits, `9583f0a`..`4bffaae`). Every acceptance item is met. The binary is out of the
tree and `.gitignore` lists it. `ci.yml` is checkout plus `docker build .`, with no secrets,
GCP or registry. FILE_TREE is updated, and 1.9.25 gives the reasoning: wrong belief, cost,
new belief, evidence. The docs diff is 50 lines. The developer named the CI/deploy image
gap, as the spec asked, and did not claim CI proves more than it does. Anon tier only:
nothing here renders by tier. `deploy: none` stands.

**Merge step for Paulo:** merging deletes `cloud-sql-proxy` from the main checkout's
working tree. Copy it back from the worktree first, or let `dev.sh` download it again.

**Not verified:**
- **The CI run.** The repo is private, so I could not read run 40212247876 without auth.
  It rests on the developer's link. Open it in the browser to settle it.
- **The `push: master` trigger.** Only the PR trigger has fired so far. The first push
  after merge exercises it. Check that a run appears.
- **`scripts/db_proxy.sh`** did not run with the binary absent. It has the same
  missing-file check as `dev.sh`, which was exercised, but on a relative path, so it
  works only from the repo root.

No ROUTED_CHECKS entry: nothing in production changes.
