-- Initialize SkillsHub database
-- Runs once when the Postgres container is first created.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- trigram index for fuzzy name/skill lookups

-- Sanity check (visible in container logs on first boot)
DO $$
BEGIN
  RAISE NOTICE 'SkillsHub DB initialized: vector + uuid-ossp + pg_trgm extensions ready.';
END $$;
