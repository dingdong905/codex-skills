#!/usr/bin/env python3
"""Read-only PNG container, raster dimension and byte-size checks. No pixel decoding."""
import argparse
import json
import struct
import sys
import zlib
from pathlib import Path

SIGNATURE = b"\x89PNG\r\n\x1a\n"
BIT_DEPTHS = {0: {1, 2, 4, 8, 16}, 2: {8, 16}, 3: {1, 2, 4, 8}, 4: {8, 16}, 6: {8, 16}}


def inspect_png(file):
    file = Path(file)
    size = file.stat().st_size
    with file.open("rb") as handle:
        if handle.read(8) != SIGNATURE:
            raise ValueError("Expected a PNG file; extension alone does not establish format")
        info, seen_idat, ended_idat, palette, transparency = None, False, False, False, False
        while True:
            header = handle.read(8)
            if len(header) != 8:
                raise ValueError("Truncated PNG or missing IEND")
            length, kind = struct.unpack(">I4s", header)
            if any(not (65 <= c <= 90 or 97 <= c <= 122) for c in kind):
                raise ValueError("Invalid PNG chunk type")
            if length > size - handle.tell() - 4:
                raise ValueError("PNG chunk exceeds file boundary")
            if info is None and (kind != b"IHDR" or length != 13):
                raise ValueError("PNG must start with a 13-byte IHDR")
            if info is not None and kind == b"IHDR":
                raise ValueError("Duplicate IHDR")
            crc, remaining, small_data = zlib.crc32(kind), length, b""
            while remaining:
                block = handle.read(min(remaining, 65536))
                if not block:
                    raise ValueError("Truncated PNG chunk")
                crc = zlib.crc32(block, crc)
                if kind == b"IHDR":
                    small_data += block
                remaining -= len(block)
            stored_crc = handle.read(4)
            if len(stored_crc) != 4 or (crc & 0xFFFFFFFF) != struct.unpack(">I", stored_crc)[0]:
                raise ValueError("PNG chunk CRC mismatch")
            if kind == b"IHDR":
                width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", small_data)
                if width < 1 or height < 1 or width > 2**31 - 1 or height > 2**31 - 1:
                    raise ValueError("Invalid PNG dimensions")
                if color not in BIT_DEPTHS or depth not in BIT_DEPTHS[color] or compression != 0 or filtering != 0 or interlace not in (0, 1):
                    raise ValueError("Unsupported or invalid PNG IHDR fields")
                info = {"width": width, "height": height, "bit_depth": depth, "color_type": color}
            elif kind == b"PLTE":
                if seen_idat or palette or length < 3 or length > 768 or length % 3 or info["color_type"] in (0, 4):
                    raise ValueError("Invalid PNG palette")
                palette = True
            elif kind == b"tRNS":
                transparency = True
            elif kind == b"IDAT":
                if ended_idat or (info["color_type"] == 3 and not palette):
                    raise ValueError("Non-contiguous IDAT or indexed PNG missing palette")
                seen_idat = True
            elif kind == b"IEND":
                if length or not seen_idat:
                    raise ValueError("Invalid IEND or PNG missing IDAT")
                if handle.read(1):
                    raise ValueError("Unexpected data after IEND")
                info.update({"bytes": size, "alpha_capable": info["color_type"] in (4, 6) or transparency,
                             "container_checks_passed": True, "pixels_decoded": False})
                return info
            if seen_idat and kind != b"IDAT":
                ended_idat = True


def check_export(file, width, height, max_bytes=None):
    info = inspect_png(file)
    errors = []
    if (info["width"], info["height"]) != (width, height):
        errors.append(f"Dimensions {info['width']}x{info['height']} differ from required {width}x{height}")
    if max_bytes is not None and info["bytes"] > max_bytes:
        errors.append(f"File size {info['bytes']} exceeds {max_bytes} bytes")
    return {"file": str(Path(file).resolve()), **info, "required_width": width, "required_height": height,
            "ok": not errors, "errors": errors,
            "scope": "PNG container/dimensions/bytes only; open final image to verify decoding, text, crop and visual quality"}


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--width", required=True, type=positive, help="Required physical raster width in pixels")
    parser.add_argument("--height", required=True, type=positive, help="Required physical raster height in pixels")
    parser.add_argument("--max-bytes", type=positive, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = check_export(args.file, args.width, args.height, args.max_bytes)
    except (OSError, ValueError, struct.error) as exc:
        result = {"file": str(args.file), "ok": False, "errors": [str(exc)]}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(("PASS" if result["ok"] else "FAIL") + ": " + result["file"])
        if "width" in result:
            print(f"{result['width']}x{result['height']} physical px, {result['bytes']} bytes; pixels not decoded")
        for error in result["errors"]:
            print(error)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
