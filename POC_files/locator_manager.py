import json
from pathlib import Path


class LocatorManager:
    def __init__(self, base_dir=None):
        # Base dir should be the directory containing self_healing_locators/
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.locator_dir = self.base_dir / "self_healing_locators"

    def load_locators(self, page):
        """Load locator mapping for a specific page"""
        path = self.locator_dir / f"{page}.json"
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_all_locators(self, key, page):
        """
        Return list of locators (original + fallbacks) for a given key and page.
        """
        locators = self.load_locators(page)
        if key not in locators:
            return []
        data = locators[key]
        return [data["original"]] + data.get("alternatives", [])

    def remember_successful_locator(self, key, working_locator, page="fallback"):
        """
        If a fallback locator worked, update fallback.json with it for future use.
        """
        fallback_path = self.locator_dir / f"{page}.json"
        fallback_data = {}

        if fallback_path.exists():
            with open(fallback_path, "r", encoding="utf-8") as f:
                fallback_data = json.load(f)

        if key not in fallback_data:
            fallback_data[key] = {
                "original": working_locator,
                "alternatives": []
            }
        else:
            if working_locator != fallback_data[key]["original"] and working_locator not in fallback_data[key]["alternatives"]:
                fallback_data[key]["alternatives"].insert(0, working_locator)

        with open(fallback_path, "w", encoding="utf-8") as f:
            json.dump(fallback_data, f, indent=2)
