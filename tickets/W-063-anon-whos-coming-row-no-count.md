# W-063 — The anonymous who's-coming row gives a screen reader no count

`priority: 5` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-27 (while on W-028), filed at the W-028 review`

## What is wrong

Signed out, the event page's who's-coming columns are a heading and an
avatar row (`event.html:506-517`):

```html
<h3 class="whos-coming-col-title">Going</h3>
<div class="whos-coming-anon-row">
  {{ avatar_strip([], attendance_summary.going_count, ...
```

Every avatar is `aria-hidden` (W-028 kept that, per Paulo's rule 5), and
the `+N` chip only renders above the cap of 4. So with 1-4 attendees a
screen reader hears "Going" and nothing else. Tiles don't have this
problem: each row sits beside its "N going" text.

Pre-existing; W-028 neither caused nor changed it. Paulo's rule 5 ("keep
or add one accessible label per avatar row, such as the existing going
count text") is met by the letter, not by what it asks for.

## Acceptance

1. Signed out, each anon who's-coming row exposes its count to assistive
   tech: one label per row, not per circle.
2. Signed-in render unchanged.
3. Checked with the accessibility tree (Chrome DevTools or equivalent),
   quoted in the changelog.

## Out of scope

Visible design changes to the row. The signed-in who's-coming list.

**Wording candidate (W-066 review, 2026-10-28):** W-066 settled the signed-in
line as `1 indie runner is going` / `N indie runners are going`. That
sentence could be this row's one label. It's a candidate, not a decision.
