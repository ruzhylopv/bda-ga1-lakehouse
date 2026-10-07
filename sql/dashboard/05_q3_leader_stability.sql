-- title: Q3 - is the overall leader's share stable? (monthly share and rank, complete months only)
-- boundary months (first and last) are excluded as potentially incomplete, same rule as 02_gold_layer
WITH totals AS (
    SELECT category, brand, SUM(brand_revenue) AS brand_revenue
    FROM bda_gold.brand_category_monthly
    GROUP BY category, brand
),
shares AS (
    SELECT category, brand,
           brand_revenue / NULLIF(SUM(brand_revenue) OVER (PARTITION BY category), 0) AS market_share
    FROM totals
),
leader AS (
    SELECT category, brand
    FROM shares
    ORDER BY market_share DESC, category, brand
    LIMIT 1
),
bounds AS (
    SELECT MIN(month_start) AS min_month, MAX(month_start) AS max_month
    FROM bda_gold.brand_category_monthly
),
monthly AS (
    SELECT m.month_start, m.category, m.brand, m.market_share,
           RANK() OVER (PARTITION BY m.month_start, m.category ORDER BY m.market_share DESC) AS monthly_rank
    FROM bda_gold.brand_category_monthly m
    JOIN leader l ON m.category = l.category
    CROSS JOIN bounds b
    WHERE m.market_share IS NOT NULL
      AND m.month_start > b.min_month
      AND m.month_start < b.max_month
)
SELECT
    m.month_start,
    m.brand,
    m.category,
    ROUND(m.market_share * 100, 2) AS market_share_pct,
    m.monthly_rank
FROM monthly m
JOIN leader l ON m.brand = l.brand
ORDER BY m.month_start
