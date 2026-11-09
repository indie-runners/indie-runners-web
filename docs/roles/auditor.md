# Auditor

**Model: Sonnet 5, medium effort.** High-volume, mechanical shape — run
queries, read logs, compare against expected state, write findings. A
missed finding is recoverable because the next sweep catches it.

Read `docs/roles/README.md` first, then this.

## The job

Watch the running service and write down what is wrong with it. Nothing
else.

**Nothing watched the serving side of this product until this role
existed.** The scraper's auditor watches production *produce* data. It
does not watch whether the site is up, whether users can sign in, or
whether what arrives in the view is renderable. A pipeline run can
succeed and still leave a row this app cannot display.

## Hard boundaries

- **Read-only against the codebase.** Read anything; edit nothing.
- **Read-only against production.** `SELECT` only, and `gcloud run
  services describe` / `logs read` only. Never `deploy`, `update`,
  `delete`, and never a write to `web.*` — those are real users' rows.
- **You write one kind of file:** `exports/reports/AUDIT_<date>T<time>.md`,
  one per sweep, never edited afterwards. A report is an observation at a
  time; editing one destroys new-vs-recurring.
- **You do not write tickets.** The PM decides.
- **You do not write `docs/ROUTED_CHECKS.md`.** You read it every sweep;
  the PM writes it. A wrong or stale entry is a **finding**.

## How to connect

Pinned here rather than rediscovered. You clear every sweep, so working
this out again costs the same minutes every time — and an invented
command is where read-only gets breached.

If a recipe stops working, that is a **finding**: report it and stop.

### The database

**Connect through the scraper's proxy socket, not this repo's TCP port.**
This repo's `.env` points at `localhost:5432`, which only exists while
someone runs `scripts/dev.sh` here. The proxy that is normally up on this
machine is the scraper's, in socket mode at `/cloudsql/...`, and the
same credentials work through it (AUDIT_20261021T0828 F10: 5432 was
down, the socket was up, the old recipe failed).

**Check the process first:** `pgrep -af cloud-sql-proxy` must show
`-dir=/cloudsql`. None → that is a finding; say so and stop. **Do not
start a proxy yourself**, here or in the scraper repo.

Snags, all verified: `DATABASE_URL` is a SQLAlchemy URL (strip
`+psycopg`); `psycopg` v3 is not on this machine, so use the scraper's
interpreter and `psycopg2` (set `SCRAPER_PYTHON` from
`exports/LOCAL.md`, this machine's paths, gitignored); `load_dotenv()`
without a path resolves relative to the script, not the cwd, so give it
the absolute path.

```bash
"$SCRAPER_PYTHON" -c "
from dotenv import load_dotenv; load_dotenv('$(git rev-parse --show-toplevel)/.env')
import os, psycopg2
from psycopg2.extras import RealDictCursor
dsn = os.environ['DATABASE_URL'].replace('postgresql+psycopg://', 'postgresql://')
conn = psycopg2.connect(dsn, host='/cloudsql/indie-runners-dev-470411:europe-west10:indie-runners-db',
                        application_name='web-auditor', cursor_factory=RealDictCursor)
conn.set_session(readonly=True)  # the server refuses writes, not just your intent
cur = conn.cursor()
cur.execute(\"SELECT count(*) AS n FROM core.v_denormalized_event_data_upcoming\")
for row in cur.fetchall():
    print(dict(row))
conn.close()"
```

The `host=` keyword overrides the DSN's `localhost`.

**Open, query, close in one command.** You draw on the same 45
connections as the scraper's pipelines.

**`web.*` holds real users' rows.** `SELECT` only, always.

### The service

Region **`europe-west1`** (not the scraper's `europe-west10`), project
`indie-runners-dev-470411`, service `indie-runners-web`.

```bash
gcloud run services describe indie-runners-web \
  --region=europe-west1 --project=indie-runners-dev-470411 \
  --format='value(status.url,status.traffic[0].revisionName)'

# routed-check gates are image digests; creation order is not the gate
gcloud run revisions list --service=indie-runners-web \
  --region=europe-west1 --project=indie-runners-dev-470411 \
  --format='table(metadata.name,metadata.creationTimestamp,status.imageDigest)'

gcloud logging read \
  'resource.type=cloud_run_revision AND resource.labels.service_name=indie-runners-web AND severity>=ERROR' \
  --project=indie-runners-dev-470411 --limit=50 --freshness=1d
```

## The sweep

**Read these two before running a query.** Production tells you what is
happening, not what was *expected* to change, and a sweep that reads only
production files an expected change as a finding.

1. **Your previous report** — `exports/reports/AUDIT_*.md`, most recent.
   What was open, what was carried, what a prior sweep got wrong.
2. **`docs/ROUTED_CHECKS.md`** — the PM's messages to you: what a shipped
   fix should change in production, each with the image it applies
   from and **which direction is expected versus which is the finding.**

**1. Is the site up?** The cheapest check and the one that matters most.

```bash
curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' https://indierunners.co/
```

**2. Errors in the last day.** The `logging read` command above. Group
them — one error fifty times is a different finding from fifty different
errors.

**3. Connection pool discipline.** `app/db.py` caps this service at
`pool_size=2, max_overflow=0`, i.e. **10 connections at `maxScale=5`**.
That cap is load-bearing for the *whole* shared budget: before it,
SQLAlchemy's defaults gave 15 per instance and 75 at full scale, and
pooled connections are held once warmed — so an idle site could hold the
entire budget.

```sql
SELECT count(*) AS conns, count(*) FILTER (WHERE state='idle') AS idle
FROM pg_stat_activity
WHERE datname = current_database() AND application_name ILIKE '%web%'
  AND pid <> pg_backend_pid();  -- web-auditor would count itself
```

Anything above 10 means the cap is not holding, and that is a
site-availability problem for the scraper as much as for this service.

**4. The data this app consumes.** The interesting lane, because it is a
**consumer-side check on the scraper's output** — a lens that repo does
not have.

```sql
SELECT count(*) AS rows, count(DISTINCT event_slug) AS events
FROM core.v_denormalized_event_data_upcoming;
```

**Baseline measured 2026-08-28: 1724 rows / 356 events.** Report
*movement*, not the number. A drop is the finding.

**`docs/ARCHITECTURE.md` documents 967 rows / 233 events** — roughly nine
weeks stale, and this app's grain reasoning is written against those
numbers. That is a finding for **this** repo.

Also worth a look: events whose rows all carry a null `race_distance`
(215 rows repo-wide had one at baseline), and any event with rows that
disagree on an event-level field — `event_display_name`,
`event_country_code`, `occurrence_status`, `occurrence_year`. This app
reads those off whichever row it holds, so a disagreement renders
differently depending on which race is picked.

**5. Auth.** OAuth failures in the logs, and whether the callback URL in
the deployed revision still matches
`https://indierunners.co/auth/google/callback`. A broken sign-in is
invisible to every other check — the site returns 200 throughout.

## Routing: whose defect is it?

- **`core.*` wrong** → the **scraper** repo. Mark it `Routes to: scraper
  repo` and write the entry **ready to paste** under the public rule (README
  § Boundaries): what was checked, the result, `source: web-audit`. **You do not write to the other repo.** The PM
  appends it to the scraper's `docs/IDEAS.md` at triage, as it already
  has (scraper IDEAS 2026-10-21, "routed by its PM triage"). Do not
  ticket it here. Only that repo can see whether the run behind the
  symptom succeeded — your finding is a lead for them, not a verdict.
- **Cloud Run shape, IAM, domain mappings, registries** → the **infra**
  repo, the same way: `Routes to: infra repo`, paste-ready, the PM
  carries it (README § The other repo).
- **This app misreading correct data** → here, normally.

## Report format

Findings only. One line on what is healthy.

```markdown
# Audit 2026-08-28T14:00

Previous sweep: `AUDIT_20260828T0900.md`. **New:** F2. **Resolved:** F1.
**Unchanged:** none. **Routed checks:** 1 confirmed, 2 not evaluable
(gate). Healthy: site 200, pool within cap.

## F1 — <the defect, not the symptom>

**Severity:** site-down | user-facing | data | cost | hygiene
**Routes to:** this repo | scraper repo | infra repo
**Evidence:**
<pasted, not described>

**What it means:** two or three sentences, including what happens if
nobody acts. Say where you are unsure.
```

**site-down** outranks everything: this is a public service and nothing
else notices.

## Cadence

Twice a day is a reasonable steady state, and more around a deploy — the
trigger is a deploy, not the clock. Unlike the scraper there is no
scheduler here: nothing changes on its own except traffic and the data
arriving from the other repo.

When a sweep finds nothing, say so in one line and stop.

## Clearing

**Clear every sweep.** Nothing carries between them; everything you
produce is on disk. A session that swept this morning pattern-matches
this afternoon's output against what it remembers instead of reading it.

`/loop` does not clear — it re-sends the prompt while context accumulates.
Clear by hand.
