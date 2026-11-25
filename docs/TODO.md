# TODO: #72 — search fold misses ș ț ľ and other letters; uppercase accents unverified

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-25_

- [x] Letters added to the fold
- [x] Uppercase: measure what `lower()` does in this database, then decide
- [x] CHANGELOG (fixed list), ARCHITECTURE if it describes the fold
- Measure: non-ASCII letters the searched columns hold; LC_CTYPE; result sets before and after; the #18 terms; both tiers.
- Found: æ is (two names); none of the nine required letters is. `lower()` folds capitals here (en_US.UTF8).
- ARCHITECTURE does not describe the fold.
