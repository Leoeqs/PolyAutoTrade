import requests
import json
import re
import os
from datetime import datetime

GAMMA_BASE = "https://gamma-api.polymarket.com"
CLOB_BASE = "https://clob.polymarket.com"
OUTPUT_DIR = "data/orderbooks"


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
    try:
        return float(x)
    except Exception:
        return 0.0


def fetch_market_by_slug(slug: str):
    url = f"{GAMMA_BASE}/markets/slug/{slug}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 404:
        raise FileNotFoundError(f"404 for slug {slug}")
    elif resp.status_code != 200:
        raise ValueError(f"❌ Error {resp.status_code}: {resp.text}")
    return resp.json()


def fetch_market_by_condition_id(slug: str):
    resp = requests.get(f"{GAMMA_BASE}/markets/all", timeout=15)
    if resp.status_code != 200:
        raise ValueError("❌ Failed to fetch markets list.")
    for m in resp.json():
        if slug in m.get("slug", "").lower() or slug in m.get("question", "").lower():
            return m
    raise FileNotFoundError(f"Market not found for slug '{slug}'.")


def fetch_orderbook(token_id: str):
    """Fetch the full CLOB orderbook for a given token."""
    url = f"{CLOB_BASE}/book"
    params = {"token_id": token_id}
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code == 404:
        raise FileNotFoundError(f"404: Book not found for token_id {token_id}")
    elif resp.status_code != 200:
        raise ValueError(f"❌ Orderbook error {resp.status_code}: {resp.text}")
    return resp.json()


def normalize_price(p):
    """Convert micro-units to standard decimals."""
    return safe_float(p) / 1_000_000


def summarize_orderbook(label, ob_data):
    """Print detailed orderbook info for debugging/trading logic."""
    bids = ob_data.get("bids", [])
    asks = ob_data.get("asks", [])

    if not bids or not asks:
        print(f"⚠️ No orderbook data for {label} (empty side).")
        return

    top_bid = normalize_price(bids[0]["price"])
    top_ask = normalize_price(asks[0]["price"])
    mid = (top_bid + top_ask) / 2
    print(f"✅ {label} Top of Book → bid {top_bid:.4f} | ask {top_ask:.4f} | mid {mid:.4f} ({mid*100:.2f}%)")

    print(f"📊 {label} Depth Snapshot (top 5 each):")
    print("  Bids:")
    for b in bids[:5]:
        print(f"   • {normalize_price(b['price']):.4f}  x  {b['size']}")
    print("  Asks:")
    for a in asks[:5]:
        print(f"   • {normalize_price(a['price']):.4f}  x  {a['size']}")
    print()


def save_orderbook(slug, market_name, orderbooks):
    """Save full orderbook JSON to data/orderbooks/<slug>.json"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(OUTPUT_DIR, f"{slug}.json")
    with open(filename, "w") as f:
        json.dump(
            {
                "market": market_name,
                "timestamp": datetime.utcnow().isoformat(),
                "orderbooks": orderbooks,
            },
            f,
            indent=2,
        )
    print(f"💾 Orderbook saved to {filename}")


def fetch_market_data(raw_input: str):
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

    all_books = {}
    for label, token_id in zip(["YES", "NO"], clob_ids):
        try:
            ob = fetch_orderbook(token_id)
            summarize_orderbook(label, ob)
            all_books[label] = ob
        except Exception as e:
            print(f"❌ Could not fetch orderbook for {label}: {e}")

    save_orderbook(slug, question, all_books)


if __name__ == "__main__":
    print("📈 Polymarket Market Data Fetcher")
    raw = input("Enter working market slug or URL: ").strip()
    try:
        fetch_market_data(raw)
    except Exception as e:
        print(f"❌ {e}")
