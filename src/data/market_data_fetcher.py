import requests
import json
from datetime import datetime

GAMMA_BASE = "https://gamma-api.polymarket.com"

def fetch_market(slug_or_id: str):
    """Fetch full market object from Gamma API using slug or ID."""
    url = f"{GAMMA_BASE}/markets/slug/{slug_or_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        raise ValueError(f"Error {resp.status_code}: {resp.text}")
    return resp.json()

def fetch_orderbook(token_id: str):
    """Fetch live orderbook for a CLOB token ID."""
    url = f"{GAMMA_BASE}/clob/orderbook?token_id={token_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        raise ValueError(f"Error {resp.status_code}: {resp.text}")
    return resp.json()

def format_orderbook_side(side):
    """Return best bid, best ask, and mid for a given side dict."""
    bids = side.get("bids", [])
    asks = side.get("asks", [])
    best_bid = float(bids[0]["price"]) if bids else 0.0
    best_ask = float(asks[0]["price"]) if asks else 1.0
    mid = round((best_bid + best_ask) / 2, 4)
    return best_bid, best_ask, mid

def fetch_market_data(slug_or_id: str):
    """Fetch metadata + orderbook info for both tokens."""
    market = fetch_market(slug_or_id)
    question = market.get("question")
    end_date = market.get("endDate")
    volume = market.get("volume", 0)
    clob_ids = json.loads(market["clobTokenIds"])

    print(f"\n📊 Market: {question}")
    print(f"🗓️ Ends: {end_date} | 💰 Volume: ${volume:,.0f}\n")

    results = {}
    for label, token_id in zip(["YES", "NO"], clob_ids):
        ob = fetch_orderbook(token_id)
        bids, asks, mid = format_orderbook_side(ob)
        results[label] = {
            "token_id": token_id,
            "best_bid": bids,
            "best_ask": asks,
            "mid": mid,
            "implied_prob": round(mid * 100, 2),
        }
        print(f"{label}: {bids} / {asks} → mid {mid} ({mid*100:.2f}%)")

    return results


if __name__ == "__main__":
    slug = input("Enter working market slug or URL: ").strip()
    # Example: will-satoshi-move-any-bitcoin-in-2025
    try:
        fetch_market_data(slug)
    except Exception as e:
        print(f"❌ {e}")
