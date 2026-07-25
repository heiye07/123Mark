import tempfile
import unittest
from pathlib import Path

from config import AppConfig
from favorites import FavoritesManager


class StorageTests(unittest.TestCase):
    def test_config_round_trip_and_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            config = AppConfig(path)
            self.assertEqual(config.get("output_format"), "保持原格式")
            self.assertTrue(config.set("output_quality", 88))
            self.assertEqual(AppConfig(path).get("output_quality"), 88)

    def test_favorites_limit_deduplication_and_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FavoritesManager(Path(temp_dir) / "favorites.json", max_items=3)
            for index in range(4):
                manager.add({"name": str(index), "text": f"text-{index}"})
            self.assertEqual(manager.count(), 3)
            self.assertEqual(manager.get(0)["text"], "text-3")
            manager.add({"name": "renamed", "text": "text-2"})
            self.assertEqual(manager.get(0)["name"], "renamed")
            self.assertEqual(manager.count(), 3)


if __name__ == "__main__":
    unittest.main()
