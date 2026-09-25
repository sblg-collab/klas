import time

import requests

DETAIL_URL = "https://api.coingecko.com/api/v3/coins/{id}"


def fetch_item_details(item_id):
    """
    Fetch a short English description and basic market stats for one
    item from the data provider. This is the raw material for the
    "why is this trending" explanation, so no separate news API or
    key is needed.
    """
    url = DETAIL_URL.format(id=item_id)
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    description = (data.get("description", {}) or {}).get("en", "") or ""
    description = description.split("\r\n\r\n")[0].split("\n\n")[0]  # first paragraph only

    market_data = data.get("market_data", {}) or {}
    price_change_24h = market_data.get("price_change_percentage_24h")
    current_price = (market_data.get("current_price", {}) or {}).get("usd")

    return {
        "description": description.strip(),
        "price_change_24h": price_change_24h,
        "current_price_usd": current_price,
    }


def fetch_details_for_items(items, delay=1.5):
    """
    The free tier of the data provider is rate limited, so pause
    briefly between calls when enriching several items in a row.
    """
    enriched = []
    for item in items:
        try:
            details = fetch_item_details(item["id"])
        except requests.RequestException:
            details = {"description": "", "price_change_24h": None, "current_price_usd": None}
        enriched.append({**item, **details})
        time.sleep(delay)
    return enriched
