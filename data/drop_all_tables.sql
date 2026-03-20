-- ─────────────────────────────────────────────────────────────────────────────
-- Drop ALL RelAI tables and their dependent objects (triggers, functions).
-- Run this in the Supabase SQL Editor to get a clean slate, then re-run
-- schema.sql to rebuild everything.
--
-- After dropping, rebuild with:
--   1. Run data/schema.sql in the Supabase SQL Editor
--   2. Re-seed data: python data/repopulate_supabase_data.py
-- ─────────────────────────────────────────────────────────────────────────────

-- Drop tables (CASCADE removes triggers and FK constraints)
DROP TABLE IF EXISTS assignments_archive CASCADE;
DROP TABLE IF EXISTS assignments        CASCADE;
DROP TABLE IF EXISTS scenarios          CASCADE;
DROP TABLE IF EXISTS projects_history   CASCADE;
DROP TABLE IF EXISTS projects           CASCADE;
DROP TABLE IF EXISTS personnel_history  CASCADE;
DROP TABLE IF EXISTS personnel          CASCADE;
DROP TABLE IF EXISTS skills_history     CASCADE;
DROP TABLE IF EXISTS skills             CASCADE;

-- Drop trigger functions
DROP FUNCTION IF EXISTS update_personnel_modtime()  CASCADE;
DROP FUNCTION IF EXISTS handle_personnel_scd2()     CASCADE;
DROP FUNCTION IF EXISTS update_projects_modtime()   CASCADE;
DROP FUNCTION IF EXISTS handle_projects_scd2()      CASCADE;
DROP FUNCTION IF EXISTS update_skills_modtime()     CASCADE;
DROP FUNCTION IF EXISTS handle_skills_scd2()        CASCADE;
