# daily-content-bot

Posts a daily English-language article about today's trending items,
with one short casual paragraph per item, a sourced image per item,
and a single closing sentence naming the data sources used.

## How it works

1. `src/fetch_signals.py` pulls today's trending items from a free,
   no-key market data endpoint.
2. `src/fetch_details.py` fetches each item's short description and
   24h change data, used as the raw material for the "why is this
   trending" explanation.
3. `src/compose_post.py` turns that into a casual blog-style post,
   strips em/en dashes, avoids the Oxford comma, and builds the
   closing "data sourced from..." sentence automatically.
4. `src/publish.py` either prints a simulated post (default) or
   broadcasts it live.
5. `main.py` wires the four steps together.
6. `.github/workflows/daily-post.yml` runs `main.py` once a day via
   GitHub Actions, and can also be triggered manually.

## Setup

1. Push this repo to GitHub.
2. In **Settings → Secrets and variables → Actions**, add:
   - `ACCOUNT`: the account that will post.
   - `POSTING_KEY`: that account's **posting-level** key only (never
     an active/owner/master key).
3. By default every run is a **simulation**: it prints the title, tags
   and full body to the workflow log but posts nothing. This is
   controlled by `DRY_RUN` (defaults to `true`).

## Testing locally

```bash
pip install -r requirements.txt
python main.py
```

With no `DRY_RUN` set, this prints a simulated post to your terminal.
Nothing is published.

## Testing on GitHub before going live

1. Push the repo.
2. Go to **Actions → Daily Content Post → Run workflow**.
3. Leave `dry_run` as `true` and run it.
4. Open the run's log and check the simulated title, tags and body.

## Going live

Once the simulated output looks right, either:

- Trigger the workflow manually with `dry_run` set to `false`, or
- Add a repository variable `DRY_RUN=false` so the daily scheduled
  run also publishes for real (the manual `dry_run` input still
  overrides this when you run the workflow by hand).

## Optional: higher quality writing with an LLM

`src/compose_post.py` ships a plain template (`build_blurb_template`)
that needs no extra key. `build_blurb_llm` is a drop-in replacement
that calls an LLM for better prose; wire up a client in `main.py` and
pass it through once you add an API key as a GitHub secret.

## Notes

- The market data provider's free tier is rate limited, so
  `fetch_details_for_items` pauses briefly between calls. If you
  raise `NUM_ITEMS` in `main.py`, you may need a longer delay.
- Only ever use a posting-level key, not an active/owner/master key.
