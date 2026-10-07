-- title: Q2 - average list-price margin per brand (Brand#32 highlighted)
-- per product: average over supplier offers; per brand: equal-weight average over products
SELECT
    brand,
    COUNT(*)                                  AS product_count,
    COUNT(average_list_unit_margin)           AS products_with_known_margin,
    ROUND(AVG(average_list_unit_margin), 2)   AS average_list_unit_margin,
    CASE WHEN brand = 'Brand#32' THEN 'Brand#32' ELSE 'Other brands' END AS highlight
FROM bda_gold.part_list_margin
GROUP BY brand
ORDER BY average_list_unit_margin DESC
