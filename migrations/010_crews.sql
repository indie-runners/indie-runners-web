-- 010_crews.sql
-- Adds web.crews, the crews primitive. Ships PR3 of docs/BRIEF.md
-- (privacy, visibility, crews, settings).
--
-- Background: PR2 shipped a per-user visibility tri-state; the
-- middle tier ('crews_only') was accepted by the column CHECK but
-- hidden from every viewer but self, because no crews existed. PR3
-- lands the primitive — a named group of users, invite-only, no
-- public directory — and turns 'crews_only' into a real predicate
-- (visible iff viewer shares at least one crew with attendee).
--
-- This file is one of three additive migrations that land together
-- (010 = crews, 011 = memberships, 012 = invites). Splitting them
-- keeps each file trivially reversible and per-file testable. See
-- PLAN Decision 11.
--
-- created_by is a soft reference to web.users.id, matching the
-- soft-ref idiom that web.attendance uses for core.events. No FK is
-- declared — orphaned-crew handling on user delete is a corner case
-- that PR4 will specify (see PLAN "Out of scope for PR3").

CREATE TABLE web.crews (
    id           SERIAL PRIMARY KEY,
    slug         VARCHAR(64) NOT NULL UNIQUE,
    display_name VARCHAR(120) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by   INTEGER NOT NULL
);

CREATE INDEX idx_crews_created_by ON web.crews(created_by);
