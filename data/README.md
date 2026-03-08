# Data Directory

## History

This project originally used CSV files as its data store:

| File | Description |
|---|---|
| `mechanics.csv` | Mechanics with skills, availability status, and available date |
| `projects.csv` | Projects with required skills, dates, duration, and status |
| `skills.csv` | Master list of skills |
| `assignments.csv` | Mechanic-to-project assignments with sequences and date ranges |

The CSVs used simple integer IDs. We migrated to **Supabase** (Postgres) with UUID primary keys and SCD2 history tables for auditing. The CSVs are kept here as a reference.

The migration was performed via `migrate_to_supabase.py` (in this directory), which:
1. Inserted projects from CSV, capturing old integer ID → new UUID mappings
2. Fetched mechanics already in Supabase, mapping them by name
3. Inserted assignments using the resolved UUIDs

---

## Setting Up a New Supabase Project

Run the following SQL in order in the Supabase SQL Editor.

### 1. Mechanics

```sql
CREATE TABLE mechanics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    skills TEXT NOT NULL,
    availability_status TEXT NOT NULL,
    available_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE mechanics DISABLE ROW LEVEL SECURITY;

CREATE TABLE mechanics_history (
    hid BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mechanic_id UUID NOT NULL,
    name TEXT,
    skills TEXT,
    availability_status TEXT,
    available_date DATE,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    is_current BOOLEAN DEFAULT TRUE
);

ALTER TABLE mechanics_history DISABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION update_mechanics_modtime()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_mechanics_modtime
    BEFORE UPDATE ON mechanics FOR EACH ROW
    EXECUTE PROCEDURE update_mechanics_modtime();

CREATE OR REPLACE FUNCTION handle_mechanics_scd2()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        UPDATE mechanics_history SET valid_to = NEW.updated_at, is_current = FALSE
        WHERE mechanic_id = OLD.id AND is_current = TRUE;
        INSERT INTO mechanics_history (mechanic_id, name, skills, availability_status, available_date, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.skills, NEW.availability_status, NEW.available_date, NEW.updated_at, TRUE);
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO mechanics_history (mechanic_id, name, skills, availability_status, available_date, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.skills, NEW.availability_status, NEW.available_date, NEW.created_at, TRUE);
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE mechanics_history SET valid_to = NOW(), is_current = FALSE
        WHERE mechanic_id = OLD.id AND is_current = TRUE;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_mechanics_scd2
    AFTER INSERT OR UPDATE OR DELETE ON mechanics FOR EACH ROW
    EXECUTE PROCEDURE handle_mechanics_scd2();
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

### 4. Assignments

Must be created after mechanics and projects (foreign key dependencies).

```sql
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mechanic_id UUID NOT NULL REFERENCES mechanics(id),
    project_id UUID NOT NULL REFERENCES projects(id),
    sequence INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE assignments DISABLE ROW LEVEL SECURITY;
```

---

## Re-seeding Data

After creating the tables, re-seed from the CSVs using the migration script in this directory:

```bash
python data/migrate_to_supabase.py
```

Note: the script expects mechanics and skills to already be in Supabase (insert those manually or extend the script), then handles projects and assignments automatically.
