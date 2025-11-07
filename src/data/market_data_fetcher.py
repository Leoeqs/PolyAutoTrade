import requests
import json
import re

GAMMA_BASE = "https://gamma-api.polymarket.com"
CLOB_BASE = "https://clob.polymarket.com"


def clean_slug(raw_input: str) -> str:
    """Normalize user input or URL into a clean Polymarket slug."""
    raw_input = raw_input.strip()

    if "polymarket.com/event/" in raw_input:
        slug = raw_input.split("/event/")[-1].split("?")[0]
        return slug.lower()

    if re.fullmatch(r"[a-z0-9\\-]+", raw_input):
        return raw_input.lower()

    slug = raw_input.lower()
    slug = slug.replace("–", "-").replace("—", "-")
    slug = slug.replace("#", "number")
    slug = re.sub(r"\\([^)]*\\)", "", slug)
    slug = re.sub(r"[^\\w\\s-]", "", slug)
    slug = re.sub(r"[\\s_]+", "-", slug).strip("-")
    return slug


def safe_float(x):
    """Safely convert to float, fallback to 0.0."""
    try:
        return float(x)
    except Exception:
        return 0.0


def fetch_market_by_slug(slug: str):
    """Fetch market data using the Gamma API slug endpoint."""
    url = f"{GAMMA_BASE}/markets/slug/{slug}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 404:
        raise FileNotFoundError(f"404 for slug {slug}")
    elif resp.status_code != 200:
        raise ValueError(f"❌ Error {resp.status_code}: {resp.text}")
    return resp.json()


def fetch_market_by_condition_id(slug: str):
    """Fallback: search all markets if the slug fails."""
    resp = requests.get(f"{GAMMA_BASE}/markets/all", timeout=15)
    if resp.status_code != 200:
        raise ValueError("❌ Failed to fetch markets list.")
    all_markets = resp.json()
    for m in all_markets:
        if slug in m.get("slug", "").lower() or slug in m.get("question", "").lower():
            return m
    raise FileNotFoundError(f"Market not found for slug '{slug}' even after fallback.")


def fetch_orderbook(token_id: str):
    """Fetch orderbook data from the correct CLOB endpoint."""
    url = f"{CLOB_BASE}/book"
    params = {"token_id": token_id}
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code == 404:
        raise FileNotFoundError(f"404: Book not found for token_id {token_id}")
    elif resp.status_code != 200:
        raise ValueError(f"❌ Orderbook error {resp.status_code}: {resp.text}")
    return resp.json()


def format_orderbook(ob_data):
    """Extract best bid, ask, and mid values from CLOB data."""
    bids = ob_data.get("bids", [])
    asks = ob_data.get("asks", [])

    best_bid = safe_float(bids[0]["price"]) if bids else 0.0
    best_ask = safe_float(asks[0]["price"]) if asks else 1.0
    mid = round((best_bid + best_ask) / 2, 4)

    return best_bid, best_ask, mid


def fetch_market_data(raw_input: str):
    """Main function to fetch and print market/orderbook data."""
    slug = clean_slug(raw_input)

    try:
        market = fetch_market_by_slug(slug)
    except FileNotFoundError:
        print(f"⚠️ Slug '{slug}' not found — retrying with fallback search...")
        market = fetch_market_by_condition_id(slug)

    question = market.get("question", "Unknown Market")
    end_date = market.get("endDate", "N/A")
    volume = safe_float(market.get("volume", 0))

    print(f"\n📊 Market: {question}")
    print(f"🗓️ Ends: {end_date} | 💰 Volume: ${volume:,.0f}\n")

    clob_ids_raw = market.get("clobTokenIds")
    if not clob_ids_raw:
        raise ValueError("❌ No token IDs found for this market.")

    try:
        clob_ids = json.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
    except Exception:
        raise ValueError("❌ Failed to parse CLOB token IDs.")

    results = {}
    for label, token_id in zip(["YES", "NO"], clob_ids):
        try:
            ob = fetch_orderbook(token_id)
            best_bid, best_ask, mid = format_orderbook(ob)
            implied_prob = round(mid * 100, 2)
            results[label] = implied_prob
            print(f"✅ {label}: bid {best_bid:.4f} | ask {best_ask:.4f} | mid {mid:.4f} → {implied_prob:.2f}%")
        except Exception as e:
            print(f"❌ Could not fetch orderbook for {label}: {e}")

    if "YES" in results and "NO" in results:
        total = results["YES"] + results["NO"]
        skew = abs(total - 100)
        print(f"\n🧮 YES + NO = {total:.2f}% (skew {skew:.2f}%)")


if __name__ == "__main__":
    print("📈 Polymarket Market Data Fetcher")
    raw = input("Enter working market slug or URL: ").strip()
    try:
        fetch_market_data(raw)
    except Exception as e:
        print(f"❌ {e}")
