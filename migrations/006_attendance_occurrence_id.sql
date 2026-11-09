-- 006_attendance_occurrence_id.sql
-- Re-keys web.attendance from (user_id, event_id) to (user_id, occurrence_id).
-- One row per user per edition. Preserves past editions as separate rows.
--
-- Take a manual Cloud SQL backup before running on production.
-- Run each step separately. Verify counts before proceeding.

-- Step 1: add occurrence_id column (nullable for backfill)
ALTER TABLE web.attendance ADD COLUMN occurrence_id INTEGER;

-- Step 2: backfill occurrence_id from core.event_occurrences.
-- Join on event_id and start_date matching race_date (set in migration 005).
-- Rows with no match (race_date is null or no occurrence matches) stay null.
UPDATE web.attendance a
SET occurrence_id = o.id
FROM core.event_occurrences o
WHERE a.event_id = o.event_id
  AND a.race_date = o.start_date
  AND a.occurrence_id IS NULL;

-- Step 3: verification.
-- Rows still missing occurrence_id have either a null race_date (event was
-- already past when migration 005 ran) or no exact start_date match.
-- Confirm this count is understood before proceeding.
SELECT count(*) AS rows_without_occurrence_id FROM web.attendance WHERE occurrence_id IS NULL;

-- Step 4: drop old unique constraint
ALTER TABLE web.attendance DROP CONSTRAINT uq_attendance_user_event;

-- Step 5: add new unique constraint on (user_id, occurrence_id).
-- Null occurrence_id rows are excluded from uniqueness enforcement by postgres
-- (nulls are not equal), so they will not block this step.
ALTER TABLE web.attendance ADD CONSTRAINT uq_attendance_user_occurrence UNIQUE (user_id, occurrence_id);

-- Step 6: add index on occurrence_id
CREATE INDEX idx_attendance_occurrence_id ON web.attendance (occurrence_id);
