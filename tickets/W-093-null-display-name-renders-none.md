# W-093 — A runner with no name shows as "None"

`priority: 4` · `effort: S` · `area: templates` · `deploy: batched`
`source: W-080 review 2026-11-02 (PM)`

## What is wrong

`web.users.display_name` is nullable, and `short_display_name` returns
`None` when Google sends a blank name. Three templates print it raw, and
Jinja renders `None` as the text "None". Since W-080 that text is the
link to the member's profile.

## Evidence

```
app/templates/crews_detail.html:106  <span class="crew-member-name">{{ user.display_name }}</span>
app/templates/profile.html:3         {% block title %}{{ target_user.display_name }} — Indie Runners{% endblock %}
app/templates/profile.html:61        <h1 class="profile-name">{{ target_user.display_name }}</h1>
```

AMENDED 2026-11-03 at the W-082 review. After W-082 merges, the member
name above moves to `crews_detail.html:112`. Two more raw renders arrive
with the Remove button, so a nameless member reads "Remove None":

```
app/templates/crews_detail.html:119  confirm(("Remove " ~ user.display_name ~ " from " ...) | tojson)
app/templates/crews_detail.html:120  aria-label="Remove {{ user.display_name }}"
```

The pattern already in use, `event.html:459`:

```
<a href="/profile/{{ u.id }}" class="whos-coming-name">{{ u.display_name or 'Runner' }}</a>
```

`user_service.py:147`: `short_display_name({"name": "  ", "given_name": ""}) is None`.

## Acceptance

1. The five renders above fall back to `'Runner'`, as `event.html` does.
2. Verified with a user whose `display_name` is NULL, signed in: the crew
   member row and that user's profile title and heading read "Runner",
   and an admin's Remove label and confirm text name "Runner".

## Out of scope

- Backfilling NULL names. The fallback covers them.
- Initials and `alt` text: they already fall back (`'?'`, `''`).
