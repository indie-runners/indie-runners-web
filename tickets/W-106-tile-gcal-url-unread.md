# W-106 — Every signed-in tile still builds a calendar link nothing reads

`priority: 5` · `effort: S` · `area: templates` · `deploy: batched`
`source: W-096 review 2026-11-04 (DEV_NOTES 2026-11-04, while on W-096)`

## What is wrong

W-096 removed every control from the tile, so nothing on a tile can open
the calendar dialog. The tile still calls `gcal_url()` and writes the
result to a `data-gcal-url` attribute. The only reader is
`offerCalendar`, and it now reads the event page's action bar only.

## Evidence

The developer's note:

> `race_tile.html:7` calls `gcal_url()` once per tile per signed-in render
> and writes `data-gcal-url` on the tile; only `offerCalendar` read it, and
> after W-096 nothing on a tile can trigger it. Sixty calls per signed-in
> index load for an attribute nobody reads.

Read on `fix/tiles-drop-attendance-controls` at `14c950c`:

```
app/templates/partials/race_tile.html:7   {% set gcal = gcal_url(race.name, ...) if current_user and not race.is_tbc else none %}
app/templates/partials/race_tile.html:10  ...{% if gcal %} data-gcal-url="{{ gcal }}"{% endif %}>
static/js/attendance.js:38                const url = bar.dataset.gcalUrl;      (bar = .event-attendance)
app/main.py:157                           templates.env.globals["gcal_url"] = gcal_url
```

## Acceptance

1. No tile carries `data-gcal-url`, and the tile template no longer calls
   `gcal_url()`.
2. If nothing else calls the Jinja global, `main.py:157` goes too. The
   event page builds its link in Python (`main.py:477`) and keeps it.
3. The event page's "Save to Google Calendar" still opens after Going,
   signed in.
4. **Amended 2026-11-05 (triage, DEV_NOTES while on W-107):**
   `avatar_strip`'s `size` argument and its `size_cls` line go, with
   `.avatar--lg` and `.hover-avatar` in `main.css`. The tile and event
   page strips render as before, signed out and signed in.

## Amendment 2026-11-05: the avatar leftovers

The developer's note (W-107 removed the last `'lg'` call):

> W-107 removed the last `avatar_strip(..., 'lg')` calls, so the macro's
> `size` argument and `.avatar--lg` are now dead. `.hover-avatar` in
> `main.css` was dead already.

Read on `master` at `9c449ee`: the four remaining `avatar_strip(` calls
(`race_tile.html:26,33`, `event.html:506,514`) pass four arguments, none
a size. `.hover-avatar` is written only by `static/js/script.js`, which
only `mockup_reference.html` loads, and that page links `styles.css`, not
`main.css`. Same unit as the rest: deletions left by W-096 and W-107,
checked by the same render.

## Out of scope

- The calendar dialog and `gcal_url()` itself.
- The reference mockups (`mockup_reference.html`, `script.js`,
  `styles.css`) and the `.hover-avatar` they carry.
- The hover panel's layout (IDEAS 2026-11-04). If that ticket lands
  first and touches `race_tile.html`, fold this one into it.
