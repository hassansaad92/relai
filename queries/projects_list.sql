SELECT
    p.id,
    p.name,
    p.committed_start_date,
    p.committed_end_date,
    p.duration_days,
    p.procurement_date,
    p.required_skills,
    p.award_status,
    p.allow_overtime,
    p.customer_id,
    p.account_type,
    p.work_order_number,
    p.work_order_date,
    p.equipment,
    p.material_status,
    p.division,
    p.sales_rep,
    p.description,
    p.man_hours,
    p.crew_hours,
    p.total_amount,
    p.created_at,
    p.updated_at,
    MIN(a.start_date) AS actual_start_date,
    MAX(a.end_date) AS actual_end_date,
    COUNT(a.id) AS assignment_count,
    CASE
        WHEN COUNT(a.id) = 0 THEN 'not_scheduled'
        WHEN MIN(a.start_date) <= CURRENT_DATE AND MAX(a.end_date) >= CURRENT_DATE THEN 'active'
        ELSE 'scheduled'
    END AS schedule_status
FROM projects p
LEFT JOIN assignments a ON a.project_id = p.id AND a.scenario_id = %(scenario_id)s
GROUP BY p.id
ORDER BY p.committed_start_date NULLS LAST
