WITH daily_totals AS (
    SELECT
        date,
        SUM(market_cap) AS total_market_cap,
        SUM(total_volume) AS total_volume
    FROM {{ source('raw', 'coin_history') }}
    GROUP BY date
),

top_volume_coin AS (
    SELECT DISTINCT ON (date)
        date,
        coin_id AS top_coin_by_volume
    FROM {{ source('raw', 'coin_history') }}
    ORDER BY date, total_volume DESC
),

price_changes AS (
    SELECT
        coin_id,
        date,
        price,
        market_cap,
        LAG(price) OVER (PARTITION BY coin_id ORDER BY date) AS prev_price
    FROM {{ source('raw', 'coin_history') }}
),

top10_avg_change AS (
    SELECT
        date,
        AVG(
            CASE WHEN prev_price > 0 THEN (price - prev_price) / prev_price * 100 END
        ) AS avg_price_change_top10
    FROM (
        SELECT *,
            RANK() OVER (PARTITION BY date ORDER BY market_cap DESC) AS mc_rank
        FROM price_changes
    ) ranked
    WHERE mc_rank <= 10
    GROUP BY date
)

SELECT
    dt.date,
    dt.total_market_cap,
    dt.total_volume,
    tv.top_coin_by_volume,
    t10.avg_price_change_top10
FROM daily_totals dt
LEFT JOIN top_volume_coin tv ON tv.date = dt.date
LEFT JOIN top10_avg_change t10 ON t10.date = dt.date
ORDER BY dt.date