-- Migration 002: Replace race_id with event_id on web.attendance
-- Attendance is event-level: a user attends an event, not a specific race within it.

-- Step 1: add event_id column (nullable for backfill)
ALTER TABLE web.attendance ADD COLUMN event_id BIGINT;

-- Step 2: backfill event_id from core view by matching existing race_id
-- core.mv_denormalized_event_data.race_id is TEXT; cast for comparison
UPDATE web.attendance a
SET event_id = mv.event_id::BIGINT
FROM (
    SELECT DISTINCT race_id::BIGINT AS race_id, event_id::BIGINT AS event_id
    FROM core.mv_denormalized_event_data
    WHERE race_id IS NOT NULL
      AND event_id IS NOT NULL
) mv
WHERE a.race_id = mv.race_id;

-- Step 3: delete rows that could not be matched (orphaned attendance)
DELETE FROM web.attendance WHERE event_id IS NULL;

-- Step 4: enforce NOT NULL now that backfill is done
ALTER TABLE web.attendance ALTER COLUMN event_id SET NOT NULL;

-- Step 5: drop old race_id column and its index + constraint
DROP INDEX IF EXISTS web.idx_attendance_race_id;
ALTER TABLE web.attendance DROP CONSTRAINT IF EXISTS attendance_user_id_race_id_key;
ALTER TABLE web.attendance DROP COLUMN race_id;

-- Step 6: add new unique constraint and index on event_id
ALTER TABLE web.attendance ADD CONSTRAINT uq_attendance_user_event UNIQUE (user_id, event_id);
CREATE INDEX idx_attendance_event_id ON web.attendance(event_id);
