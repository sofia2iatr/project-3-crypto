import time
from datetime import datetime, timezone

import dlt
import requests
from dotenv import load_dotenv
import os

load_dotenv()

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "crypto-project",
}
api_key = os.getenv("COINGECKO_API_KEY")
if api_key:
    HEADERS["x-cg-demo-api-key"] = api_key

session = requests.Session()

def get_json(url):
    while True:
        response = session.get(url, headers=HEADERS, timeout=10)

        if response.status_code == 200:
            return response.json()

        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 20))
            print(f"Rate limit. I' m waiting {wait} seconds...")
            time.sleep(wait)
            continue

        response.raise_for_status()

@dlt.resource(
    name="coins",
    write_disposition="merge",
    primary_key="id",
    columns={
        "current_price": {"data_type": "double"}
    }
)
def coins():
    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        "?vs_currency=usd"
        "&order=market_cap_desc"
        "&per_page=50"
        "&page=1"
    )

    data = get_json(url)
    print(f"Loaded {len(data)} coins")
    yield data

@dlt.resource(
    name="coin_history",
    write_disposition="merge",
    primary_key=["coin_id", "date"],
    columns={
        "price": {"data_type": "double"},
        "market_cap": {"data_type": "double"},
        "total_volume": {"data_type": "double"}
    }
)
def coin_history(
    updated_at=dlt.sources.incremental("date", initial_value="2000-01-01")
):
    markets_url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        "?vs_currency=usd"
        "&order=market_cap_desc"
        "&per_page=50"
        "&page=1"
    )

    all_coins = get_json(markets_url)
    print(f"Κατεβάζω ιστορικό για {len(all_coins)} coins...")

    for index, coin in enumerate(all_coins, start=1):
        coin_id = coin["id"]
        print(f"[{index}/50] {coin_id}")

        history_url = (
            f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            "?vs_currency=usd"
            "&days=90"
            "&interval=daily"
        )

        history = get_json(history_url)
        prices = history.get("prices", [])
        market_caps = history.get("market_caps", [])