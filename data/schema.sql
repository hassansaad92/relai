-- ─────────────────────────────────────────────────────────────────────────────
-- RelAI Supabase Schema
-- Run this entire file in the Supabase SQL Editor to set up a new project.
-- ─────────────────────────────────────────────────────────────────────────────


-- ── 1. Personnel ──────────────────────────────────────────────────────────────

CREATE TABLE personnel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    skills TEXT NOT NULL,
    availability_status TEXT NOT NULL,
    available_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE personnel DISABLE ROW LEVEL SECURITY;

CREATE TABLE personnel_history (
    hid BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    personnel_id UUID NOT NULL,
    name TEXT,
    skills TEXT,
    availability_status TEXT,
    available_date DATE,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    is_current BOOLEAN DEFAULT TRUE
);

ALTER TABLE personnel_history DISABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION update_personnel_modtime()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_personnel_modtime
    BEFORE UPDATE ON personnel FOR EACH ROW
    EXECUTE PROCEDURE update_personnel_modtime();

CREATE OR REPLACE FUNCTION handle_personnel_scd2()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        UPDATE personnel_history SET valid_to = NEW.updated_at, is_current = FALSE
        WHERE personnel_id = OLD.id AND is_current = TRUE;
        INSERT INTO personnel_history (personnel_id, name, skills, availability_status, available_date, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.skills, NEW.availability_status, NEW.available_date, NEW.updated_at, TRUE);
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO personnel_history (personnel_id, name, skills, availability_status, available_date, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.skills, NEW.availability_status, NEW.available_date, NEW.created_at, TRUE);
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE personnel_history SET valid_to = NOW(), is_current = FALSE
        WHERE personnel_id = OLD.id AND is_current = TRUE;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_personnel_scd2
    AFTER INSERT OR UPDATE OR DELETE ON personnel FOR EACH ROW
    EXECUTE PROCEDURE handle_personnel_scd2();


-- ── 2. Projects ───────────────────────────────────────────────────────────────

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    start_date DATE NOT NULL,
    duration_weeks INTEGER NOT NULL,
    num_elevators INTEGER NOT NULL,
    required_skills TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE projects DISABLE ROW LEVEL SECURITY;

CREATE TABLE projects_history (
    hid BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id UUID NOT NULL,
    name TEXT,
    start_date DATE,
    duration_weeks INTEGER,
    num_elevators INTEGER,
    required_skills TEXT,
    status TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    is_current BOOLEAN DEFAULT TRUE
);

ALTER TABLE projects_history DISABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION update_projects_modtime()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_projects_modtime
    BEFORE UPDATE ON projects FOR EACH ROW
    EXECUTE PROCEDURE update_projects_modtime();

CREATE OR REPLACE FUNCTION handle_projects_scd2()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        UPDATE projects_history SET valid_to = NEW.updated_at, is_current = FALSE
        WHERE project_id = OLD.id AND is_current = TRUE;
        INSERT INTO projects_history (project_id, name, start_date, duration_weeks, num_elevators, required_skills, status, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.start_date, NEW.duration_weeks, NEW.num_elevators, NEW.required_skills, NEW.status, NEW.updated_at, TRUE);
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO projects_history (project_id, name, start_date, duration_weeks, num_elevators, required_skills, status, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.start_date, NEW.duration_weeks, NEW.num_elevators, NEW.required_skills, NEW.status, NEW.created_at, TRUE);
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE projects_history SET valid_to = NOW(), is_current = FALSE
        WHERE project_id = OLD.id AND is_current = TRUE;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_projects_scd2
    AFTER INSERT OR UPDATE OR DELETE ON projects FOR EACH ROW
    EXECUTE PROCEDURE handle_projects_scd2();


-- ── 3. Skills ─────────────────────────────────────────────────────────────────

CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE skills DISABLE ROW LEVEL SECURITY;

CREATE TABLE skills_history (
    hid BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    skill_id UUID NOT NULL,
    skill TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    is_current BOOLEAN DEFAULT TRUE
);

ALTER TABLE skills_history DISABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION update_skills_modtime()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_skills_modtime
    BEFORE UPDATE ON skills FOR EACH ROW
    EXECUTE PROCEDURE update_skills_modtime();

CREATE OR REPLACE FUNCTION handle_skills_scd2()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        UPDATE skills_history SET valid_to = NEW.updated_at, is_current = FALSE
        WHERE skill_id = OLD.id AND is_current = TRUE;
        INSERT INTO skills_history (skill_id, skill, valid_from, is_current)
        VALUES (NEW.id, NEW.skill, NEW.updated_at, TRUE);
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO skills_history (skill_id, skill, valid_from, is_current)
        VALUES (NEW.id, NEW.skill, NEW.created_at, TRUE);
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE skills_history SET valid_to = NOW(), is_current = FALSE
        WHERE skill_id = OLD.id AND is_current = TRUE;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_skills_scd2
    AFTER INSERT OR UPDATE OR DELETE ON skills FOR EACH ROW
    EXECUTE PROCEDURE handle_skills_scd2();


-- ── 4. Scenarios ──────────────────────────────────────────────────────────────
-- Must be created before assignments (foreign key dependency).

CREATE TABLE scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',         -- 'master' or 'draft'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_from UUID REFERENCES scenarios(id),   -- which scenario it was branched from
    archived_at TIMESTAMPTZ,                       -- null = active
    archived_reason TEXT,                          -- 'superseded', 'deleted', 'limit_exceeded'
    promoted_to_master_at TIMESTAMPTZ,             -- null if never promoted
    demoted_from_master_at TIMESTAMPTZ             -- null if still master or never promoted
);

ALTER TABLE scenarios DISABLE ROW LEVEL SECURITY;

-- Seed the initial master scenario
INSERT INTO scenarios (name, status, promoted_to_master_at)
VALUES ('Master Schedule', 'master', NOW());


-- ── 5. Assignments ────────────────────────────────────────────────────────────
-- Must be created after personnel, projects, and scenarios (foreign key dependencies).

CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    personnel_id UUID NOT NULL REFERENCES personnel(id),
    project_id UUID NOT NULL REFERENCES projects(id),
    scenario_id UUID NOT NULL REFERENCES scenarios(id),
    sequence INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE assignments DISABLE ROW LEVEL SECURITY;
