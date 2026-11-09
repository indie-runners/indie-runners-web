-- 011_crew_memberships.sql
-- Adds web.crew_memberships. Ships alongside 010_crews.sql and
-- 012_crew_invites.sql as part of PR3 of docs/BRIEF.md.
--
-- One row per (crew, user) pair. `role` is 'admin' or 'member'; PR3
-- ships one admin per crew (the creator), but the column exists so
-- PR4 can add co-admins and transfer without a schema change (PLAN
-- Decision 2).
--
-- Both foreign keys cascade on delete. Deleting a crew removes its
-- memberships; deleting a user removes their memberships. These are
-- the sane defaults — the alternative (SET NULL / RESTRICT) would
-- leave dangling rows that no service call would ever return.
--
-- idx_crew_memberships_user is the load-bearing index for the
-- visibility predicate: AttendanceService.get_attendance_summary
-- fetches viewer_crews via a WHERE user_id = :viewer lookup on this
-- table, and attendee_crews via WHERE user_id = ANY(:attendees).
-- Without this index the summary path drops to a seq scan on every
-- pageload.

CREATE TABLE web.crew_memberships (
    crew_id    INTEGER NOT NULL REFERENCES web.crews(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES web.users(id) ON DELETE CASCADE,
    role       VARCHAR(16) NOT NULL DEFAULT 'member'
               CHECK (role IN ('admin', 'member')),
    joined_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (crew_id, user_id)
);

CREATE INDEX idx_crew_memberships_user ON web.crew_memberships(user_id);
