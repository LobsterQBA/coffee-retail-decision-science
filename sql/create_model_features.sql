DROP TABLE IF EXISTS model_features;

CREATE TABLE model_features AS
WITH daily AS (
    SELECT
        t.date,
        t.store_id,
        s.region,
        s.store_type,
        s.walkability_score,
        t.category,
        t.units_sold,
        t.price,
        t.base_price,
        t.unit_cost,
        t.discount_pct,
        t.temperature_f,
        t.precipitation_in,
        c.day_of_week,
        c.is_weekend,
        c.is_holiday,
        c.week_start,
        ROUND(t.units_sold * t.price, 2) AS revenue,
        ROUND(t.units_sold * (t.price - t.unit_cost), 2) AS gross_margin,
        CASE WHEN t.discount_pct > 0 THEN 1 ELSE 0 END AS is_promoted
    FROM transactions t
    JOIN stores s
        ON t.store_id = s.store_id
    JOIN calendar c
        ON t.date = c.date
),
with_baselines AS (
    SELECT
        *,
        AVG(units_sold) OVER (
            PARTITION BY store_id, category
            ORDER BY date
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS trailing_28d_units,
        AVG(gross_margin) OVER (
            PARTITION BY store_id, category
            ORDER BY date
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS trailing_28d_margin
    FROM daily
)
SELECT
    *,
    CASE
        WHEN trailing_28d_units IS NULL THEN units_sold
        ELSE trailing_28d_units
    END AS baseline_units,
    CASE
        WHEN trailing_28d_margin IS NULL THEN gross_margin
        ELSE trailing_28d_margin
    END AS baseline_margin
FROM with_baselines;
