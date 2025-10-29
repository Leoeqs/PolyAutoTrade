#helper agent that returns the live price of sol updated every second

import time
import os
import requests

BINANCE_URL = "https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT"  # no key needed
COINBASE_URL = "https://api.exchange.coinbase.com/products/SOL-USD/ticker"  # fallback

HEADERS = {"User-Agent": "sol-price-tracker/1.0"}

def get_price_binance():
    r = requests.get(BINANCE_URL, headers=HEADERS, timeout=5)
    r.raise_for_status()
    data = r.json()
    # price is a string like "152.43000000"
    return float(data["price"])

def get_price_coinbase():
    r = requests.get(COINBASE_URL, headers=HEADERS, timeout=5)
    r.raise_for_status()
    data = r.json()
    # "price" is a string
    return float(data["price"])

def get_sol_price():
    # Try Binance first (very high limits), then Coinbase as a backup
    try:
        return get_price_binance(), "Binance"
    except Exception:
        try:
            return get_price_coinbase(), "Coinbase"
        except Exception as e:
            raise RuntimeError(f"All sources failed: {e}")

if __name__ == "__main__":
    while True:
        try:
            price, source = get_sol_price()
            print(f"💰 Live SOL Price: ${price:,.2f}  (source: {source})")
        except Exception as e:
            print("Error fetching price:", e)
        time.sleep(1)
