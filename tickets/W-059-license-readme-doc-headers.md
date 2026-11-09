# W-059 — No license, no README, and planning docs that read as current

`priority: 2` · `effort: S` · `area: docs` · `deploy: none`
`source: claude/WEB_GO_PUBLIC.md (Paulo, 2026-10-27)`. This is P-2 of
the go-public prep. Paulo's decision: **AGPL-3.0**.

## What is wrong

A public repo with no license is all rights reserved, the opposite of
what Paulo intends. A public reader who meets `tickets/W-###`,
`docs/roles/` and the Claude co-author trailers with nothing to explain
them has to guess. `docs/TODO.md` and `docs/PLAN.md` read as current to
a stranger.

## Evidence (PM, 2026-10-27)

```
$ ls LICENSE* README*
ls: cannot access 'LICENSE*': No such file or directory
ls: cannot access 'README*': No such file or directory
$ git log --format=%B | grep -ci "co-authored-by: claude"
274
$ head -1 docs/TODO.md
# TODO: W-054 — CI applies every web migration on the scraper's baseline
$ sed -n 3p docs/PLAN.md
Rewritten 2026-08-28. ...
```

## Three corrections to the paste

1. **There is no README.** The section isn't added to an existing
   README. This ticket creates `README.md`: a title, one line saying what
   the service is (FastAPI + Jinja behind indierunners.co), the section
   below, and the license line. Nothing more.
2. **The AGPL text has no copyright line to fill in.** Unlike MIT, the
   only copyright line in it is the FSF's, on the license itself.
   "Unmodified" and "copyright line Paulo Morales Castillo" can't both
   hold inside `LICENSE`. So `LICENSE` is the verbatim text, from
   `https://www.gnu.org/licenses/agpl-3.0.txt`, and the README carries
   `Copyright (C) 2026 Paulo Morales Castillo` and the license line.
   That's where the license's own "How to Apply" puts the notice.
3. **`docs/FILE_TREE.md` must list `LICENSE` and `README.md`.** "Nothing
   else in docs/ is edited" would otherwise break review check 6. It's
   two lines, plus the CHANGELOG entry every ticket gets. Nothing else
   changes.

## Acceptance

1. `LICENSE` is byte-identical to the GNU text
   (`curl -s https://www.gnu.org/licenses/agpl-3.0.txt | diff - LICENSE`
   prints nothing, quoted).
2. `README.md` has the copyright notice and a one-line license
   statement. *Amended at review (R1):* plus one line saying the
   third-party marks in `static/icons/` (`instagram.svg`, `strava.svg`)
   belong to their owners and are not under this license.
3. A section titled "How this repo is built", under 120 words, with no
   marketing. It says:
   - the work runs as roles (auditor, PM, developer, chief of staff),
     and each is a Claude Code session opened with a brief under
     `docs/roles/`;
   - Paulo sets direction, priorities and every production decision;
   - sessions write most of the code, and every ticket, review and
     changelog entry, under those briefs;
   - commits carry the session's model as co-author.
   It links `docs/roles/README.md`. The word count is quoted here.
   *Amended at review (R1):* the paragraph is dated to the role split
   (2026-08-28), e.g. "Since 2026-08-28, …". Still under 120 words.
4. `docs/TODO.md` and `docs/PLAN.md` each get a two-line header: what
   the file is, and the date it was last true. The dates come from the
   PM, so the developer doesn't judge them:
   - **PLAN.md: 2026-08-28.** That arc (deploy path, read model) was
     overtaken by the CI/CD plan of 2026-10-25, which lives outside
     this repo (`claude/CICD_TERRAFORM_PLAN.md`).
   - **TODO.md:** the date its ticket last changed it. It's the
     per-ticket checklist and gets overwritten by the next ticket, so
     the header says so.
5. `docs/IDEAS.md` gets one line saying it is Paulo's inbox, not a
   roadmap.
6. `git diff master --stat` touches nothing in `docs/` or `tickets/`
   except the files named here. The diary is published as it is; that
   is the point.

## Out of scope

- Rewriting any ticket or changelog entry for a public audience.
- The data's license. `core.*` data is a separate, later decision.
- **Rewriting PLAN.md for the current arc.** That's the PM's file and a
  separate act. The header only makes its age visible.

## Review, 2026-10-27 (PM)

Checks 1, 3, 6 and 7 pass. `curl … | diff - LICENSE` empty, re-run here.
62 words. 32 docs lines. Changelog names the belief, the cost (none,
still private), the evidence. Carrying W-058's Support line into TODO
was right. Checks 4 and 5 don't apply: docs only, `deploy: none`.

**R1 — two README sentences overstate their scope (check 2).** Both
are what this ticket's acceptance asked for. The developer met the spec;
the spec was wrong, so 2 and 3 above are amended.

1. "Licensed under the GNU Affero General Public License v3.0" covers
   the whole tree. `static/icons/instagram.svg` and `strava.svg` (W-050,
   2026-10-26) are third-party marks Paulo can't license. A forker
   inherits the claim. Nothing else needs naming: the monogram's
   Fraunces outlines are OFL and fine in a logo, and the image inputs
   are `.gitkeep` only.
2. "Commits carry the session's model as co-author", undated. Before
   the role split (`87b6ed0`, 2026-08-28) 59 of 203 commits carry a
   Claude trailer; since then 227 of 230. A reader paging `git log`
   meets the first 203 too. Dating the paragraph also scopes "every
   ticket, review and changelog entry" to when tickets existed.

Blocks rather than follow-ups for W-004's reason: the wrong sentences
are in this diff. Changing two phrases costs less than a ticket cycle,
and the public flip waits anyway (Support 4914411, W-060).

Separate from this branch: `developer.md:20` says "Wipe what the last
one left", so the next ticket drops TODO's new header. That's a brief
change, routed to the chief of staff in
`docs/handoffs/2026-10-27-pm-to-cos-todo-header.md`.

## Verdict

**VERDICT: BLOCKED — R1** — 2026-10-27. Unblock: add the `static/icons/`
exception line under License and date the "How this repo is built"
paragraph to 2026-08-28. Requote the word count. No routed check:
nothing changes in production.

**Not verified:** how GitHub renders the README's relative links, and
whether its license detection picks AGPL-3.0 from the verbatim text.
Both are visible only once the repo is pushed or public. Also not
verified: that the next developer drops the TODO header. That's
predicted from the brief, not observed.

## Verdict (re-review)

**VERDICT: APPROVED** — 2026-10-27. R1 resolved in `28a1628`, both
halves. The paragraph opens "Since 2026-08-28" (65 words, re-counted
here). The License section excepts `static/icons/instagram.svg` and
`strava.svg` by name. `LICENSE` is still byte-identical to the GNU text
(re-run against the branch). Docs: 33 lines. Merge and push master.
`deploy: none`. No routed check, because nothing changes in production.

**Not verified:** GitHub's render of the README's relative links and
its license detection. Neither shows until the repo is pushed or
public. The TODO header surviving the next ticket depends on the CoS
handoff (`docs/handoffs/2026-10-27-pm-to-cos-todo-header.md`), not on
this branch.
