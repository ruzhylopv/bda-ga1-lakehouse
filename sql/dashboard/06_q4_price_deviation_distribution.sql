-- title: Q4 - distribution of sale-line price deviation vs. the 15% threshold
-- deviation = |actual unit price - list price| / list price, bucketed by whole percent
SELECT
    CAST(FLOOR(price_deviation_ratio * 100) AS INT) AS deviation_pct_bucket,
    COUNT(*)                                        AS sale_lines,
    CASE WHEN price_deviation_ratio > 0.15 THEN 'above 15% threshold'
         ELSE 'within threshold' END                AS threshold_status
FROM bda_gold.brand_sales
GROUP BY 1, 3
ORDER BY deviation_pct_bucket
