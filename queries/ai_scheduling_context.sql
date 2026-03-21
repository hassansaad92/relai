-- Personnel with their assignments for a given scenario.
-- One row per personnel × assignment, ordered by person then date.
-- LEFT JOIN so unassigned personnel still appear.
SELECT
    p.id          AS personnel_id,
    p.name        AS personnel_name,
    p.skills,
    a.project_id,
    pr.name       AS project_name,
    a.start_date,
    a.end_date,
    a.sequence,
    a.allocated_days,
    a.assignment_type
FROM personnel p
LEFT JOIN assignments a
    ON a.personnel_id = p.id
    AND a.scenario_id = %(scenario_id)s
LEFT JOIN projects pr
    ON pr.id = a.project_id
ORDER BY p.name, a.start_date NULLS LAST;
