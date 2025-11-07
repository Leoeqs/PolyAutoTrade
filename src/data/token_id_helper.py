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
        Given a market slug, return the outcome token IDs (Yes/No).
        Works across all Polymarket response formats.
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

        # Decode stringified outcomes if needed
        outcomes = data.get("outcomes", [])
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except json.JSONDecodeError:
                # If still not valid JSON, outcomes might just be ["Yes","No"]
                outcomes = [outcomes]

        print(f"\n📊 Market: {data.get('question', 'Unknown market')}\n")

        result = {}

        # --- Case 1: Standard dict outcomes ---
        if outcomes and isinstance(outcomes[0], dict):
            for o in outcomes:
                name = o.get("name", "Unknown")
                token_id = o.get("token_id", "N/A")
                result[name] = token_id

        # --- Case 2: Simple string outcomes like ["Yes", "No"] ---
        elif outcomes and isinstance(outcomes[0], str):
            tokens = data.get("tokens") or data.get("outcomeTokens") or []
            for i, name in enumerate(outcomes):
                token_id = None
                if i < len(tokens):
                    token = tokens[i]
                    token_id = (
                        token.get("token_id")
                        if isinstance(token, dict)
                        else token
                    )
                result[name] = token_id or "N/A"

        else:
            print("⚠️ No recognizable outcomes found.")
            print("Raw data preview:", data)
            return None

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
