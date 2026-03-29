-- Project staffing stats for awarded projects
SELECT
    COUNT(*) AS total_projects,
    COUNT(*) FILTER (WHERE has_assignment) AS staffed_count,
    COUNT(*) FILTER (WHERE NOT has_assignment) AS unstaffed_count,
    CASE
        WHEN COUNT(*) > 0 THEN ROUND(100.0 * COUNT(*) FILTER (WHERE has_assignment) / COUNT(*))
        ELSE 0
    END AS staffed_pct,
    COUNT(*) FILTER (WHERE material_arrived IS NULL OR material_arrived = false) AS material_pending_count,
    COUNT(*) FILTER (WHERE total_hours = 0 AND duration_days = 0) AS zero_hours_count
FROM (
    SELECT
        pr.id,
        EXISTS (
            SELECT 1 FROM assignments a
            WHERE a.project_id = pr.id AND a.scenario_id = %(scenario_id)s
        ) AS has_assignment,
        pr.material_arrived,
        COALESCE(pr.man_hours, 0) + COALESCE(pr.crew_hours, 0) AS total_hours,
        COALESCE(pr.duration_days, 0) AS duration_days
    FROM projects pr
    WHERE pr.award_status = 'awarded'
) sub
