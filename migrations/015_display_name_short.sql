-- 015_display_name_short.sql
-- Backfills web.users.display_name to first name + last initial (W-090).
-- Sign-in now writes 'Paulo M.' (user_service.short_display_name), but
-- 11 of 23 users had not signed in for 30 days and would keep their full
-- Google name indefinitely. Paulo: "It is imperative we show first name
-- and the initial of the last name instead."
--
-- Rule, matching the helper's fallback on Google's `name`: first token,
-- space, first letter of the LAST token, '.'. Only multi-token rows
-- change, so a row already in the short form ('Paulo M.' -> 'Paulo M.')
-- is a no-op and the file can be re-run. Three-plus-token rows take the
-- last token (the spec accepts this; the next sign-in corrects them from
-- Google's own fields). updated_at is left alone: it means "last sign-in".
--
-- Deploy order: the code (1.9.56) first, then this file. A sign-in on the
-- old revision would write the full name back.

BEGIN;

UPDATE web.users
SET display_name = split_part(btrim(display_name), ' ', 1)
    || ' '
    || left(regexp_replace(btrim(display_name), '^.*\s', ''), 1)
    || '.'
WHERE btrim(display_name) ~ '\s'
  AND display_name !~ '^\S+ \S\.$';

COMMIT;
