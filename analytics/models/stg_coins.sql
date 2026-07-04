SELECT
    id,
    symbol,
    name,
    current_price,
    market_cap,
    total_volume,
    price_change_24h,
    last_updated::timestamp AS last_updated,
    RANK() OVER (ORDER BY market_cap DESC) AS market_cap_rank
FROM {{ source('raw', 'coins') }}
WHERE current_price IS NOT NULL