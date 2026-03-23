-- Personnel available for a project: not already assigned to this project,
-- and have capacity on ALL days in the project window.
-- Capacity-based: person is available only if every day has total allocated_days < 1.0.
-- Dates are INCLUSIVE (end_date is the last working day).
SELECT p.id, p.name, p.skills
FROM personnel p
WHERE NOT EXISTS (
    SELECT 1 FROM assignments a
    WHERE a.personnel_id = p.id
      AND a.scenario_id = %(scenario_id)s
      AND a.project_id = %(project_id)s
)
AND NOT EXISTS (
    -- Exclude person if ANY day in the project window is fully booked (>= 1.0)
    SELECT 1
    FROM generate_series(%(project_start)s::date, %(project_end)s::date, '1 day') AS d(dt)
    WHERE (
        SELECT COALESCE(SUM(a.allocated_days), 0)
        FROM assignments a
        WHERE a.personnel_id = p.id
          AND a.scenario_id = %(scenario_id)s
          AND a.start_date <= d.dt
          AND a.end_date >= d.dt
    ) >= 1.0
)
ORDER BY p.name
