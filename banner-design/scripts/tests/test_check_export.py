import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
from check_export import inspect_png, check_export, SIGNATURE


def chunk(kind, data=b""):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def png(width=2, height=3, color=6, include_idat=True):
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color, 0, 0, 0))
    channels = 4 if color == 6 else 3
    pixels = (b"\x00" + b"\x80" * width * channels) * height
    return SIGNATURE + ihdr + (chunk(b"IDAT", zlib.compress(pixels)) if include_idat else b"") + chunk(b"IEND")


class ExportChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="codex-banner-test-")
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / "banner.png"
        self.file.write_bytes(png())

    def test_valid_export_is_read_only_and_reports_physical_pixels(self):
        before = self.file.read_bytes()
        result = check_export(self.file, 2, 3)
        self.assertTrue(result["ok"])
        self.assertTrue(result["alpha_capable"])
        self.assertFalse(result["pixels_decoded"])
        self.assertEqual(before, self.file.read_bytes())

    def test_rgb_without_alpha_is_reported(self):
        self.file.write_bytes(png(color=2))
        self.assertFalse(inspect_png(self.file)["alpha_capable"])

    def test_dimension_mismatch_fails(self):
        result = check_export(self.file, 3, 2)
        self.assertFalse(result["ok"])
        self.assertIn("Dimensions", result["errors"][0])

    def test_byte_limit_and_boundary(self):
        size = self.file.stat().st_size
        self.assertTrue(check_export(self.file, 2, 3, size)["ok"])
        self.assertFalse(check_export(self.file, 2, 3, size - 1)["ok"])

    def test_extension_does_not_hide_non_png(self):
        self.file.write_bytes(b"not png")
        with self.assertRaisesRegex(ValueError, "Expected a PNG"):
            inspect_png(self.file)

    def test_crc_corruption_fails(self):
        data = bytearray(self.file.read_bytes())
        data[25] ^= 1
        self.file.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "CRC"):
            inspect_png(self.file)

    def test_truncated_export_fails(self):
        self.file.write_bytes(self.file.read_bytes()[:-2])
        with self.assertRaises(ValueError):
            inspect_png(self.file)

    def test_missing_pixel_block_fails(self):
        self.file.write_bytes(png(include_idat=False))
        with self.assertRaisesRegex(ValueError, "missing IDAT"):
            inspect_png(self.file)

    def test_trailing_data_fails(self):
        self.file.write_bytes(png() + b"extra")
        with self.assertRaisesRegex(ValueError, "after IEND"):
            inspect_png(self.file)

    def test_zero_dimensions_fail(self):
        self.file.write_bytes(png(width=0))
        with self.assertRaisesRegex(ValueError, "dimensions"):
            inspect_png(self.file)

    def test_indexed_image_requires_palette(self):
        self.file.write_bytes(png(color=3))
        with self.assertRaisesRegex(ValueError, "missing palette"):
            inspect_png(self.file)

    def test_cli_json_success_failure_and_invalid_argument(self):
        command = [sys.executable, "-B", str(SCRIPTS / "check_export.py"), str(self.file), "--width", "2", "--height", "3", "--json"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])
        command[command.index("--width") + 1] = "4"
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["ok"])
        command[command.index("--width") + 1] = "0"
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
