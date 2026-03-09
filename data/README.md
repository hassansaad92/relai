# Data Directory

## History

This project originally used CSV files as its data store:

| File | Description |
|---|---|
| `personnel.csv` | Personnel with skills, availability status, and available date |
| `projects.csv` | Projects with required skills, dates, duration, and status |
| `skills.csv` | Master list of skills |
| `assignments.csv` | Personnel-to-project assignments with sequences and date ranges |

The CSVs used simple integer IDs. We migrated to **Supabase** (Postgres) with UUID primary keys and SCD2 history tables for auditing. The CSVs are kept here as a reference.

The migration was performed via `reset_supabase_data.py` (in this directory), which:
1. Inserted projects from CSV, capturing old integer ID → new UUID mappings
2. Fetched personnel already in Supabase, mapping them by name
3. Inserted assignments using the resolved UUIDs

---

## Setting Up a New Supabase Project

Run the following SQL in order in the Supabase SQL Editor.

### 1. Personnel

```sql
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
```

---

### 2. Projects

```sql
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
```

---

### 3. Skills

```sql
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
```

---

### 4. Scenarios

Must be created before assignments (foreign key dependency).

```sql
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
```

---

### 5. Assignments

Must be created after personnel, projects, and scenarios (foreign key dependencies).

```sql
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
```

**Migrating existing assignments to the master scenario:**
```sql
-- After running the scenarios seed above, get the master ID and update existing rows:
UPDATE assignments
SET scenario_id = (SELECT id FROM scenarios WHERE status = 'master' LIMIT 1)
WHERE scenario_id IS NULL;
```

---

## Re-seeding Data

After creating the tables, re-seed from the CSVs using the migration script in this directory:

```bash
python data/reset_supabase_data.py
```

Note: the script expects personnel and skills to already be in Supabase (insert those manually or extend the script), then handles projects and assignments automatically.
