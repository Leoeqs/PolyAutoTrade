import requests
import json
import re

GAMMA_BASE = "https://gamma-api.polymarket.com"


def clean_slug(raw_input: str) -> str:
    """Normalize user input (URL, title, or slug) into a clean slug for Gamma API."""
    raw_input = raw_input.strip()

    # Case 1: Full URL (extract the /event/ part)
    if "polymarket.com/event/" in raw_input:
        slug = raw_input.split("/event/")[-1]
        slug = slug.split("?")[0]
        return slug.lower()

    # Case 2: already looks like a slug
    if re.fullmatch(r"[a-z0-9\-]+", raw_input):
        return raw_input.lower()

    # Case 3: normalize title text
    slug = raw_input.lower()
    slug = slug.replace("–", "-").replace("—", "-")
    slug = slug.replace("’", "'").replace("“", "").replace("”", "")
    slug = slug.replace("#", "number")
    slug = re.sub(r"\([^)]*\)", "", slug)
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    return slug


def fetch_market(slug_or_id: str):
    """Fetch market JSON from Gamma API via slug."""
    url = f"{GAMMA_BASE}/markets/slug/{slug_or_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        raise ValueError(f"❌ Error {resp.status_code}: {resp.text}")
    return resp.json()


def fetch_orderbook(token_id: str):
    """Fetch orderbook data for a given CLOB token ID."""
    url = f"{GAMMA_BASE}/clob/orderbook?token_id={token_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        raise ValueError(f"❌ Error {resp.status_code}: {resp.text}")
    return resp.json()


def safe_float(x):
    """Convert a string or numeric input safely to float."""
    try:
        return float(x)
    except Exception:
        return 0.0


def format_orderbook_side(ob_data):
    """Extract best bid/ask and compute midprice."""
    bids = ob_data.get("bids", [])
    asks = ob_data.get("asks", [])
    best_bid = safe_float(bids[0]["price"]) if bids else 0.0
    best_ask = safe_float(asks[0]["price"]) if asks else 1.0
    mid = round((best_bid + best_ask) / 2, 4)
    return best_bid, best_ask, mid


def fetch_market_data(raw_input: str):
    """Fetch and print orderbook + metadata for any valid market input."""
    slug = clean_slug(raw_input)
    market = fetch_market(slug)

    question = market.get("question", "Unknown Market")
    end_date = market.get("endDate", "N/A")
    volume = market.get("volume", 0)

    print(f"\n📊 Market: {question}")
    print(f"🗓️ Ends: {end_date} | 💰 Volume: ${volume:,.0f}\n")

    try:
        clob_ids = json.loads(market["clobTokenIds"])
    except Exception:
        raise ValueError("❌ Could not parse token IDs from market JSON.")

    results = {}
    for label, token_id in zip(["YES", "NO"], clob_ids):
        ob = fetch_orderbook(token_id)
        best_bid, best_ask, mid = format_orderbook_side(ob)
        implied_prob = round(mid * 100, 2)
        results[label] = implied_prob
        print(f"✅ {label}: bid {best_bid:.3f} | ask {best_ask:.3f} | mid {mid:.3f} → {implied_prob:.2f}%")

    # Optional summary line
    if "YES" in results and "NO" in results:
        print(f"\n🧮 Check: YES + NO = {results['YES'] + results['NO']:.2f}% (market skew {abs(results['YES'] + results['NO'] - 100):.2f}%)")


if __name__ == "__main__":
    print("📈 Polymarket Market Data Fetcher")
    raw = input("Enter working market slug or URL: ").strip()
    try:
        fetch_market_data(raw)
    except Exception as e:
        print(e)
