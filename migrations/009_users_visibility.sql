-- 009_users_visibility.sql
-- Adds a per-user visibility tri-state to web.users. Ships PR2 of
-- docs/BRIEF.md (privacy, visibility, crews, settings).
--
-- Background: PR1 hid identity from anonymous visitors globally. PR2
-- adds a per-user knob for signed-in-visitor visibility, with three
-- levels. The column carries all three values from day one; the
-- settings form only exposes 'public' and 'private' — 'crews_only'
-- becomes user-selectable in PR3 when the crews primitive lands. See
-- BRIEF Decision 4.
--
-- Additive change: new NOT NULL column with DEFAULT 'public'.
-- Existing rows land on 'public' via the DEFAULT — that matches
-- today's behaviour (all users visible to any signed-in visitor), so
-- no data migration is required.
--
-- Retroactive-hide semantics are read-time: no write to web.attendance
-- ever happens as a side effect of flipping visibility. Because of
-- that, this migration is one ALTER and nothing else.

ALTER TABLE web.users
    ADD COLUMN visibility VARCHAR(16) NOT NULL DEFAULT 'public'
    CHECK (visibility IN ('public', 'crews_only', 'private'));
