-- Migration 003: Add Google OAuth support
-- Additive only — no rows dropped, no Strava columns removed yet.
-- Strava columns dropped in 004 after Google login is confirmed working.

-- Step 1: add new user identity columns
ALTER TABLE web.users ADD COLUMN email VARCHAR(255);
ALTER TABLE web.users ADD COLUMN display_name VARCHAR(255);
ALTER TABLE web.users ADD COLUMN avatar_url VARCHAR(500);

-- Step 2: backfill display_name from existing Strava names
UPDATE web.users
SET display_name = TRIM(firstname || ' ' || COALESCE(lastname, ''))
WHERE firstname IS NOT NULL;

-- Step 3: backfill avatar_url from existing Strava profile photos
UPDATE web.users SET avatar_url = profile_photo_url WHERE profile_photo_url IS NOT NULL;

-- Step 4: enforce UNIQUE on email (nullable ok for existing Strava-only rows)
ALTER TABLE web.users ADD CONSTRAINT uq_users_email UNIQUE (email);

-- Step 5: allow strava_athlete_id to be NULL (new Google-only users have no Strava ID)
ALTER TABLE web.users ALTER COLUMN strava_athlete_id DROP NOT NULL;

-- Step 6: create auth_identities table
CREATE TABLE web.auth_identities (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER NOT NULL REFERENCES web.users(id) ON DELETE CASCADE,
    provider         VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255),
    provider_email   VARCHAR(255),
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    last_used_at     TIMESTAMPTZ,

    CONSTRAINT uq_auth_identity_provider_user UNIQUE (provider, provider_user_id),
    CONSTRAINT uq_auth_identity_user_provider UNIQUE (user_id, provider)
);

CREATE INDEX idx_auth_identities_user_id ON web.auth_identities(user_id);
