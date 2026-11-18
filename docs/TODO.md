# TODO: #51 — nothing reports the crew-growth numbers

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-18_

## Steps

- [x] `scripts/growth_numbers.py`: one connection, READ ONLY transaction, five numbers to stdout
- [x] Operator id from `--operator-id` or `GROWTH_OPERATOR_ID`, never in a tracked file
- [x] One production run; output to `evidence #51`
- [x] FILE_TREE, changelog

## Measure

- Cross-check crew and user totals by independent queries (`evidence #51`)

## Unsure

- Weeks are cut in the database session's time zone (UTC), Monday start

## What the work showed

- The operator's sign-in email is not the operator's crew account: the id must be the runner account, or number 3 counts every crew
