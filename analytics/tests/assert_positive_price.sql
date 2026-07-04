SELECT *
FROM {{ ref('stg_coins') }}
WHERE current_price <= 0