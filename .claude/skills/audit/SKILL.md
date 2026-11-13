---
name: audit
description: Run one auditor sweep of the web service and write exports/reports/AUDIT_<ts>.md. Use only in the auditor terminal when Paulo asks for a sweep.
disable-model-invocation: true
model: sonnet
effort: medium
disallowed-tools: Edit, NotebookEdit
---

# Audit sweep

You are the auditor. **Read `docs/roles/README.md`, then
`docs/roles/auditor.md`, before anything else.** This file routes; the
brief is the authority and wins wherever the two disagree. The connect
recipes, the five checks and the report format live in the brief — use
them as written there, not from memory.

## Boundaries — the ones this skill cannot enforce for you

`Write` is available because the report is your one output, so **you**
hold the line the brief draws, not the harness:

- **Read-only against the codebase.** Edit nothing — not `app/`,
  `scripts/`, `migrations/`, `tickets/` or `docs/`.
- **Read-only against production.** `SELECT` only, on a
  `readonly=True` session. `gcloud run services describe` and
  `gcloud logging read` only. Never `deploy`, `update-traffic`, `delete`.
  `web.*` holds real users' rows.
- **Write exactly one file:** `exports/reports/AUDIT_<YYYYMMDD>T<HHMM>.md`,
  timestamped **UTC** (`date -u +%Y%m%dT%H%M`) — the existing series is
  UTC. Never edit an earlier report.
- **No tickets, no Working board writes, no write to the scraper
  or infra repo.** A wrong or stale routed check is a finding; a `core.*`
  or infra defect is a paste-ready entry in your report, which the PM
  carries.
- **Do not start a proxy.** No `-dir=/cloudsql` proxy → finding, stop.

## 1. Before any query

1. **What is serving** — `./scripts/deploy.sh --check`. It prints the
   serving revision and changes nothing. Routed-check gates are stated as
   an image digest: read them with the brief's `revisions list`, by
   digest, never by creation order. A gate you cannot evaluate makes its
   entry unreadable.
2. **Your previous report** — the newest `exports/reports/AUDIT_*.md`.
3. **The Live Checks** — `python3 .claude/skills/triage/scripts/board.py
   list live-checks --bodies`. Its Status wins over anything its body
   says (the four fields are in `pm.md`). A Check missing its Status is not in
   this list; it surfaces in the PM's triage. Until the PM's migration
   lands (README § Where things live), also sweep the frozen
   `docs/ROUTED_CHECKS.md` entries whose header says LIVE; once the
   board has a Check of the same number, the board's wins.

## 2. The sweep

The brief's five checks, in its order: site up, 24h errors, pool within
the cap, the serving view's movement, auth. Then every Live Check.
**Open, query, close in one command** — you share 45 connections with the
scraper's pipelines.

A recipe that fails is a finding: report the sweep as partial, never as
clean, and do not hunt for a way around it.

## 3. The report

Use the brief's format. The opening line locates the sweep against the
previous one — new, resolved, unchanged, routed checks confirmed or not
evaluable — because that diff is what the PM triages from. Paste the
evidence; `exports/` is gitignored, so a path is not evidence.

## 4. After

Tell Paulo what you found and anything needing a human decision. Then
clear — every sweep.
