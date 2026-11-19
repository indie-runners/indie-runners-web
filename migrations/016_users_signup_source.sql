-- 016_users_signup_source.sql
-- Where a user signed up from (#53): the utm_* / ref on the link the
-- visitor clicked Sign in from, or 'invite' and the crew for an invite link
-- (app/main.py google_login). Written once when the user row is created
-- (UserService.get_or_create_user_from_google), never updated, never rendered.
--
-- Nullable, no backfill: existing users have no known source. Text, capped
-- in the app (100 chars). signup_crew_id is a soft ref like crews.created_by:
-- no FK, so deleting the crew keeps the record of where the user came from.
--
-- Deploy order: this file first, then the code (1.9.86). The old revision
-- never names these columns, so it runs unchanged against them.

BEGIN;

ALTER TABLE web.users
    ADD COLUMN signup_source   TEXT,
    ADD COLUMN signup_medium   TEXT,
    ADD COLUMN signup_campaign TEXT,
    ADD COLUMN signup_content  TEXT,
    ADD COLUMN signup_ref      TEXT,
    ADD COLUMN signup_crew_id  INTEGER;

COMMIT;
