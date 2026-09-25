import requests

TRENDING_URL = "https://api.coingecko.com/api/v3/search/trending"


def fetch_trending_items(limit=5):
    """
    Fetch today's trending items from the market data provider (free,
    no API key required). Returns a list of dicts: id, name, symbol,
    market_cap_rank, score, image urls.
    """
    response = requests.get(TRENDING_URL, timeout=15)
    response.raise_for_status()
    data = response.json()

    items = []
    for entry in data.get("coins", [])[:limit]:
        item = entry.get("item", {})
        items.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "symbol": item.get("symbol", ""),
            "market_cap_rank": item.get("market_cap_rank"),
            "score": item.get("score"),
            "image_small": item.get("small"),
            "image_large": item.get("large"),
        })
    return items


if __name__ == "__main__":
    for item in fetch_trending_items():
        print(item)
