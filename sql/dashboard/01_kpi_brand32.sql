-- title: Brand#32 headline KPIs (Q1, Q2, Q4)
-- revenue = net of discount, excluding tax (see README "Business definitions")
WITH b32 AS (
    SELECT SUM(brand_revenue) AS brand_revenue,
           COUNT(DISTINCT category) AS category_count
    FROM bda_gold.brand_category_monthly
    WHERE brand = 'Brand#32'
),
b32_categories AS (
    SELECT SUM(m.brand_revenue) AS category_revenue
    FROM bda_gold.brand_category_monthly m
    WHERE m.category IN (
        SELECT DISTINCT category FROM bda_gold.brand_category_monthly WHERE brand = 'Brand#32'
    )
),
margin AS (
    SELECT COUNT(*) AS product_count,
           AVG(average_list_unit_margin) AS average_list_unit_margin
    FROM bda_gold.part_list_margin
    WHERE brand = 'Brand#32'
),
deviation AS (
    SELECT COUNT(*) AS deviating_product_count FROM bda_gold.price_deviation_products
)
SELECT
    ROUND(b32.brand_revenue, 2)                                    AS brand32_revenue,
    ROUND(b32.brand_revenue / c.category_revenue * 100, 2)         AS brand32_share_pct,
    b32.category_count                                             AS brand32_category_count,
    m.product_count                                                AS brand32_product_count,
    ROUND(m.average_list_unit_margin, 2)                           AS brand32_average_margin,
    d.deviating_product_count                                      AS deviating_product_count
FROM b32
CROSS JOIN b32_categories c
CROSS JOIN margin m
CROSS JOIN deviation d
