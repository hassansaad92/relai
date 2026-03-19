-- Each person's current + next assignment (by sequence), plus any ending within 14 days
WITH ranked AS (
    SELECT
        a.personnel_id,
        a.project_id,
        a.start_date,
        a.end_date,
        a.sequence,
        p.name AS personnel_name,
        pr.name AS project_name,
        CASE
            WHEN a.start_date <= CURRENT_DATE AND a.end_date >= CURRENT_DATE THEN 'active'
            WHEN a.end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '14 days' THEN 'ending_soon'
            WHEN a.start_date > CURRENT_DATE THEN 'upcoming'
            ELSE 'past'
        END AS event_type,
        ROW_NUMBER() OVER (
            PARTITION BY a.personnel_id
            ORDER BY a.sequence
        ) AS seq_rank
    FROM assignments a
    JOIN personnel p ON p.id = a.personnel_id
    JOIN projects pr ON pr.id = a.project_id
    WHERE a.scenario_id = %(scenario_id)s
      AND a.end_date >= CURRENT_DATE
)
SELECT
    personnel_name,
    project_name,
    start_date,
    end_date,
    sequence,
    event_type
FROM ranked
WHERE seq_rank <= 2
ORDER BY personnel_name, sequence
