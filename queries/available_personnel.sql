SELECT p.id, p.name, p.skills
FROM personnel p
WHERE NOT EXISTS (
    SELECT 1 FROM assignments a
    WHERE a.personnel_id = p.id
      AND a.scenario_id = %(scenario_id)s
      AND a.project_id = %(project_id)s
)
AND NOT EXISTS (
    SELECT 1 FROM assignments a
    WHERE a.personnel_id = p.id
      AND a.scenario_id = %(scenario_id)s
      AND a.start_date < %(project_end)s::date
      AND a.end_date > %(project_start)s::date
)
ORDER BY p.name
