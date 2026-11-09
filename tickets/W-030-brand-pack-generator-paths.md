# W-030 — The logo pack's generator and README still say `/static/favicon/`

`priority: 5` · `effort: S` · `area: hygiene` · `deploy: batched`
`source: W-024 review, 2026-10-22`

## What is wrong

W-024 fixed the two icon paths in the **served**
`static/brand/favicon/site.webmanifest` to `/static/brand/favicon/`.
The pack's source still carries the old path:

- `static/brand/build_assets.py:318-319` writes the manifest with
  `"/static/favicon/icon-192.png"` and `"…/icon-512.png"`.
- `static/brand/README.md` ("Wiring it into the web app") says to copy
  files to `static/favicon/` and gives `<head>` tags with that path.

The script writes to `static/brand/out/`, so running it overwrites
nothing. But the README says "Run it again to change colours or sizes",
and the natural next step, copying `out/favicon/` over `favicon/`,
puts the broken manifest back. The README would then point the next
reader at a layout this repo does not use.

## Acceptance

1. `build_assets.py` writes `/static/brand/favicon/...` in the manifest.
   Change the strings only. **Do not run the script** (W-024's rule
   stands).
2. The README's wiring section matches what `base.html` actually
   carries, and says the pack is served in place, not copied.
3. Changelog entry, one line is enough.

## Out of scope

- Regenerating any asset.
- The `og:` tags and `og-image.png` (W-010's territory).
