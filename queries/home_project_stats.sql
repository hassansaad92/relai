-- Project staffing stats for awarded projects
SELECT
    COUNT(*) AS total_projects,
    COUNT(*) FILTER (WHERE has_assignment) AS staffed_count,
    COUNT(*) FILTER (WHERE NOT has_assignment) AS unstaffed_count,
    CASE
        WHEN COUNT(*) > 0 THEN ROUND(100.0 * COUNT(*) FILTER (WHERE has_assignment) / COUNT(*))
        ELSE 0
    END AS staffed_pct
FROM (
    SELECT
        pr.id,
        EXISTS (
            SELECT 1 FROM assignments a
            WHERE a.project_id = pr.id AND a.scenario_id = %(scenario_id)s
        ) AS has_assignment
    FROM projects pr
    WHERE pr.award_status = 'awarded'
) sub
