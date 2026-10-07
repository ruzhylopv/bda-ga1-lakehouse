-- title: Alert - Brand#32 share drop >= 5 pp in the latest complete month (same logic as sql/brand_share_alert.sql)
WITH latest AS (
    SELECT MAX(month_start) AS month_start
    FROM bda_gold.brand_monitoring WHERE is_complete_month
)
SELECT
    l.month_start,
    COUNT(CASE WHEN m.is_comparable_month AND m.share_change_percentage_points <= -5 THEN 1 END) AS affected_category_count,
    COUNT(CASE WHEN NOT m.is_comparable_month THEN 1 END) AS unavailable_category_count,
    COUNT(m.category) AS monitored_category_count
FROM latest l
LEFT JOIN bda_gold.brand_monitoring m
    ON m.month_start = l.month_start AND m.brand = 'Brand#32'
GROUP BY l.month_start
