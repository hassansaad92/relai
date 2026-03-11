-- Migration: Rename requested_start_date / requested_end_date → contract_start_date / contract_end_date
-- Run this in the Supabase SQL Editor to migrate an existing database.

ALTER TABLE projects RENAME COLUMN requested_start_date TO contract_start_date;
ALTER TABLE projects RENAME COLUMN requested_end_date TO contract_end_date;

ALTER TABLE projects_history RENAME COLUMN requested_start_date TO contract_start_date;
ALTER TABLE projects_history RENAME COLUMN requested_end_date TO contract_end_date;

-- Recreate the SCD2 trigger function to use new column names
CREATE OR REPLACE FUNCTION handle_projects_scd2()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        UPDATE projects_history SET valid_to = NEW.updated_at, is_current = FALSE
        WHERE project_id = OLD.id AND is_current = TRUE;
        INSERT INTO projects_history (project_id, name, contract_start_date, contract_end_date, duration_weeks, num_elevators, required_skills, award_status, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.contract_start_date, NEW.contract_end_date, NEW.duration_weeks, NEW.num_elevators, NEW.required_skills, NEW.award_status, NEW.updated_at, TRUE);
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO projects_history (project_id, name, contract_start_date, contract_end_date, duration_weeks, num_elevators, required_skills, award_status, valid_from, is_current)
        VALUES (NEW.id, NEW.name, NEW.contract_start_date, NEW.contract_end_date, NEW.duration_weeks, NEW.num_elevators, NEW.required_skills, NEW.award_status, NEW.created_at, TRUE);
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE projects_history SET valid_to = NOW(), is_current = FALSE
        WHERE project_id = OLD.id AND is_current = TRUE;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
