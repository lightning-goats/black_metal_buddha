from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "black_metal_buddhist_prints"
SPEC = PKG / "PRINT_SPECIFICATIONS.json"
SUMS = PKG / "SHA256SUMS.txt"

REVISED = {
    "lotus_of_the_void": {
        "raster": "01_transparent_png/lotus_of_the_void_12x16_300dpi.png",
        "svg": "02_two_ink_vector/lotus_of_the_void_two_ink.svg",
        "two": "03_two_ink_png/lotus_of_the_void_two_ink_12x16_300dpi.png",
        "preview": "04_previews/lotus_of_the_void_PNG_preview_on_black.jpg",
        "two_preview": "04_previews/lotus_of_the_void_TWO_INK_preview_on_black.jpg",
        "reference": "05_original_mockups/lotus_of_the_void_REFERENCE_ONLY.jpg",
    },
    "dharma_of_decay": {
        "raster": "01_transparent_png/dharma_of_decay_12x16_300dpi.png",
        "svg": "02_two_ink_vector/dharma_of_decay_two_ink.svg",
        "two": "03_two_ink_png/dharma_of_decay_two_ink_12x16_300dpi.png",
        "preview": "04_previews/dharma_of_decay_PNG_preview_on_black.jpg",
        "two_preview": "04_previews/dharma_of_decay_TWO_INK_preview_on_black.jpg",
        "reference": "05_original_mockups/dharma_of_decay_REFERENCE_ONLY.jpg",
    },
}


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


def test_revised_lotus_and_dharma_are_complete_in_every_active_format():
    for files in REVISED.values():
        for relative in files.values():
            path = PKG / relative
            assert path.is_file(), path
            assert path.stat().st_size > 0, path


def test_revised_lotus_and_dharma_rasters_are_transparent_12x16_300dpi():
    for files in REVISED.values():
        for key in ("raster", "two"):
            path = PKG / files[key]
            width, height, color_type, dpi = png_metadata(path)
            assert (width, height) == (3600, 4800)
            assert color_type in {4, 6}
            assert dpi == (300, 300)

        # The revised 01 and 03 files intentionally represent the same approved
        # two-ink artwork so an obsolete cross-containing raster cannot survive.
        raster = (PKG / files["raster"]).read_bytes()
        two = (PKG / files["two"]).read_bytes()
        assert hashlib.sha256(raster).digest() == hashlib.sha256(two).digest()


def test_revised_vector_masters_use_only_brand_inks_and_no_embedded_raster():
    for files in REVISED.values():
        text = (PKG / files["svg"]).read_text()
        assert 'viewBox="0 0 3600 4800"' in text
        assert 'id="ink-bone"' in text
        assert 'id="ink-red"' in text
        assert "#E9E1D5" in text
        assert "#971F1F" in text
        assert "<image" not in text.lower()


def test_print_spec_marks_both_revisions_as_cross_free_and_superseding():
    spec = json.loads(SPEC.read_text())
    by_slug = {item["slug"]: item for item in spec["designs"]}

    for slug, files in REVISED.items():
        item = by_slug[slug]
        assert item["cross_like_motifs_removed"] is True
        assert item["art_revision"] == "2026-09-19-cross-free"
        assert item["source_master"] == files["svg"]
        assert item["raster_png"] == files["raster"]
        assert item["two_ink_png"] == files["two"]
        assert item["preview_png_on_black"] == files["preview"]
        assert item["preview_two_ink_on_black"] == files["two_preview"]
        assert item["reference_only"] == files["reference"]
        assert "supersede" in item["status"].lower()


def test_revised_package_checksums_match_every_replaced_asset():
    checksums = checksum_map()
    for files in REVISED.values():
        for relative in files.values():
            path = PKG / relative
            assert relative in checksums
            assert hashlib.sha256(path.read_bytes()).hexdigest() == checksums[relative]


def test_printer_handoff_explicitly_rejects_old_cross_containing_revisions():
    start = (PKG / "START_HERE_FOR_PRINTER.txt").read_text().lower()
    message = (PKG / "MESSAGE_TO_PRINTER.txt").read_text().lower()
    for text in (start, message):
        assert "cross-like" in text
        assert "christian" in text
        assert "do not use" in text
