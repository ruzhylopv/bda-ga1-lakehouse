-- title: Data quality - latest validation run, checks passed per phase
WITH latest AS (
    SELECT run_id FROM bda_gold.validation_results
    ORDER BY checked_at DESC
    LIMIT 1
)
SELECT
    v.phase,
    COUNT(*)                                        AS checks,
    SUM(CASE WHEN v.passed THEN 1 ELSE 0 END)       AS passed,
    SUM(CASE WHEN NOT v.passed THEN 1 ELSE 0 END)   AS failed,
    SUM(CASE WHEN NOT v.passed AND v.is_critical THEN 1 ELSE 0 END) AS critical_failures
FROM bda_gold.validation_results v
JOIN latest l ON v.run_id = l.run_id
GROUP BY v.phase
ORDER BY CASE v.phase WHEN 'bronze' THEN 1 WHEN 'silver' THEN 2
                      WHEN 'reconciliation' THEN 3 WHEN 'gold' THEN 4 ELSE 5 END
