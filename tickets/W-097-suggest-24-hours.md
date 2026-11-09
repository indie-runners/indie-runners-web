# W-097 — Suggest a race: say "we get your race up and running in 24 hours or less"

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-11-02 (Paulo)`

## What is wrong

Paulo, 2026-11-02: add to the suggest-a-race text "we get your race up
and running in 24 hours or less".

## Evidence

```
app/templates/index.html:62   <a href="https://forms.gle/TSE2djQbkFyPLfXe7" ... class="suggest-btn">   (label "Suggest a race")
app/templates/index.html:124  <p>Paste the link to any race website and we will add it to the platform. The more races we have, the easier it is for everyone to find their next adventure.</p>
```

## Acceptance

1. **Default, veto at review:** the sentence goes into the banner
   paragraph at `index.html:124`. The two button labels stay "Suggest a
   race".
2. Checked at 375px and desktop, anon and signed-in: the banner wraps
   cleanly.

## Out of scope

- The Form itself, and prefilling it (an option in the search entry in
  IDEAS, left raw there).
