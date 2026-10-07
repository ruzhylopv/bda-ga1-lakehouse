-- alert on latest complete month; missing comparisons remain visible
WITH latest AS (
    SELECT MAX(month_start) AS month_start
    FROM bda_gold.brand_monitoring WHERE is_complete_month
)
SELECT
    COUNT(CASE WHEN m.is_comparable_month AND m.share_change_percentage_points <= -5 THEN 1 END) AS affected_category_count,
    COUNT(CASE WHEN NOT m.is_comparable_month THEN 1 END) AS unavailable_category_count,
    CASE WHEN COUNT(m.category)=0 THEN true ELSE false END AS coverage_unavailable
FROM latest l
LEFT JOIN bda_gold.brand_monitoring m
    ON m.month_start=l.month_start AND m.brand='Brand#32';
