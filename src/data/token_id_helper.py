import requests
import json
import re

def clean_slug(raw_input: str) -> str:
    """
    Convert a user input (slug, title, or full URL) into a valid Polymarket slug
    that matches Gamma API formatting exactly.
    """
    raw_input = raw_input.strip()

    # Case 1: full URL — extract the slug part
    if "polymarket.com/event/" in raw_input:
        slug = raw_input.split("/event/")[-1]
        slug = slug.split("?")[0]  # remove ?tid= etc.
        return slug.lower()

    # Case 2: already a valid slug
    if re.fullmatch(r"[a-z0-9\-]+", raw_input):
        return raw_input.lower()

    # Case 3: descriptive title — normalize it
    slug = raw_input.lower()

    # Normalize punctuation and special Unicode
    slug = slug.replace("–", "-").replace("—", "-")
    slug = slug.replace("’", "'").replace("“", "").replace("”", "")
    slug = slug.replace("#", "number")  # Replace hashtags with "number"

    # Remove parentheses and their contents
    slug = re.sub(r"\([^)]*\)", "", slug)

    # Remove punctuation except hyphens and letters/numbers
    slug = re.sub(r"[^\w\s-]", "", slug)

    # Replace spaces/underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)

    # Collapse multiple hyphens
    slug = re.sub(r"-{2,}", "-", slug)

    # Trim leading/trailing hyphens
    slug = slug.strip("-")

    return slug


class PolymarketTokenHelper:
    BASE_URL = "https://gamma-api.polymarket.com"

    def __init__(self):
        self.session = requests.Session()

    def get_market_data(self, slug: str):
        """Fetch raw market data for a given slug."""
        url = f"{self.BASE_URL}/markets/slug/{slug}"
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            print(f"❌ Error fetching market: {e}")
            print(f"URL attempted: {url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error: {e}")
            return None

    def get_token_ids(self, slug: str):
        """Extract YES/NO token IDs for a given market."""
        market = self.get_market_data(slug)
        if not market:
            return None

        print(f"\n📊 Market: {market.get('question', 'Unknown Market')}\n")

        token_ids = {}

        # Primary location: top-level market object
        if "clobTokenIds" in market:
            try:
                ids = json.loads(market["clobTokenIds"])
                if len(ids) >= 2:
                    token_ids["Yes"] = ids[0]
                    token_ids["No"] = ids[1]
            except Exception:
                pass

        # Secondary location: inside events
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
                        continue

        # Display results or fallback
        if not token_ids:
            print("⚠️ Could not find token IDs. Printing data snippet for debugging:\n")
            print(json.dumps(market, indent=2)[:1200])
            return None

        for k, v in token_ids.items():
            print(f"  {k} → {v}")

        return token_ids


if __name__ == "__main__":
    print("🔍 Polymarket Token Helper")
    raw = input("Enter the market slug or URL: ").strip()
    slug = clean_slug(raw)
    helper = PolymarketTokenHelper()
    helper.get_token_ids(slug)
