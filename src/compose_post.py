import random
import re

# Matches em dash and en dash
DASH_PATTERN = re.compile(r"[\u2014\u2013]")

# How far past the soft length limit we're willing to look for a sentence
# ending before we give up and just cut on a word boundary.
SENTENCE_SEARCH_WINDOW = 200


def clean_style(text):
    """
    House style: no em/en dashes, no dangling Oxford-comma-before-'and'.
    """
    text = DASH_PATTERN.sub(",", text)
    text = re.sub(r",\s*and\b", " and", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def trim_to_sentence(desc, max_len=280, search_window=SENTENCE_SEARCH_WINDOW):
    """
    Trim a description to roughly max_len characters, but never mid
    sentence. Looks for the last sentence-ending punctuation at or
    shortly after max_len; if none is found it falls back to cutting
    on a word boundary and closing the sentence with a period, so we
    never ship a dangling "..." fragment.
    """
    if not desc:
        return desc
    if len(desc) <= max_len:
        return desc

    search_end = min(len(desc), max_len + search_window)
    segment = desc[:search_end]
    matches = list(re.finditer(r"[.!?](?:\s|$)", segment))
    if matches:
        end_idx = matches[-1].end()
        return desc[:end_idx].strip()

    cut = desc[:max_len]
    last_space = cut.rfind(" ")
    if last_space > 0:
        cut = cut[:last_space]
    return cut.strip() + "."


# Rotating openers so every item doesn't start with the same
# "X is trending today" phrasing. {name} and {symbol} get filled in.
OPENERS = [
    "{name} ({symbol}) is trending today.",
    "Let's talk about {name} ({symbol}), because it is on the move today.",
    "{name} ({symbol}) has caught our eye today.",
    "Next up is {name} ({symbol}), another name people are watching today.",
    "Here is why {name} ({symbol}) is on everyone's radar today.",
    "{name} ({symbol}) is one of today's big talking points.",
]


def build_blurb_template(item, index=0):
    """
    Fallback template used when no LLM key is configured. Casual,
    blog-style, one short paragraph per item. Good enough to ship
    while the pipeline is being tested; swap in build_blurb_llm once
    an LLM key is wired up in main.py for higher quality writing.

    `index` picks a different opening line for each item in the post
    (rotating through OPENERS) so the blurbs do not all start with the
    same "X is trending today" sentence.
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

    trimmed_desc = trim_to_sentence(desc, max_len=280)

    opener = OPENERS[index % len(OPENERS)].format(name=name, symbol=symbol)

    blurb = f"{opener} {market_line} {trimmed_desc}".strip()
    return clean_style(blurb)


def build_blurb_llm(item, client=None, index=0):
    """
    Optional higher quality path: call an LLM to write the blurb in a
    casual blog voice. Pass a configured client from main.py once an
    API key is available as a GitHub secret; falls back to the plain
    template otherwise so the pipeline never breaks for lack of a key.

    `index` is accepted for signature parity with build_blurb_template
    (build_post_body passes it to whichever blurb_fn is in use); the
    LLM is prompted directly to vary its own opening lines.
    """
    if client is None:
        return build_blurb_template(item, index=index)

    prompt = (
        f"Write one short, casual blog style paragraph (3 to 4 sentences) explaining "
        f"why {item['name']} ({(item.get('symbol') or '').upper()}) might be trending "
        f"today. Use this context: {item.get('description', '')}. "
        f"24 hour price change: {item.get('price_change_24h')} percent. "
        f"Do not use an Oxford comma. Do not use an em dash or en dash. "
        f"Always finish every sentence you start, never trail off with '...'. "
        f"Vary your opening line, do not always start with '{item['name']} is trending today'. "
        f"Keep it friendly and easy to read, like a knowledgeable friend explaining it."
    )
    text = client.generate(prompt)
    return clean_style(text)


def join_names(names):
    """
    Turns ['A', 'B', 'C'] into 'A, B and C' (Oxford-comma-free, matching
    house style).
    """
    names = [n for n in names if n]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


# Rotating intro templates so the opening greeting is not identical
# every single day. First-person, blog voice, no exclamation marks.
INTRO_TEMPLATES = [
    "Hey friends, welcome back. Today I'm taking a look at {lineup}, "
    "the names everyone in crypto seems to be talking about right now. "
    "Let's see why each one is trending.",

    "Hi everyone, good to have you here again. Today I'm digging into "
    "{lineup}, since these are the coins catching the most attention "
    "right now. Here's what's behind the moves.",

    "Welcome back to the blog. Today I want to walk through {lineup} "
    "and explain what's driving all the attention.",

    "Hey there, thanks for stopping by. Today's post covers {lineup}, "
    "a lineup of coins making noise in the market right now.",

    "Hello again. Today I'm breaking down {lineup} and why each of "
    "them is trending.",
]


def build_intro(items):
    """
    Warm, blogger-style opening greeting plus a one to two sentence
    heads up on what today's post covers. Picks a random template each
    run so the greeting does not read the same in every post.
    """
    names = [item["name"] for item in items]
    lineup = join_names(names)
    template = random.choice(INTRO_TEMPLATES)
    intro = template.format(lineup=lineup)
    return clean_style(intro)


def build_disclaimer():
    """
    Short reminder that trending does not mean safe or reliable. Not
    financial advice, just a heads up to be careful.
    """
    return clean_style(
        "Quick reminder before you go: just because a coin or token is "
        "trending does not mean it is safe or reliable. Always do your "
        "own research and be careful with your decisions."
    )


def build_farewell():
    """
    Short, friendly sign-off at the end of the post.
    """
    return clean_style("That is all for today's roundup, see you again tomorrow.")


def build_source_sentence(sources):
    """
    One friendly closing sentence naming every data source used this run.
    """
    if len(sources) == 1:
        joined = sources[0]
    else:
        joined = ", ".join(sources[:-1]) + " and " + sources[-1]
    return clean_style(f"By the way, all the data and images in this post are sourced from {joined}.")


def build_post_body(items_with_details, sources, blurb_fn=build_blurb_template):
    sections = []
    for index, item in enumerate(items_with_details):
        blurb = blurb_fn(item, index=index)
        image_line = f"![{item['name']}]({item['image_large']})\n*Image source: CoinGecko*"
        sections.append(f"## {item['name']} ({(item.get('symbol') or '').upper()})\n\n{image_line}\n\n{blurb}")

    intro = build_intro(items_with_details)
    body = "\n\n".join(sections)
    closing = build_source_sentence(sources)
    disclaimer = build_disclaimer()
    farewell = build_farewell()
    return f"{intro}\n\n{body}\n\n---\n\n{closing}\n\n{disclaimer}\n\n{farewell}"


def build_title(items):
    lead = items[0]["name"] if items else "Today"
    return clean_style(f"Why {lead} Is Trending Today")
