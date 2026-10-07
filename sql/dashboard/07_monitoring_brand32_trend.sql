-- title: Monitoring - Brand#32 revenue and share across its categories, complete months
SELECT
    month_start,
    ROUND(SUM(brand_revenue), 2)                                    AS brand32_revenue,
    ROUND(SUM(brand_revenue) / NULLIF(SUM(category_revenue), 0) * 100, 3) AS brand32_share_pct
FROM bda_gold.brand_monitoring
WHERE brand = 'Brand#32'
  AND is_complete_month
GROUP BY month_start
ORDER BY month_start
