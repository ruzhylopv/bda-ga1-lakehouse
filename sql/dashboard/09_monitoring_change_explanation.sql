-- title: Monitoring - why did the share move? brand effect vs. category effect (10 largest moves)
SELECT
    month_start,
    category,
    ROUND(brand_revenue_effect_pp, 3)    AS brand_effect_pp,
    ROUND(category_revenue_effect_pp, 3) AS category_effect_pp,
    ROUND(actual_share_change_pp, 3)     AS actual_change_pp
FROM bda_gold.brand_share_change_explanation
WHERE brand = 'Brand#32'
  AND month_start = (
      SELECT MAX(month_start) FROM bda_gold.brand_share_change_explanation WHERE brand = 'Brand#32'
  )
ORDER BY ABS(actual_share_change_pp) DESC
LIMIT 10
