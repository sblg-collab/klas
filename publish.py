import os
import re
from datetime import datetime, timezone


def get_recent_titles(account, limit=10):
    """
    Returns the titles of the account's most recent posts (newest first),
    or an empty list if Hive can't be reached. Read-only, needs no key.
    """
    if not account:
        return []
    try:
        from beem import Hive
        from beem.account import Account

        acc = Account(account, blockchain_instance=Hive())
        titles = []
        for entry in acc.get_blog(limit=limit):
            if entry["author"] == account and entry["title"]:
                titles.append(entry["title"])
        return titles
    except Exception as exc:
        print(f"Could not fetch recent titles: {exc}")
        return []


def make_permlink(title):
    """Title to URL slug: lowercase letters, digits and hyphens only."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:200] or "post"


def permlink_exists(account, permlink, client):
    from beem.comment import Comment

    try:
        Comment(f"@{account}/{permlink}", blockchain_instance=client)
        return True
    except Exception:
        return False


def unique_permlink(account, title, client):
    """
    Hive treats a repeated permlink as an EDIT of the old post, so never
    reuse one. Try the plain slug first; if that URL is taken, add the
    date, and if that is taken too, add the time as well.
    """
    base = make_permlink(title)
    now = datetime.now(timezone.utc)
    candidates = [
        base,
        f"{base}-{now:%Y%m%d}",
        f"{base}-{now:%Y%m%d-%H%M%S}",
    ]
    for candidate in candidates:
        if not permlink_exists(account, candidate, client):
            return candidate
    return candidates[-1]


def publish_post(title, body, tags, account, posting_key, app_name="hive"):
    """
    Publishes, or simulates publishing, a post to the target platform.

    Controlled by the DRY_RUN environment variable, which defaults to
    "true" so nothing is ever broadcast by accident. Set it to "false"
    only once the simulated output has been reviewed and looks right.

    app_name is written to the post's json_metadata ("app" field). beem
    would otherwise stamp it as "beem/<version>".
    """
    dry_run = os.getenv("DRY_RUN", "true").lower() != "false"

    if dry_run:
        print("=== SIMULATION MODE (DRY_RUN=true, nothing will be posted) ===")
        print(f"Account: {account}")
        print(f"Title: {title}")
        print(f"Tags: {tags}")
        print(f"App: {app_name}")
        print("Body:\n")
        print(body)
        print("\n=== End of simulated post. ===")
        return {"simulated": True, "title": title, "body": body}

    from beem import Hive

    if not account or not posting_key:
        raise RuntimeError("ACCOUNT and POSTING_KEY must be set to publish for real.")

    client = Hive(keys=[posting_key])
    permlink = unique_permlink(account, title, client)
    print(f"Permlink: {permlink}")

    result = client.post(
        title=title,
        body=body,
        author=account,
        permlink=permlink,
        tags=tags,
        app=app_name,
    )
    return result
