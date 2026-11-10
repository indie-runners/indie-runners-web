# W-112 — Every deploy installs whatever Python packages are newest that day

`priority: 2` · `effort: S` · `area: build` · `deploy: batched`
`source: docs/IDEAS.md "Lock the Python dependencies, highest priority" (Paulo, 2026-11-09)`

## What is wrong

The image does not pin its dependencies, so building the same commit twice
can produce two different images. `requirements.txt` puts an upper bound on
SQLAlchemy only. Every other package has just a lower bound, and the
Dockerfile installs from that file. So `scripts/deploy.sh` picks up whatever
version is newest on the day of the build. With no test suite, a FastAPI,
Starlette or pydantic release that changes behaviour gets caught by the
manual run before deploy, or not at all on a route nobody clicked. And when
something regresses, nobody can tell whether it was our change or a
dependency that moved.

## Evidence

`requirements.txt` at `f69ebc3`:

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
# ... The other requirements remain unpinned -- pinning
# them is a separate change.
sqlalchemy>=2.0.0,<2.1
psycopg[binary]>=3.1.0
...
```

`Dockerfile`:

```
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

At triage, the serving revision was `indie-runners-web-00094-862`, image
`gcr.io/indie-runners-dev-470411/indie-runners-web@sha256:aab295ea84e0e6a51cf0b7bbf817a70bd87291047d9fe2cefa7440facd268377`
(created 2026-11-09T10:59:21Z). The image has no tag (W-008), so the
digest is the only way to refer to it.

## Acceptance

1. **The pins come from the image that is serving, not from a fresh
   install.** Run `pip freeze` inside the live image. Use the digest
   above, or the current one from `./scripts/deploy.sh --check` plus
   `gcloud run revisions describe` if a deploy has happened since. Write
   the result to a new tracked file (call it `requirements.lock`, or
   another name if you prefer). A `pip install` on the dev machine today
   can already differ from what production runs, and the whole point is
   that the pins match production.
2. `requirements.txt` stays as the list of direct dependencies. Its
   comment saying the rest are unpinned goes away or gets rewritten to
   point at the lock file.
3. The Dockerfile installs from the lock file.
4. **The check:** `pip freeze` inside the locally built image, sorted,
   equals `pip freeze` inside the live image, sorted, with an empty diff.
   Record which revision and digest it was compared against in
   `evidence W-112`. CI's `docker build .` passes.
5. The changelog says how an upgrade now happens, in one or two lines:
   edit `requirements.txt`, regenerate the lock, deploy. Update
   `docs/FILE_TREE.md` for the new file.

## Out of scope

- **Upgrading any package.** The lock has to equal what is live. If a pin
  looks old, that is a separate ticket.
- **Dependabot.** It only helps once the repo is public and needs its own
  `.github/dependabot.yml`. That is a follow-up after the flip and comes
  back through IDEAS or triage.
- **`--require-hashes`.** The IDEAS entry calls it optional.
- **The `python:3.11-slim` base tag.** It floats too, but it is a
  different mechanism with a different trade-off (OS security patches
  arrive through that tag). Don't fold it in partway through.
- **The local interpreter.** `scripts/dev.sh` runs Paulo's PyCharm
  interpreter, and this ticket doesn't manage it.

## Notes

`deploy: batched`. If the pins equal what is live, the first deploy after
the merge installs the same packages, and that is the point of the
acceptance-4 diff. No routed check, because nothing in production is
expected to change.

## Verdict

**VERDICT: APPROVED** — 2026-11-09. Acceptance 1–5 met. The sorted
freezes of the locally built image and the live revision 00094-862 (by
digest) diff empty: 51 packages, Python 3.11.18 in both (evidence W-112).
The local image renders anon and signed-in. `deploy: batched`, and no
ROUTED_CHECKS entry, because the first deploy should install the same
packages.

**Not verified:** the Cloud Build path that `deploy.sh` uses. Only a local
`docker build` and CI's were run. What settles it: after the next deploy,
`pip freeze` in the serving image equals `requirements.lock`. The sign-in
flow wasn't run. The base tag still floats, and with it pip, setuptools
and Python (out of scope).
