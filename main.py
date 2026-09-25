import os

from src.fetch_signals import fetch_trending_items
from src.fetch_details import fetch_details_for_items
from src.compose_post import build_post_body, build_title
from src.publish import publish_post

SOURCES = ["CoinGecko"]
NUM_ITEMS = 5


def main():
    account = os.getenv("ACCOUNT")
    posting_key = os.getenv("POSTING_KEY")

    items = fetch_trending_items(limit=NUM_ITEMS)
    items_with_details = fetch_details_for_items(items)

    title = build_title(items_with_details)
    body = build_post_body(items_with_details, SOURCES)
    tags = ["trending", "daily", "notes"]

    result = publish_post(
        title=title,
        body=body,
        tags=tags,
        account=account,
        posting_key=posting_key,
    )
    print(result)


if __name__ == "__main__":
    main()
