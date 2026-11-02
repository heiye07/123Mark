import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from app import WatermarkApp
from config import AppConfig
from favorites import FavoritesManager


class SettingsTests(unittest.TestCase):
    def test_favorites_keep_styles_and_legacy_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "favorites.json"
            favorites = FavoritesManager(path)
            favorites.add({"text": "legacy"})
            favorites.add({"text": "same", "settings": {"selected_color": "红色"}})
            favorites.add({"text": "same", "settings": {"selected_color": "蓝色"}})
            loaded = FavoritesManager(path)
            self.assertEqual(loaded.count(), 3)
            self.assertEqual(loaded.get(0)["settings"]["selected_color"], "蓝色")
            self.assertEqual(loaded.get(2)["text"], "legacy")
            loaded.get(0)["settings"]["selected_color"] = "黑色"
            self.assertEqual(loaded.get(0)["settings"]["selected_color"], "蓝色")

    def test_restart_and_favorite_restore_all_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            favorites_path = Path(directory) / "favorites.json"
            with patch("app.AppConfig", side_effect=lambda: AppConfig(config_path)), patch(
                "app.FavoritesManager", side_effect=lambda: FavoritesManager(favorites_path)
            ):
                root = tk.Tk()
                root.withdraw()
                app = WatermarkApp(root)
                expected = {
                    "watermark_text": "测试水印", "selected_color": "彩虹",
                    "selected_font_size": "72", "selected_position": "左上",
                    "opacity_var": 35, "rotation_var": -45, "margin_var": 37,
                    "tile_var": True, "tile_rows_var": 4, "tile_cols_var": 6,
                    "watermark_mode": "text", "watermark_image_path": "",
                    "watermark_image_size_var": "150%",
                }
                app._apply_watermark_settings(expected)
                app.favorites.add({"text": "测试水印", "settings": app._capture_watermark_settings()})
                app._save_config()
                if app._preview_after_id:
                    root.after_cancel(app._preview_after_id)
                root.destroy()

                root = tk.Tk()
                root.withdraw()
                try:
                    app = WatermarkApp(root)
                    self.assertEqual(app._capture_watermark_settings(), expected)
                    self.assertTrue(app.rainbow_var.get())
                    self.assertEqual(app.opacity_value.cget("text"), "35%")
                    self.assertEqual(app.rotation_value.cget("text"), "-45°")
                    self.assertEqual(app.tile_grid_frame.winfo_manager(), "pack")
                    app._on_color_click("黑色")
                    app.tile_var.set(False)
                    app._apply_watermark_settings({"watermark_mode": "image"})
                    app._refresh_favorite_combo()
                    app.fav_combo.current(0)
                    app._on_favorite_selected()
                    self.assertEqual(app._capture_watermark_settings(), expected)
                    app.favorites.add({"text": "旧收藏"})
                    app._refresh_favorite_combo()
                    app.fav_combo.current(0)
                    app._on_favorite_selected()
                    self.assertEqual(app.watermark_text.get(), "旧收藏")
                    self.assertEqual(app.selected_color.get(), "彩虹")
                finally:
                    if app._preview_after_id:
                        root.after_cancel(app._preview_after_id)
                    root.destroy()
