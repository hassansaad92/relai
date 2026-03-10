SELECT
    p.id,
    p.name,
    p.requested_start_date,
    p.requested_end_date,
    p.duration_weeks,
    p.num_elevators,
    p.required_skills,
    p.award_status,
    COUNT(a.id) AS assignment_count,
    MIN(a.start_date) AS actual_start_date,
    MAX(a.end_date) AS actual_end_date,
    CASE
        WHEN COUNT(a.id) = 0 THEN 'not_scheduled'
        ELSE 'scheduled'
    END AS schedule_status
FROM projects p
LEFT JOIN assignments a ON a.project_id = p.id AND a.scenario_id = %(scenario_id)s
GROUP BY p.id
ORDER BY p.requested_start_date
