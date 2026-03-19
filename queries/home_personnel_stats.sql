-- Personnel roster stats
SELECT
    COUNT(*) AS total_roster,
    COUNT(*) FILTER (WHERE has_active) AS currently_assigned,
    COUNT(*) FILTER (WHERE has_any_future) AS has_future_assignment,
    COUNT(*) FILTER (WHERE NOT has_any_future AND NOT has_active) AS unassigned
FROM (
    SELECT
        p.id,
        EXISTS (
            SELECT 1 FROM assignments a
            WHERE a.personnel_id = p.id
              AND a.scenario_id = %(scenario_id)s
              AND a.start_date <= CURRENT_DATE
              AND a.end_date >= CURRENT_DATE
        ) AS has_active,
        EXISTS (
            SELECT 1 FROM assignments a
            WHERE a.personnel_id = p.id
              AND a.scenario_id = %(scenario_id)s
              AND a.end_date >= CURRENT_DATE
        ) AS has_any_future
    FROM personnel p
) sub
