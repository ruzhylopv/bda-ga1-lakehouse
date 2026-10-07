-- title: Q3 - category leader (largest all-time share) per category
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
ranked AS (
    SELECT *, RANK() OVER (PARTITION BY category ORDER BY market_share DESC) AS category_rank
    FROM shares
)
SELECT
    category,
    brand,
    ROUND(market_share * 100, 4) AS market_share_pct,
    CONCAT(brand, ' / ', category) AS label
FROM ranked
WHERE category_rank = 1
ORDER BY market_share_pct DESC
LIMIT 15
