import requests
from src.data.token_id_helper import PolymarketTokenHelper

class MarketDataFetcher:
    BASE_URL = "https://gamma-api.polymarket.com"

    def __init__(self):
        self.session = requests.Session()
        self.token_helper = PolymarketTokenHelper()

    def _get(self, endpoint, params=None):
        """Internal helper for GET requests."""
        url = f"{self.BASE_URL}{endpoint}"
        r = self.session.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()

    def get_orderbook(self, token_id: str):
        """
        Fetch full orderbook for a given token_id.
        Returns all bids/asks as lists of [price, size].
        """
        data = self._get("/orderbook", params={"token_id": token_id})
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        return {"bids": bids, "asks": asks}

    def get_market_snapshot(self, slug: str):
        """
        Given a market slug, fetch the full orderbooks (YES & NO)
        and also show top 4 levels for reference.
        """
        # 1️⃣ Get token IDs from your helper
        token_map = self.token_helper.get_token_ids(slug)
        if not token_map:
            print("⚠️ Could not fetch token IDs for slug:", slug)
            return None

        # 2️⃣ Fetch market metadata for the question text
        market_data = self._get(f"/markets/slug/{slug}")
        if isinstance(market_data, dict) and "markets" in market_data:
            market_data = market_data["markets"][0]
        question = market_data.get("question", "Unknown market")

        # 3️⃣ Build snapshot with full orderbook data
        snapshot = {"question": question, "slug": slug, "orderbooks": {}}

        for outcome_name, token_id in token_map.items():
            full_ob = self.get_orderbook(token_id)
            snapshot["orderbooks"][outcome_name] = full_ob

        return snapshot


if __name__ == "__main__":
    print("🔍 Polymarket Market Data Fetcher")
    slug = input("Enter the market slug: ").strip()
    fetcher = MarketDataFetcher()
    snapshot = fetcher.get_market_snapshot(slug)
    if snapshot:
        print(f"\n📊 {snapshot['question']}")
        for outcome, ob in snapshot["orderbooks"].items():
            print(f"\n📈 {outcome} Orderbook (showing top 4 levels):")
            print("  Bids:", ob["bids"][:4])
            print("  Asks:", ob["asks"][:4])
            print(f"  Total bids: {len(ob['bids'])}, total asks: {len(ob['asks'])}")

