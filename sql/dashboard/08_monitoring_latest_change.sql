-- title: Monitoring - Brand#32 share change in the latest comparable month vs. the -5 pp alert threshold
SELECT
    month_start,
    category,
    ROUND(market_share * 100, 2)              AS market_share_pct,
    ROUND(share_change_percentage_points, 2)  AS share_change_pp,
    -5.0                                      AS alert_threshold_pp,
    CASE WHEN share_change_percentage_points <= -5 THEN 'ALERT' ELSE 'ok' END AS alert_status
FROM bda_gold.brand_monitoring
WHERE brand = 'Brand#32'
  AND is_comparable_month
  AND month_start = (
      SELECT MAX(month_start) FROM bda_gold.brand_monitoring
      WHERE brand = 'Brand#32' AND is_comparable_month
  )
ORDER BY share_change_pp
