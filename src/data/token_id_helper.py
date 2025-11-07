import requests
import json
import re

def clean_slug(raw_input: str) -> str:
    """Cleans a user-provided Polymarket URL or title into a valid Gamma slug."""
    raw_input = raw_input.strip()

    # Case 1: full URL (e.g., https://polymarket.com/event/will-satoshi-move-any-bitcoin-in-2025?tid=...)
    if "polymarket.com/event/" in raw_input:
        slug = raw_input.split("/event/")[-1]
        slug = slug.split("?")[0]  # remove ?tid= if present
        return slug.lower()

    # Case 2: already safe slug
    if re.match(r"^[a-z0-9\-]+$", raw_input):
        return raw_input.lower()

    # Case 3: full title (contains spaces or punctuation)
    slug = raw_input.lower()
    slug = slug.replace("#", "number")  # handle hashtags
    slug = re.sub(r"[^a-z0-9]+", "-", slug)  # replace punctuation/spaces with dashes
    slug = slug.strip("-")
    slug = re.sub(r"-+", "-", slug)  # collapse multiple dashes
    return slug

class PolymarketTokenHelper:
    BASE_URL = "https://gamma-api.polymarket.com"

    def __init__(self):
        self.session = requests.Session()

    def get_market_data(self, slug: str):
        """Fetch raw market data from Polymarket Gamma API."""
        url = f"{self.BASE_URL}/markets/slug/{slug}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching market: {e}")
            return None

    def get_token_ids(self, slug: str):
        """Extract YES/NO token IDs (long form) from a given market."""
        market = self.get_market_data(slug)
        if not market:
            return None

        print(f"\n📊 Market: {market.get('question', 'Unknown Market')}\n")

        token_ids = {}

        # Look inside known key paths for IDs
        if "clobTokenIds" in market:
            try:
                ids = json.loads(market["clobTokenIds"])
                if len(ids) >= 2:
                    token_ids["Yes"] = ids[0]
                    token_ids["No"] = ids[1]
            except Exception:
                print("⚠️ Could not parse clobTokenIds")

        # Fallback: look inside 'events' or nested data
        if not token_ids and "events" in market:
            for ev in market["events"]:
                if "clobTokenIds" in ev:
                    try:
                        ids = json.loads(ev["clobTokenIds"])
                        if len(ids) >= 2:
                            token_ids["Yes"] = ids[0]
                            token_ids["No"] = ids[1]
                            break
                    except Exception:
                        pass

        if not token_ids:
            print("⚠️ Could not directly find long token IDs.")
            print("Inspecting data keys for clarity...")
            print(json.dumps(market, indent=2)[:1500])  # shortened dump for debugging
            return None

        for outcome, tid in token_ids.items():
            print(f"  {outcome} → {tid}")

        return token_ids


if __name__ == "__main__":
    print("🔍 Polymarket Token Helper")
    raw_input = input("Enter the market slug or URL: ")
    slug = clean_slug(raw_input)
    helper = PolymarketTokenHelper()
    helper.get_token_ids(slug)
