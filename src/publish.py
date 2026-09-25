import os


def publish_post(title, body, tags, account, posting_key):
    """
    Publishes, or simulates publishing, a post to the target platform.

    Controlled by the DRY_RUN environment variable, which defaults to
    "true" so nothing is ever broadcast by accident. Set it to "false"
    only once the simulated output has been reviewed and looks right.
    """
    dry_run = os.getenv("DRY_RUN", "true").lower() != "false"

    if dry_run:
        print("=== SIMULATION MODE (DRY_RUN=true, nothing will be posted) ===")
        print(f"Account: {account}")
        print(f"Title: {title}")
        print(f"Tags: {tags}")
        print("Body:\n")
        print(body)
        print("\n=== End of simulated post. ===")
        return {"simulated": True, "title": title, "body": body}

    from beem import Hive

    if not account or not posting_key:
        raise RuntimeError("ACCOUNT and POSTING_KEY must be set to publish for real.")

    client = Hive(keys=[posting_key])
    permlink = (
        title.lower()
        .replace(" ", "-")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")[:255]
    )

    result = client.post(
        title=title,
        body=body,
        author=account,
        permlink=permlink,
        tags=tags,
    )
    return result
