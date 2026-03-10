SELECT
    p.id,
    p.name,
    p.skills,
    p.created_at,
    p.updated_at,
    CASE
        WHEN ca.id IS NOT NULL THEN 'assigned'
        ELSE 'available'
    END AS availability_status,
    COALESCE(la.max_end_date, CURRENT_DATE) AS next_available_date,
    ca_proj.name AS current_project_name,
    ca.end_date AS current_assignment_end,
    na_proj.name AS next_project_name,
    na.start_date AS next_assignment_start
FROM personnel p
LEFT JOIN LATERAL (
    SELECT a.id, a.end_date, a.project_id
    FROM assignments a
    WHERE a.personnel_id = p.id
      AND a.scenario_id = %(scenario_id)s
      AND a.start_date <= CURRENT_DATE
      AND a.end_date >= CURRENT_DATE
    ORDER BY a.start_date
    LIMIT 1
) ca ON TRUE
LEFT JOIN projects ca_proj ON ca_proj.id = ca.project_id
LEFT JOIN LATERAL (
    SELECT a.id, a.start_date, a.project_id
    FROM assignments a
    WHERE a.personnel_id = p.id
      AND a.scenario_id = %(scenario_id)s
      AND a.start_date > CURRENT_DATE
    ORDER BY a.start_date
    LIMIT 1
) na ON TRUE
LEFT JOIN projects na_proj ON na_proj.id = na.project_id
LEFT JOIN LATERAL (
    SELECT MAX(a.end_date) AS max_end_date
    FROM assignments a
    WHERE a.personnel_id = p.id
      AND a.scenario_id = %(scenario_id)s
) la ON TRUE
ORDER BY p.name
