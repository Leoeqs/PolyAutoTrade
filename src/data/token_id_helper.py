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

        # Handle array wrapper if present
        if isinstance(data, dict) and "markets" in data:
            data = data["markets"][0]

        print(f"\n📊 Market: {data.get('question', 'Unknown market')}\n")

        # Try to extract outcomes
        outcomes = data.get("outcomes", [])
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except json.JSONDecodeError:
                outcomes = ["Yes", "No"]

        # --- Search for full token IDs under "outcomeTokens" or "tokens" ---
        token_ids = []
        if "outcomeTokens" in data:
            token_ids = [t.get("token_id") for t in data["outcomeTokens"] if isinstance(t, dict)]
        elif "tokens" in data:
            token_ids = [t.get("token_id") for t in data["tokens"] if isinstance(t, dict)]

        # --- Print debug info if needed ---
        if not token_ids or any(tid is None for tid in token_ids):
            print("⚠️ Could not directly find long token IDs.")
            print("Inspecting data keys for clarity...")
            if "outcomeTokens" in data:
                print(json.dumps(data["outcomeTokens"], indent=2))
            else:
                print(json.dumps(data, indent=2))
            return None

        # --- Map outcomes to token IDs ---
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

    # Allow full URLs too
    if "polymarket.com/event/" in slug:
        slug = slug.split("/event/")[-1].split("?")[0]

    helper = PolymarketTokenHelper()
    helper.get_token_ids(slug)
