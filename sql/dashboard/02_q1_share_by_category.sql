-- title: Q1 - Brand#32 share within each category it belongs to
-- fair_share_pct = 100 / number of brands in the category (equal split benchmark)
WITH b32 AS (
    SELECT category,
           SUM(brand_revenue)    AS brand32_revenue,
           SUM(category_revenue) AS category_revenue
    FROM bda_gold.brand_category_monthly
    WHERE brand = 'Brand#32'
    GROUP BY category
),
brands AS (
    SELECT category, COUNT(DISTINCT brand) AS brand_count
    FROM bda_gold.brand_category_monthly
    GROUP BY category
)
SELECT
    b.category,
    ROUND(b.brand32_revenue, 2)                                         AS brand32_revenue,
    ROUND(b.category_revenue, 2)                                        AS category_revenue,
    ROUND(b.brand32_revenue / NULLIF(b.category_revenue, 0) * 100, 2)   AS brand32_share_pct,
    ROUND(100.0 / n.brand_count, 2)                                     AS fair_share_pct
FROM b32 b
JOIN brands n ON b.category = n.category
ORDER BY brand32_share_pct DESC
