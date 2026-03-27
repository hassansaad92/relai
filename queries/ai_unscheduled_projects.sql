-- Projects with award_status = 'awarded' that have no assignments in the target scenario.
-- Excludes projects with unknown material status and zero-hour projects.
SELECT
    p.id,
    p.name,
    p.required_skills,
    p.committed_start_date,
    p.committed_end_date,
    p.duration_days,
    p.procurement_date,
    p.allow_overtime,
    p.customer_id,
    p.account_type,
    p.man_hours,
    p.crew_hours,
    p.work_order_number,
    p.division,
    p.equipment,
    p.material_arrived
FROM projects p
WHERE p.award_status = 'awarded'
  AND NOT EXISTS (
      SELECT 1
      FROM assignments a
      WHERE a.project_id = p.id
        AND a.scenario_id = %(scenario_id)s
  )
  AND p.material_arrived IS NOT NULL
  AND (COALESCE(p.man_hours, 0) + COALESCE(p.crew_hours, 0) > 0 OR p.duration_days > 0)
ORDER BY
    CASE WHEN p.account_type = 'priority' THEN 0 ELSE 1 END,
    p.committed_start_date NULLS LAST;
