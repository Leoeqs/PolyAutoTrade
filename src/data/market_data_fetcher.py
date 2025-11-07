import requests
import json
import re

GAMMA_BASE = "https://gamma-api.polymarket.com"

def clean_slug(raw_input: str) -> str:
    """Normalize user input (URL, title, or slug) into a clean slug for Gamma API."""
    raw_input = raw_input.strip()

    if "polymarket.com/event/" in raw_input:
        slug = raw_input.split("/event/")[-1]
        slug = slug.split("?")[0]
        return slug.lower()

    if re.fullmatch(r"[a-z0-9\\-]+", raw_input):
        return raw_input.lower()

    slug = raw_input.lower()
    slug = slug.replace("–", "-").replace("—", "-")
    slug = slug.replace("’", "'").replace("“", "").replace("”", "")
    slug = slug.replace("#", "number")
    slug = re.sub(r"\\([^)]*\\)", "", slug)
    slug = re.sub(r"[^\\w\\s-]", "", slug)
    slug = re.sub(r"[\\s_]+", "-", slug)
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

def safe_float(value):
    """Convert safely to float even if it's None or not numeric."""
    try:
        return float(value)
    except Exception:
        return 0.0

def format_orderbook_side(ob_data):
    """Extract best bid/ask and compute midprice safely."""
    bids = ob_data.get("bids", [])
    asks = ob_data.get("asks", [])

    best_bid = safe_float(bids[0].get("price")) if bids else 0.0
    best_ask = safe_float(asks[0].get("price")) if asks else 1.0

    mid = (best_bid + best_ask) / 2
    return safe_float(best_bid), safe_float(best_ask), safe_float(mid)

def fetch_market_data(raw_input: str):
    """Fetch and print orderbook + metadata for any valid market input."""
    slug = clean_slug(raw_input)
    market = fetch_market(slug)

    question = market.get("question", "Unknown Market")
    end_date = market.get("endDate", "N/A")
    volume = market.get("volume", 0)

    print(f"\n📊 Market: {question}")
    print(f"🗓️ Ends: {end_date} | 💰 Volume: ${safe_float(volume):,.0f}\n")

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

        # 👇 Every value is explicitly cast to float here
        print(f"✅ {label}: bid {float(best_bid):.4f} | ask {float(best_ask):.4f} | mid {float(mid):.4f} → {implied_prob:.2f}%")

    if "YES" in results and "NO" in results:
        print(f"\n🧮 YES + NO = {float(results['YES'] + results['NO']):.2f}% (skew {abs(results['YES'] + results['NO'] - 100):.2f}%)")

if __name__ == "__main__":
    print("📈 Polymarket Market Data Fetcher")
    raw = input("Enter working market slug or URL: ").strip()
    try:
        fetch_market_data(raw)
    except Exception as e:
        print(f"❌ {e}")
