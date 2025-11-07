import requests
import json
import re

GAMMA_BASE = "https://gamma-api.polymarket.com"


def clean_slug(raw_input: str) -> str:
    """Normalize user input or URL into a clean slug."""
    raw_input = raw_input.strip()

    if "polymarket.com/event/" in raw_input:
        slug = raw_input.split("/event/")[-1].split("?")[0]
        return slug.lower()

    if re.fullmatch(r"[a-z0-9\-]+", raw_input):
        return raw_input.lower()

    slug = raw_input.lower()
    slug = slug.replace("–", "-").replace("—", "-")
    slug = slug.replace("#", "number")
    slug = re.sub(r"\([^)]*\)", "", slug)
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug


def safe_float(x):
    """Convert safely to float."""
    try:
        return float(x)
    except Exception:
        return 0.0


def fetch_market_by_slug(slug: str):
    """Try fetching via slug."""
    url = f"{GAMMA_BASE}/markets/slug/{slug}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 404:
        raise FileNotFoundError(f"404 for slug {slug}")
    elif resp.status_code != 200:
        raise ValueError(f"❌ Error {resp.status_code}: {resp.text}")
    return resp.json()


def fetch_market_by_condition_id(slug: str):
    """Fallback: look up the market by searching /markets/all and matching the slug."""
    resp = requests.get(f"{GAMMA_BASE}/markets/all", timeout=15)
    if resp.status_code != 200:
        raise ValueError("❌ Failed to search markets list.")

    all_markets = resp.json()
    for m in all_markets:
        if slug in m.get("slug", "").lower() or slug in m.get("question", "").lower():
            return m

    raise FileNotFoundError(f"Market not found for slug '{slug}' even after fallback.")


def fetch_orderbook(token_id: str):
    """Fetch orderbook for a given CLOB token ID."""
    url = f"{GAMMA_BASE}/clob/orderbook?token_id={token_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        raise ValueError(f"❌ Orderbook error {resp.status_code}: {resp.text}")
    return resp.json()


def format_orderbook_side(ob_data):
    """Extract bid/ask/mid with safe float casting."""
    bids = ob_data.get("bids", [])
    asks = ob_data.get("asks", [])
    best_bid = safe_float(bids[0].get("price")) if bids else 0.0
    best_ask = safe_float(asks[0].get("price")) if asks else 1.0
    mid = (best_bid + best_ask) / 2
    return best_bid, best_ask, mid


def fetch_market_data(raw_input: str):
    """Fetch and print orderbook + metadata robustly."""
    slug = clean_slug(raw_input)

    try:
        market = fetch_market_by_slug(slug)
    except FileNotFoundError:
        print(f"⚠️ Slug '{slug}' not found — retrying via conditionId search...")
        market = fetch_market_by_condition_id(slug)

    question = market.get("question", "Unknown Market")
    end_date = market.get("endDate", "N/A")
    volume = safe_float(market.get("volume", 0))

    print(f"\n📊 Market: {question}")
    print(f"🗓️ Ends: {end_date} | 💰 Volume: ${volume:,.0f}\n")

    clob_ids_raw = market.get("clobTokenIds")
    try:
        clob_ids = json.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
    except Exception:
        raise ValueError("❌ Could not parse token IDs.")

    if not clob_ids:
        raise ValueError("❌ No token IDs found for this market.")

    results = {}
    for label, token_id in zip(["YES", "NO"], clob_ids):
        ob = fetch_orderbook(token_id)
        best_bid, best_ask, mid = format_orderbook_side(ob)
        implied_prob = round(mid * 100, 2)
        results[label] = implied_prob
        print(f"✅ {label}: bid {best_bid:.4f} | ask {best_ask:.4f} | mid {mid:.4f} → {implied_prob:.2f}%")

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
