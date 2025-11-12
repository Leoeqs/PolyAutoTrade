import requests
import json

CLOB_BASE = "https://clob.polymarket.com"

def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None

def get_orderbook(token_id: str):
    """Fetch orderbook for the given Polymarket token-ID."""
    url = f"{CLOB_BASE}/book"
    params = {"token_id": token_id}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data

if __name__ == "__main__":
    token_id = input("Enter token_id: ").strip()
    book = get_orderbook(token_id)
    print(json.dumps(book, indent=2))

    # Example: extract top bid/ask
    bids = book.get("bids", [])
    asks = book.get("asks", [])
    if bids:
        print("Top bid price:", bids[0].get("price"), "size:", bids[0].get("size"))
    if asks:
        print("Top ask price:", asks[0].get("price"), "size:", asks[0].get("size"))

