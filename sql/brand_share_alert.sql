-- Brand#32 market share drop alert (>= 5pp vs previous comparable month)

WITH latest AS (
    SELECT MAX(month_start) AS month_start
    FROM bda_gold.brand_monitoring
    WHERE is_comparable_month
)
SELECT COUNT(*) AS affected_category_count
FROM bda_gold.brand_monitoring m
JOIN latest
    ON m.month_start = latest.month_start
WHERE m.brand = 'Brand#32'
  AND m.share_change_percentage_points <= -5;

-- Coverage status
SELECT
    SUM(CASE WHEN is_comparable_month THEN 1 ELSE 0 END) AS comparable_months,
    SUM(CASE WHEN NOT is_comparable_month THEN 1 ELSE 0 END) AS not_comparable_months,
    COUNT(DISTINCT month_start) AS total_months
FROM bda_gold.brand_monitoring;
