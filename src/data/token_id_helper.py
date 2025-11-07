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

        # Handle possible 'markets' array
        if isinstance(data, dict) and "markets" in data:
            data = data["markets"][0]

        outcomes = data.get("outcomes", [])
        
        # 🧠 FIX: Sometimes Polymarket returns outcomes as a stringified JSON
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except json.JSONDecodeError:
                print("❌ Could not parse outcomes string as JSON.")
                print("Raw outcomes string:", outcomes)
                return None

        if not outcomes or not isinstance(outcomes, list):
            print("⚠️ No valid outcomes found for this slug.")
            print("Raw data preview:", data)
            return None

        print(f"\n📊 Market: {data.get('question', 'Unknown market')}\n")

        result = {}
        for i, o in enumerate(outcomes):
            if isinstance(o, dict):
                name = o.get("name", f"Outcome {i+1}")
                token_id = o.get("token_id", "N/A")
                print(f"  {name} → {token_id}")
                result[name] = token_id
            else:
                print(f"⚠️ Unexpected outcome type: {type(o)}")
                print("  Raw outcome value:", o)
        return result


if __name__ == "__main__":
    print("🔍 Polymarket Token Helper")
    slug = input("Enter the market slug or URL: ").strip()

    # Optional: allow full URLs too
    if "polymarket.com/event/" in slug:
        slug = slug.split("/event/")[-1].split("?")[0]

    helper = PolymarketTokenHelper()
    helper.get_token_ids(slug)
