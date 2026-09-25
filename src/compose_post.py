import re

# Matches em dash and en dash
DASH_PATTERN = re.compile(r"[\u2014\u2013]")


def clean_style(text):
    """
    House style: no em/en dashes, no dangling Oxford-comma-before-'and'.
    """
    text = DASH_PATTERN.sub(",", text)
    text = re.sub(r",\s*and\b", " and", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def build_blurb_template(item):
    """
    Fallback template used when no LLM key is configured. Casual,
    blog-style, one short paragraph per item. Good enough to ship
    while the pipeline is being tested; swap in build_blurb_llm once
    an LLM key is wired up in main.py for higher quality writing.
    """
    name = item["name"]
    symbol = (item.get("symbol") or "").upper()
    change = item.get("price_change_24h")
    price = item.get("current_price_usd")
    desc = item.get("description") or ""

    change_txt = ""
    if change is not None:
        direction = "up" if change >= 0 else "down"
        change_txt = f"it is {direction} {abs(change):.1f}% over the last 24 hours"

    price_txt = f"trading around ${price:,.4f}" if price else ""

    parts = [p for p in [change_txt, price_txt] if p]
    market_line = ""
    if parts:
        market_line = " and ".join(parts)
        market_line = market_line[0].upper() + market_line[1:] + "."

    trimmed_desc = (desc[:280] + "...") if len(desc) > 280 else desc

    blurb = f"{name} ({symbol}) is trending today. {market_line} {trimmed_desc}".strip()
    return clean_style(blurb)


def build_blurb_llm(item, client=None):
    """
    Optional higher quality path: call an LLM to write the blurb in a
    casual blog voice. Pass a configured client from main.py once an
    API key is available as a GitHub secret; falls back to the plain
    template otherwise so the pipeline never breaks for lack of a key.
    """
    if client is None:
        return build_blurb_template(item)

    prompt = (
        f"Write one short, casual blog style paragraph (3 to 4 sentences) explaining "
        f"why {item['name']} ({(item.get('symbol') or '').upper()}) might be trending "
        f"today. Use this context: {item.get('description', '')}. "
        f"24 hour price change: {item.get('price_change_24h')} percent. "
        f"Do not use an Oxford comma. Do not use an em dash or en dash. "
        f"Keep it friendly and easy to read, like a knowledgeable friend explaining it."
    )
    text = client.generate(prompt)
    return clean_style(text)


def build_source_sentence(sources):
    """
    One friendly closing sentence naming every data source used this run.
    """
    if len(sources) == 1:
        joined = sources[0]
    else:
        joined = ", ".join(sources[:-1]) + " and " + sources[-1]
    return clean_style(f"All the data and images in this post come from {joined}, pulled fresh today.")


def build_post_body(items_with_details, sources, blurb_fn=build_blurb_template):
    sections = []
    for item in items_with_details:
        blurb = blurb_fn(item)
        image_line = f"![{item['name']}]({item['image_large']})\n*Image source: CoinGecko*"
        sections.append(f"## {item['name']} ({(item.get('symbol') or '').upper()})\n\n{image_line}\n\n{blurb}")

    body = "\n\n".join(sections)
    closing = build_source_sentence(sources)
    return f"{body}\n\n---\n\n{closing}"


def build_title(items):
    lead = items[0]["name"] if items else "Today"
    return clean_style(f"Why {lead} Is Trending Today")
