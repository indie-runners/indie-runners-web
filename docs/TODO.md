# TODO: #63 — links to the site show no preview in WhatsApp

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-23_

- [ ] `base.html`: `og:` tags on every page, title and description in blocks
- [ ] Invite preview overrides the blocks and drops its own tags (else they duplicate)
- [ ] Event page keeps its meta description as `og:description`: a generic one would replace what crawlers fall back to today
- [ ] CHANGELOG, ARCHITECTURE
- Measure: each tag once on `/`, an event page, an invalid and a valid invite; `og:url` drops the query and escapes the path; image `200 image/png`; signed in too.
- Unsure: whether the missing image is the cause. Only a phone after deploy can say.
