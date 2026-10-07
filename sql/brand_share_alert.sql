-- Brand32 Market Share Drop Alert
-- Alert when Brand#32's share in any category falls by at least 5 percentage points
-- compared with the previous complete month.
--
-- Databricks Alert setup:
--   1. Go to Alerts in the sidebar
--   2. Create Alert -> name it "Brand32 market share drop"
--   3. Paste this query
--   4. Choose a SQL warehouse
--   5. Condition: affected_category_count > 0
--   6. Schedule: daily
--   7. Add yourself under Notifications

WITH latest AS (
    SELECT MAX(month_start) AS month_start
    FROM bda_gold.brand_monitoring
    WHERE is_complete_month
)
SELECT COUNT(*) AS affected_category_count
FROM bda_gold.brand_monitoring m
JOIN latest
    ON m.month_start = latest.month_start
WHERE m.brand = 'Brand#32'
  AND m.share_change_percentage_points <= -5;
