import tempfile
import unittest
from pathlib import Path

from PIL import Image

from engine import (
    RAINBOW_COLORS,
    apply_watermark,
    create_image_watermark_layer,
    create_text_watermark_layer,
    get_rainbow_color,
    process_image,
)


class EngineTests(unittest.TestCase):
    def test_rainbow_keeps_expected_end_colors(self):
        self.assertEqual(get_rainbow_color(0), RAINBOW_COLORS[0])
        self.assertEqual(get_rainbow_color(1), RAINBOW_COLORS[-1])

    def test_rainbow_text_has_multiple_visible_colors(self):
        layer = create_text_watermark_layer("123Mark 彩虹", font_size=48, opacity=220, rainbow=True)
        colors = {
            pixel[:3]
            for pixel in layer.get_flattened_data()
            if pixel[3] > 100
        }
        self.assertGreater(len(colors), 6)

    def test_tile_rows_and_columns_reach_all_grid_positions(self):
        base = Image.new("RGBA", (100, 80), "white")
        watermark = Image.new("RGBA", (5, 5), (255, 0, 0, 255))
        result = apply_watermark(base, watermark, margin=10, tile=True, tile_rows=2, tile_cols=3)
        for point in [(22, 23), (49, 23), (75, 23), (22, 53), (49, 53), (75, 53)]:
            self.assertEqual(result.getpixel(point)[:3], (255, 0, 0))

    def test_image_watermark_opacity_multiplies_original_alpha(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "watermark.png"
            Image.new("RGBA", (8, 8), (10, 20, 30, 128)).save(path)
            layer = create_image_watermark_layer(path, opacity=128, scale_percent=50)
            self.assertEqual(layer.size, (4, 4))
            self.assertIn(layer.getpixel((0, 0))[3], (64, 65))

    def test_oversized_tile_margin_keeps_marks_on_canvas(self):
        base = Image.new("RGBA", (40, 30), "white")
        watermark = Image.new("RGBA", (4, 4), (255, 0, 0, 255))
        result = apply_watermark(base, watermark, margin=500, tile=True, tile_rows=2, tile_cols=2)
        visible_red = sum(
            1
            for pixel in result.get_flattened_data()
            if pixel[:3] == (255, 0, 0)
        )
        self.assertGreater(visible_red, 0)

    def test_process_image_preserves_alpha_capability(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "source.png"
            Image.new("RGBA", (120, 80), (255, 255, 255, 0)).save(path)
            result = process_image(
                path,
                {
                    "mode": "text",
                    "text": "测试",
                    "font_size": 20,
                    "opacity": 200,
                    "rainbow": True,
                    "position": "居中",
                },
            )
            self.assertEqual(result.mode, "RGBA")
            self.assertEqual(result.size, (120, 80))


if __name__ == "__main__":
    unittest.main()
