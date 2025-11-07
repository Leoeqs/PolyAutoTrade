import json
import requests

class PolymarketTokenHelper:
    BASE_URL = "https://gamma-api.polymarket.com"

    def __init__(self):
        self.session = requests.Session()

    def _get(self, endpoint):
        url = f"{self.BASE_URL}{endpoint}"
        r = self.session.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

    def get_token_ids(self, slug: str):
        """
        Given a market slug (e.g. 'gold-price-over-4000-by-dec-31-2025'),
        return the outcome token IDs (Yes/No).
        """
        endpoint = f"/markets/slug/{slug}"
        try:
            data = self._get(endpoint)
        except requests.exceptions.HTTPError as e:
            print(f"❌ Error fetching market: {e}")
            return None

        if isinstance(data, dict) and "markets" in data:
            data = data["markets"][0]

        print(f"\n📊 Market: {data.get('question', 'Unknown market')}\n")

        outcomes = data.get("outcomes", [])
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except json.JSONDecodeError:
                outcomes = ["Yes", "No"]

        # ✅ Extract from clobTokenIds (real IDs)
        token_ids = []
        if "clobTokenIds" in data and isinstance(data["clobTokenIds"], str):
            try:
                token_ids = json.loads(data["clobTokenIds"])
            except json.JSONDecodeError:
                print("⚠️ Failed to parse clobTokenIds string.")
                print("Raw clobTokenIds:", data["clobTokenIds"])

        if len(token_ids) < 2:
            print("⚠️ Could not find full token IDs.")
            print("Raw keys available:", list(data.keys()))
            return None

        result = {}
        for i, name in enumerate(outcomes):
            tid = token_ids[i] if i < len(token_ids) else "N/A"
            result[name] = tid

        for name, tid in result.items():
            print(f"  {name} → {tid}")
        return result


if __name__ == "__main__":
    print("🔍 Polymarket Token Helper")
    slug = input("Enter the market slug or URL: ").strip()

    if "polymarket.com/event/" in slug:
        slug = slug.split("/event/")[-1].split("?")[0]

    helper = PolymarketTokenHelper()
    helper.get_token_ids(slug)
