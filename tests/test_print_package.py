from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "black_metal_buddhist_prints"

RASTER = PKG / "01_transparent_png" / "longchenpa_rest_in_illusion_12x16_300dpi.png"
SVG = PKG / "02_two_ink_vector" / "longchenpa_rest_in_illusion_two_ink.svg"
TWO_INK = PKG / "03_two_ink_png" / "longchenpa_rest_in_illusion_two_ink_12x16_300dpi.png"
PNG_PREVIEW = PKG / "04_previews" / "longchenpa_rest_in_illusion_PNG_preview_on_black.jpg"
TWO_PREVIEW = PKG / "04_previews" / "longchenpa_rest_in_illusion_TWO_INK_preview_on_black.jpg"
COLLECTION = PKG / "04_previews" / "ALL_FOUR_artwork_preview.jpg"
REFERENCE = PKG / "05_original_mockups" / "longchenpa_rest_in_illusion_REFERENCE_ONLY.jpg"
SPEC = PKG / "PRINT_SPECIFICATIONS.json"
SUMS = PKG / "SHA256SUMS.txt"


def png_metadata(path: Path) -> tuple[int, int, int, tuple[int, int] | None]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"

    width, height = struct.unpack(">II", data[16:24])
    color_type = data[25]

    offset = 8
    dpi = None
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        chunk = data[offset + 8:offset + 8 + length]
        if chunk_type == b"pHYs" and len(chunk) == 9 and chunk[8] == 1:
            x_ppm, y_ppm = struct.unpack(">II", chunk[:8])
            dpi = (round(x_ppm * 0.0254), round(y_ppm * 0.0254))
        offset += 12 + length
        if chunk_type == b"IEND":
            break

    return width, height, color_type, dpi


def checksum_map() -> dict[str, str]:
    values = {}
    for line in SUMS.read_text().splitlines():
        if not line.strip():
            continue
        digest, relative = line.split("  ", 1)
        values[relative] = digest
    return values


def test_longchenpa_production_package_is_complete():
    required = [
        RASTER,
        SVG,
        TWO_INK,
        PNG_PREVIEW,
        TWO_PREVIEW,
        COLLECTION,
        REFERENCE,
        SPEC,
        SUMS,
    ]
    for path in required:
        assert path.is_file(), path
        assert path.stat().st_size > 0, path

    assert not (PKG / "04_previews" / "ALL_THREE_artwork_preview.jpg").exists()


def test_longchenpa_rasters_are_transparent_12x16_300dpi():
    for path in (RASTER, TWO_INK):
        width, height, color_type, dpi = png_metadata(path)
        assert (width, height) == (3600, 4800)
        assert color_type in {4, 6}, "Production PNG must carry an alpha channel"
        assert dpi == (300, 300)

    # Longchenpa's 01 and 03 files intentionally represent the same approved
    # two-ink production artwork.
    assert hashlib.sha256(RASTER.read_bytes()).digest() == hashlib.sha256(TWO_INK.read_bytes()).digest()


def test_longchenpa_svg_is_the_two_ink_master():
    text = SVG.read_text()
    assert 'viewBox="0 0 3600 4800"' in text
    assert "#E9E1D5" in text
    assert "#971F1F" in text
    assert 'id="ink-bone"' in text
    assert 'id="ink-red"' in text
    assert "<image" not in text.lower(), "SVG must not embed a raster image"


def test_longchenpa_print_spec_points_to_every_required_asset():
    spec = json.loads(SPEC.read_text())
    assert spec["canvas_pixels"] == [3600, 4800]
    assert spec["canvas_inches"] == [12, 16]
    assert spec["nominal_export_ppi"] == 300

    design = next(
        item for item in spec["designs"]
        if item["slug"] == "longchenpa_rest_in_illusion"
    )
    assert design["series"] == "Lineage Series"
    assert design["source_master"] == "02_two_ink_vector/longchenpa_rest_in_illusion_two_ink.svg"
    assert design["raster_png"] == "01_transparent_png/longchenpa_rest_in_illusion_12x16_300dpi.png"
    assert design["two_ink_png"] == "03_two_ink_png/longchenpa_rest_in_illusion_two_ink_12x16_300dpi.png"
    assert design["preview_png_on_black"] == "04_previews/longchenpa_rest_in_illusion_PNG_preview_on_black.jpg"
    assert design["preview_two_ink_on_black"] == "04_previews/longchenpa_rest_in_illusion_TWO_INK_preview_on_black.jpg"
    assert design["reference_only"] == "05_original_mockups/longchenpa_rest_in_illusion_REFERENCE_ONLY.jpg"
    assert design["placed_artwork_pixels"][0] > 3000
    assert design["placed_artwork_pixels"][1] > 4400


def test_longchenpa_package_checksums_match_actual_files():
    checksums = checksum_map()
    required_relatives = [
        "01_transparent_png/longchenpa_rest_in_illusion_12x16_300dpi.png",
        "02_two_ink_vector/longchenpa_rest_in_illusion_two_ink.svg",
        "03_two_ink_png/longchenpa_rest_in_illusion_two_ink_12x16_300dpi.png",
        "04_previews/longchenpa_rest_in_illusion_PNG_preview_on_black.jpg",
        "04_previews/longchenpa_rest_in_illusion_TWO_INK_preview_on_black.jpg",
        "04_previews/ALL_FOUR_artwork_preview.jpg",
        "05_original_mockups/longchenpa_rest_in_illusion_REFERENCE_ONLY.jpg",
        "MESSAGE_TO_PRINTER.txt",
        "PRINT_SPECIFICATIONS.json",
        "START_HERE_FOR_PRINTER.txt",
    ]

    for relative in required_relatives:
        path = PKG / relative
        assert relative in checksums
        assert hashlib.sha256(path.read_bytes()).hexdigest() == checksums[relative]
