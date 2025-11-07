import requests
import json
import re

def clean_slug(raw_input: str) -> str:
    """Cleans any Polymarket input (title or URL) into a Gamma slug candidate."""
    raw_input = raw_input.strip()

    # Case 1: Full URL (https://polymarket.com/event/...?...tid=)
    if "polymarket.com/event/" in raw_input:
        slug = raw_input.split("/event/")[-1]
        slug = slug.split("?")[0]  # remove ?tid= if present
        return slug.lower()

    # Case 2: already looks like a valid slug
    if re.match(r"^[a-z0-9\-]+$", raw_input):
        return raw_input.lower()

    # Case 3: natural-language title
    slug = raw_input.lower()
    slug = slug.replace("#", "number")  # convert hashtags
    slug = re.sub(r"\([^)]*\)", "", slug)  # remove parentheses and contents
    slug = re.sub(r"[^a-z0-9]+", "-", slug)  # replace non-alphanumerics with hyphens
    slug = slug.strip("-")
    slug = re.sub(r"-+", "-", slug)  # collapse multiple dashes
    return slug


class PolymarketTokenHelper:
    BASE_URL = "https://gamma-api.polymarket.com"

    def __init__(self):
        self.session = requests.Session()

    def get_market_data(self, slug: str):
        """Fetch raw market data, with automatic fallback title search."""
        url = f"{self.BASE_URL}/markets/slug/{slug}"
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 404:
                print("🔁 Slug not found — trying fallback title search...")
                search_url = f"{self.BASE_URL}/markets?limit=15&search={slug}"
                search_resp = self.session.get(search_url, timeout=10)
                search_resp.raise_for_status()
                results = search_resp.json()

                if isinstance(results, list) and results:
                    print(f"✅ Found possible match: {results[0].get('question', 'Unknown')}")
                    return results[0]
                else:
                    print("❌ No results found for fallback search.")
                    return None

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching market: {e}")
            return None

    def get_token_ids(self, slug: str):
        """Extract YES/NO token IDs from a given market."""
        market = self.get_market_data(slug)
        if not market:
            return None

        print(f"\n📊 Market: {market.get('question', 'Unknown Market')}\n")

        token_ids = {}

        # Main location
        if "clobTokenIds" in market:
            try:
                ids = json.loads(market["clobTokenIds"])
                if len(ids) >= 2:
                    token_ids["Yes"] = ids[0]
                    token_ids["No"] = ids[1]
            except Exception:
                print("⚠️ Failed to parse clobTokenIds.")

        # Secondary fallback: nested 'events'
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
            print("⚠️ Could not locate token IDs. Dumping first 1500 chars for debug:")
            print(json.dumps(market, indent=2)[:1500])
            return None

        for k, v in token_ids.items():
            print(f"  {k} → {v}")

        return token_ids


if __name__ == "__main__":
    print("🔍 Polymarket Token Helper")
    raw = input("Enter the market slug or URL: ")
    slug = clean_slug(raw)
    helper = PolymarketTokenHelper()
    helper.get_token_ids(slug)
