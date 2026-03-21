-- Projects with award_status = 'awarded' that have no assignments in the target scenario.
SELECT
    p.id,
    p.name,
    p.required_skills,
    p.contract_start_date,
    p.contract_end_date,
    p.duration_days,
    p.procurement_date
FROM projects p
WHERE p.award_status = 'awarded'
  AND NOT EXISTS (
      SELECT 1
      FROM assignments a
      WHERE a.project_id = p.id
        AND a.scenario_id = %(scenario_id)s
  )
ORDER BY p.contract_start_date;
