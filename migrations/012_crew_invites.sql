-- 012_crew_invites.sql
-- Adds web.crew_invites. Ships alongside 010_crews.sql and
-- 011_crew_memberships.sql as part of PR3 of docs/BRIEF.md.
--
-- One row per invite token ever issued for a crew. `token` is a
-- secrets.token_urlsafe(32) value from Python (~43 chars), stored
-- opaquely. Active-vs-revoked is `revoked_at IS NULL`; rotation is
-- an UPDATE on the current active row plus an INSERT of a fresh
-- one. This is the primitive; TTL / expiry is out of scope for PR3
-- (PLAN "Out of scope for PR3").
--
-- created_by is a soft reference to web.users.id, matching the
-- pattern in web.crews.created_by. The crew_id FK cascades so a
-- deleted crew drops all its invites.
--
-- UNIQUE (token) is what makes lookup by token safe and constant
-- time; idx_crew_invites_crew_id supports the "latest active invite
-- for this crew" query on the crew detail page.

CREATE TABLE web.crew_invites (
    id          SERIAL PRIMARY KEY,
    crew_id     INTEGER NOT NULL REFERENCES web.crews(id) ON DELETE CASCADE,
    token       VARCHAR(64) NOT NULL UNIQUE,
    created_by  INTEGER NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at  TIMESTAMPTZ
);

CREATE INDEX idx_crew_invites_crew_id ON web.crew_invites(crew_id);
