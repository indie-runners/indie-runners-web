-- 014_visibility_two_levels.sql
-- Collapses web.users.visibility from three levels to two (W-076,
-- Crews v1 decision 1). 'private' hid a runner from their own crews,
-- which the crew hub (W-077) cannot honour: every crew a runner belongs
-- to sees their attendance. Paulo: "collapse to two level only."
--
-- Before: CHECK users_visibility_check IN ('public','crews_only','private');
--         3 rows 'private' (all Paulo's own test accounts).
-- After:  the same constraint name, IN ('public','crews_only');
--         those 3 rows are 'crews_only'.
--
-- Order matters: the UPDATE must land before the new CHECK, or ADD
-- CONSTRAINT fails on the 3 rows. CI applies files with plain psql -f
-- (autocommit per statement), so the transaction is explicit here.
--
-- Deploy order: the code (1.9.50) first, then this file. The old
-- revision's Private radio would be a 500 against the new CHECK.

BEGIN;

UPDATE web.users SET visibility = 'crews_only' WHERE visibility = 'private';

ALTER TABLE web.users DROP CONSTRAINT users_visibility_check;
ALTER TABLE web.users
    ADD CONSTRAINT users_visibility_check
    CHECK (visibility IN ('public', 'crews_only'));

COMMIT;
