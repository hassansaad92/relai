SELECT
    a.id,
    a.personnel_id,
    a.project_id,
    a.scenario_id,
    a.sequence,
    a.start_date,
    a.end_date,
    a.allocated_days,
    a.assignment_type,
    per.name AS personnel_name,
    proj.name AS project_name,
    proj.contract_start_date
FROM assignments a
JOIN personnel per ON per.id = a.personnel_id
JOIN projects proj ON proj.id = a.project_id
WHERE a.scenario_id = %(scenario_id)s
ORDER BY per.name, a.start_date
