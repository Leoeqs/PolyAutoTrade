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

    def _deep_search_token_ids(self, data):
        """Recursively find any token_id fields in nested dicts/lists."""
        token_ids = []
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ("token_id", "id") and isinstance(value, str) and value.isdigit():
                    token_ids.append(value)
                else:
                    token_ids.extend(self._deep_search_token_ids(value))
        elif isinstance(data, list):
            for item in data:
                token_ids.extend(self._deep_search_token_ids(item))
        return token_ids

    def get_token_ids(self, slug: str):
        """Fetch YES/NO token IDs for any market slug."""
        endpoint = f"/markets/slug/{slug}"
        try:
            data = self._get(endpoint)
        except requests.exceptions.HTTPError as e:
            print(f"❌ Error fetching market: {e}")
            return None

        # Unwrap "markets" array if present
        if isinstance(data, dict) and "markets" in data:
            data = data["markets"][0]

        question = data.get("question", "Unknown market")
        print(f"\n📊 Market: {question}\n")

        # Try to get outcomes
        outcomes = data.get("outcomes", [])
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except json.JSONDecodeError:
                outcomes = ["Yes", "No"]

        # Deep search for token_ids in entire response
        token_ids = self._deep_search_token_ids(data)
        if len(token_ids) >= 2:
            result = {outcomes[0]: token_ids[0], outcomes[1]: token_ids[1]}
        else:
            print("⚠️ Could not find token IDs automatically.")
            print("Raw data keys:", list(data.keys()))
            result = {outcomes[0]: "N/A", outcomes[1]: "N/A"}

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
