-- Personnel available for a project: not already assigned to this project,
-- and have at least one day with remaining capacity in the project window.
-- Capacity-based: person is available if any day has total allocated_days < 1.0.
SELECT p.id, p.name, p.skills
FROM personnel p
WHERE NOT EXISTS (
    SELECT 1 FROM assignments a
    WHERE a.personnel_id = p.id
      AND a.scenario_id = %(scenario_id)s
      AND a.project_id = %(project_id)s
)
AND NOT EXISTS (
    -- Exclude person only if EVERY day in the project window is fully booked (>= 1.0)
    SELECT 1
    WHERE (%(project_end)s::date - %(project_start)s::date) > 0
    AND (
        SELECT COUNT(*)
        FROM generate_series(%(project_start)s::date, %(project_end)s::date - INTERVAL '1 day', '1 day') AS d(dt)
        WHERE (
            SELECT COALESCE(SUM(a.allocated_days), 0)
            FROM assignments a
            WHERE a.personnel_id = p.id
              AND a.scenario_id = %(scenario_id)s
              AND a.start_date <= d.dt
              AND a.end_date > d.dt
        ) >= 1.0
    ) = (%(project_end)s::date - %(project_start)s::date)
)
ORDER BY p.name
