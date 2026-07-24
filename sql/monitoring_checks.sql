SELECT
    week_start,
    category,
    COUNT(*) AS observations,
    ROUND(AVG(ABS(units_sold - predicted_units)), 2) AS mae,
    ROUND(AVG(ABS(units_sold - predicted_units) / NULLIF(units_sold, 0)), 4) AS mape,
    ROUND(AVG(predicted_units - units_sold), 2) AS bias
FROM model_scored
GROUP BY week_start, category
ORDER BY week_start, category;
