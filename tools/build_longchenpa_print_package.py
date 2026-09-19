from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "black_metal_buddhist_prints"
SVG = PKG / "02_two_ink_vector" / "longchenpa_rest_in_illusion_two_ink.svg"

RASTER = PKG / "01_transparent_png" / "longchenpa_rest_in_illusion_12x16_300dpi.png"
TWO_INK = PKG / "03_two_ink_png" / "longchenpa_rest_in_illusion_two_ink_12x16_300dpi.png"
PREVIEW = PKG / "04_previews" / "longchenpa_rest_in_illusion_PNG_preview_on_black.jpg"
TWO_PREVIEW = PKG / "04_previews" / "longchenpa_rest_in_illusion_TWO_INK_preview_on_black.jpg"
COLLECTION = PKG / "04_previews" / "ALL_FOUR_artwork_preview.jpg"
REFERENCE = PKG / "05_original_mockups" / "longchenpa_rest_in_illusion_REFERENCE_ONLY.jpg"
OLD_COLLECTION = PKG / "04_previews" / "ALL_THREE_artwork_preview.jpg"
SPEC = PKG / "PRINT_SPECIFICATIONS.json"
SUMS = PKG / "SHA256SUMS.txt"

CANVAS = (3600, 4800)
DPI = (300, 300)


def render_svg() -> Image.Image:
    png = cairosvg.svg2png(
        bytestring=SVG.read_bytes(),
        output_width=CANVAS[0],
        output_height=CANVAS[1],
    )
    image = Image.open(BytesIO(png)).convert("RGBA")
    if image.size != CANVAS:
        raise RuntimeError(f"Unexpected render size: {image.size}")
    return image


def save_rgba(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", dpi=DPI, optimize=True, compress_level=9)


def flatten_preview(image: Image.Image, size: tuple[int, int], path: Path) -> None:
    foreground = image.copy()
    foreground.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (0, 0, 0))
    x = (size[0] - foreground.width) // 2
    y = (size[1] - foreground.height) // 2
    rgba = Image.new("RGBA", size, (0, 0, 0, 255))
    rgba.alpha_composite(foreground, (x, y))
    canvas = rgba.convert("RGB")
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, "JPEG", quality=93, subsampling=0, optimize=True)


def collection_preview() -> None:
    sources = [
        PKG / "04_previews" / "lotus_of_the_void_PNG_preview_on_black.jpg",
        PKG / "04_previews" / "dharma_of_decay_PNG_preview_on_black.jpg",
        PKG / "04_previews" / "meditate_on_death_PNG_preview_on_black.jpg",
        PREVIEW,
    ]
    cell = (900, 1200)
    canvas = Image.new("RGB", (1800, 2400), (0, 0, 0))
    for index, path in enumerate(sources):
        image = Image.open(path).convert("RGB")
        image.thumbnail(cell, Image.Resampling.LANCZOS)
        x0 = (index % 2) * cell[0] + (cell[0] - image.width) // 2
        y0 = (index // 2) * cell[1] + (cell[1] - image.height) // 2
        canvas.paste(image, (x0, y0))
    canvas.save(COLLECTION, "JPEG", quality=92, subsampling=0, optimize=True)
    if OLD_COLLECTION.exists():
        OLD_COLLECTION.unlink()


def update_spec(image: Image.Image) -> None:
    spec = json.loads(SPEC.read_text())
    spec["prepared_date"] = "2026-09-19"
    spec["source_detail_warning"] = (
        "The first three raster designs were enlarged from generated mockup extractions. "
        "Longchenpa — Rest in Illusion is an exception: its transparent 300-DPI raster is "
        "rendered deterministically from the approved two-ink SVG master."
    )

    alpha_bbox = image.getchannel("A").getbbox()
    if alpha_bbox is None:
        raise RuntimeError("Longchenpa artwork rendered fully transparent")
    x0, y0, x1, y1 = alpha_bbox
    width = x1 - x0
    height = y1 - y0

    for design in spec["designs"]:
        if design.get("slug") == "longchenpa_rest_in_illusion":
            design.update(
                {
                    "source_master": "02_two_ink_vector/longchenpa_rest_in_illusion_two_ink.svg",
                    "source_image_pixels": None,
                    "extracted_artwork_pixels": None,
                    "placed_artwork_pixels": [width, height],
                    "placed_artwork_inches": [round(width / 300, 3), round(height / 300, 3)],
                    "offset_inches": [round(x0 / 300, 3), round(y0 / 300, 3)],
                    "effective_original_raster_ppi_at_placed_size": None,
                    "raster_png": "01_transparent_png/longchenpa_rest_in_illusion_12x16_300dpi.png",
                    "two_ink_svg": "02_two_ink_vector/longchenpa_rest_in_illusion_two_ink.svg",
                    "two_ink_png": "03_two_ink_png/longchenpa_rest_in_illusion_two_ink_12x16_300dpi.png",
                    "preview_png_on_black": "04_previews/longchenpa_rest_in_illusion_PNG_preview_on_black.jpg",
                    "preview_two_ink_on_black": "04_previews/longchenpa_rest_in_illusion_TWO_INK_preview_on_black.jpg",
                    "reference_only": "05_original_mockups/longchenpa_rest_in_illusion_REFERENCE_ONLY.jpg",
                    "status": (
                        "Approved two-ink production artwork. Transparent 3600 x 4800 PNG "
                        "rendered from the SVG at nominal 300 ppi; physical sample approval "
                        "and final Printful variant mapping still required."
                    ),
                }
            )
            break
    else:
        raise RuntimeError("Longchenpa design missing from PRINT_SPECIFICATIONS.json")

    SPEC.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")


def write_checksums() -> None:
    rows: list[str] = []
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path == SUMS:
            continue
        rel = path.relative_to(PKG)
        if any(part.startswith(".") for part in rel.parts):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{digest}  {rel.as_posix()}")
    SUMS.write_text("\n".join(rows) + "\n")


def main() -> None:
    image = render_svg()
    save_rgba(image, RASTER)
    save_rgba(image, TWO_INK)
    flatten_preview(image, (900, 1200), PREVIEW)
    flatten_preview(image, (900, 1200), TWO_PREVIEW)
    flatten_preview(image, (1122, 1402), REFERENCE)
    collection_preview()
    update_spec(image)
    write_checksums()

    bbox = image.getchannel("A").getbbox()
    print(f"Generated Longchenpa print package: {CANVAS[0]}x{CANVAS[1]} px @ 300 dpi")
    print(f"Artwork alpha bounds: {bbox}")


if __name__ == "__main__":
    main()
