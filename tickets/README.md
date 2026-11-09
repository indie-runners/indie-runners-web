# Tickets

`BACKLOG.csv` is the board and is **authoritative** for open work.

Each ticket gets `W-###-<slug>.md` beside the CSV row when work is about
to start. The CSV is the index; the `.md` is the spec the developer works
from, written by the PM.

**`W-` prefix** so cross-repo references stay unambiguous — the scraper's
board numbers `T-###`, and findings travel between the two.

## Columns, and who owns them

| Column | Owner | Values |
|---|---|---|
| `id` | PM | `W-###`, sequential, never reused |
| `title` | PM | one line, the defect not the symptom |
| `status` | PM / **Developer** | PM: `open` at creation, `dropped`; developer: `wip` `review` `done` |
| `priority` | PM | 1–5, 1 highest |
| `effort` | PM | `S` `M` `L` |
| `area` | PM | deploy, docs, testing, templates, services, … |
| `deploy` | PM | `immediate` \| `batched` |
| `branch` | **Developer** | set when work starts |
| `source` | PM | the audit report or doc that raised it |
| `notes` | PM | why it matters, what is known, what is not |

Single-writer per column. A conflict here means someone crossed the line.

## Priority

1. Site down or sign-in broken — nothing else notices
2. User-facing wrong — wrong data rendered, a broken page
3. Shared-budget risk — anything holding connections the scraper needs
4. Blocked work
5. Hygiene

## Evidence: what the ticket quotes, what it names

Tickets are public (`docs/roles/README.md` § Boundaries). A ticket cut
from an audit finding **quotes the evidence the public rule allows** and
names the rest as `AUDIT_<ts> F<n>` or `evidence W-###`: what was
checked, and the result, in the `.md`; the rows, slugs, ids and counts
in the gitignored file.
Never a path: it is evidence that exists on one machine.
