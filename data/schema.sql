-- ─────────────────────────────────────────────────────────────────────────────
-- RelAI Supabase Schema
-- Run this entire file in the Supabase SQL Editor to set up a new project.
-- ─────────────────────────────────────────────────────────────────────────────


-- ── 1. Personnel ──────────────────────────────────────────────────────────────

CREATE TABLE personnel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    skills TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE personnel ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access" ON personnel FOR ALL USING (true) WITH CHECK (true);

CREATE TABLE personnel_history (
    hid BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    personnel_id UUID NOT NULL,
    name TEXT,
    skills TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    is_current BOOLEAN DEFAULT TRUE
);

ALTER TABLE personnel_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access" ON personnel_history FOR ALL USING (true) WITH CHECK (true);

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
        INSERT INTO personnel_history (personnel_id, name, skills, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.skills, NEW.updated_at, TRUE);
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO personnel_history (personnel_id, name, skills, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.skills, NEW.created_at, TRUE);
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
    committed_start_date DATE,
    committed_end_date DATE,
    duration_days NUMERIC(5,1) NOT NULL,
    procurement_date DATE,
    required_skills TEXT NOT NULL,
    award_status TEXT NOT NULL DEFAULT 'awarded',
    allow_overtime BOOLEAN NOT NULL DEFAULT FALSE,
    customer_id TEXT,
    account_type TEXT NOT NULL DEFAULT 'standard',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access" ON projects FOR ALL USING (true) WITH CHECK (true);

CREATE TABLE projects_history (
    hid BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id UUID NOT NULL,
    name TEXT,
    committed_start_date DATE,
    committed_end_date DATE,
    duration_days NUMERIC(5,1),
    procurement_date DATE,
    required_skills TEXT,
    award_status TEXT,
    allow_overtime BOOLEAN,
    customer_id TEXT,
    account_type TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    is_current BOOLEAN DEFAULT TRUE
);

ALTER TABLE projects_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access" ON projects_history FOR ALL USING (true) WITH CHECK (true);

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
        INSERT INTO projects_history (project_id, name, committed_start_date, committed_end_date, duration_days, procurement_date, required_skills, award_status, allow_overtime, customer_id, account_type, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.committed_start_date, NEW.committed_end_date, NEW.duration_days, NEW.procurement_date, NEW.required_skills, NEW.award_status, NEW.allow_overtime, NEW.customer_id, NEW.account_type, NEW.updated_at, TRUE);
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO projects_history (project_id, name, committed_start_date, committed_end_date, duration_days, procurement_date, required_skills, award_status, allow_overtime, customer_id, account_type, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.committed_start_date, NEW.committed_end_date, NEW.duration_days, NEW.procurement_date, NEW.required_skills, NEW.award_status, NEW.allow_overtime, NEW.customer_id, NEW.account_type, NEW.created_at, TRUE);
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

ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access" ON skills FOR ALL USING (true) WITH CHECK (true);

CREATE TABLE skills_history (
    hid BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    skill_id UUID NOT NULL,
    skill TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    is_current BOOLEAN DEFAULT TRUE
);

ALTER TABLE skills_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access" ON skills_history FOR ALL USING (true) WITH CHECK (true);

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

ALTER TABLE scenarios ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access" ON scenarios FOR ALL USING (true) WITH CHECK (true);


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
    allocated_days NUMERIC(5,1) NOT NULL DEFAULT 1.0,
    assignment_type TEXT NOT NULL DEFAULT 'full' CHECK (assignment_type IN ('full', 'cascading', 'partial')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access" ON assignments FOR ALL USING (true) WITH CHECK (true);


-- ── 6. Assignments Archive ───────────────────────────────────────────────────
-- Archived assignments from promoted/deleted scenarios. Kept separate from
-- assignments so it never bloats AI context or active queries.

CREATE TABLE assignments_archive (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_assignment_id UUID,
    personnel_id UUID NOT NULL,
    project_id UUID NOT NULL,
    scenario_id UUID NOT NULL,
    scenario_name TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    allocated_days NUMERIC(5,1) NOT NULL DEFAULT 1.0,
    assignment_type TEXT NOT NULL DEFAULT 'full',
    archived_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE assignments_archive ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access" ON assignments_archive FOR ALL USING (true) WITH CHECK (true);


-- ── 7. Chat Logs ────────────────────────────────────────────────────────────

CREATE TABLE chat_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_prompt TEXT NOT NULL,
    scenario_id UUID,
    is_tweaking BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE chat_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access" ON chat_logs FOR ALL USING (true) WITH CHECK (true);
