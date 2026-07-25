import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app import WatermarkApp


class OutputTests(unittest.TestCase):
    def test_jpeg_output_converts_transparency_to_rgb(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "result.jpg"
            source = Image.new("RGBA", (24, 18), (200, 30, 50, 120))
            WatermarkApp._save_result(source, target, "JPEG", 91)
            with Image.open(target) as saved:
                self.assertEqual(saved.format, "JPEG")
                self.assertEqual(saved.mode, "RGB")
                self.assertEqual(saved.size, (24, 18))

    def test_png_output_keeps_alpha(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "result.png"
            source = Image.new("RGBA", (12, 10), (10, 20, 30, 40))
            WatermarkApp._save_result(source, target, "PNG", 95)
            with Image.open(target) as saved:
                self.assertEqual(saved.mode, "RGBA")
                self.assertEqual(saved.getpixel((0, 0))[3], 40)


if __name__ == "__main__":
    unittest.main()
