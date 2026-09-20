from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "black_metal_buddhist_prints"
CANVAS = (3600, 4800)
DPI = (300, 300)

REVISED = {
    "lotus_of_the_void": {
        "title": "Lotus of the Void",
        "svg": PKG / "02_two_ink_vector" / "lotus_of_the_void_two_ink.svg",
        "raster": PKG / "01_transparent_png" / "lotus_of_the_void_12x16_300dpi.png",
        "two_ink": PKG / "03_two_ink_png" / "lotus_of_the_void_two_ink_12x16_300dpi.png",
        "preview": PKG / "04_previews" / "lotus_of_the_void_PNG_preview_on_black.jpg",
        "two_preview": PKG / "04_previews" / "lotus_of_the_void_TWO_INK_preview_on_black.jpg",
        "reference": PKG / "05_original_mockups" / "lotus_of_the_void_REFERENCE_ONLY.jpg",
    },
    "dharma_of_decay": {
        "title": "Dharma of Decay",
        "svg": PKG / "02_two_ink_vector" / "dharma_of_decay_two_ink.svg",
        "raster": PKG / "01_transparent_png" / "dharma_of_decay_12x16_300dpi.png",
        "two_ink": PKG / "03_two_ink_png" / "dharma_of_decay_two_ink_12x16_300dpi.png",
        "preview": PKG / "04_previews" / "dharma_of_decay_PNG_preview_on_black.jpg",
        "two_preview": PKG / "04_previews" / "dharma_of_decay_TWO_INK_preview_on_black.jpg",
        "reference": PKG / "05_original_mockups" / "dharma_of_decay_REFERENCE_ONLY.jpg",
    },
}

SPEC = PKG / "PRINT_SPECIFICATIONS.json"
SUMS = PKG / "SHA256SUMS.txt"
COLLECTION = PKG / "04_previews" / "ALL_FOUR_artwork_preview.jpg"


def render_svg(path: Path) -> Image.Image:
    data = cairosvg.svg2png(
        bytestring=path.read_bytes(),
        output_width=CANVAS[0],
        output_height=CANVAS[1],
    )
    image = Image.open(BytesIO(data)).convert("RGBA")
    if image.size != CANVAS:
        raise RuntimeError(f"Unexpected render size for {path}: {image.size}")
    alpha = image.getchannel("A")
    lo, hi = alpha.getextrema()
    if lo != 0 or hi != 255:
        raise RuntimeError(f"Expected transparent and opaque pixels in {path}")
    return image


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        path,
        format="PNG",
        dpi=DPI,
        optimize=True,
        compress_level=9,
    )


def save_black_preview(image: Image.Image, path: Path, size: tuple[int, int]) -> None:
    fg = image.copy()
    fg.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 255))
    canvas.alpha_composite(
        fg,
        ((size[0] - fg.width) // 2, (size[1] - fg.height) // 2),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(
        path,
        "JPEG",
        quality=93,
        subsampling=0,
        optimize=True,
    )


def update_spec(rendered: dict[str, Image.Image]) -> None:
    spec = json.loads(SPEC.read_text())
    spec["prepared_date"] = "2026-09-19"
    spec["source_detail_warning"] = (
        "Lotus of the Void and Dharma of Decay were replaced September 19, 2026 "
        "with approved cross-free two-ink vector masters; their production rasters "
        "are deterministic SVG renders. Meditate on Death retains its existing "
        "raster/vector preparation. Longchenpa — Rest in Illusion is rendered from "
        "its approved two-ink SVG master."
    )

    by_slug = {item["slug"]: item for item in spec["designs"]}
    for slug, cfg in REVISED.items():
        image = rendered[slug]
        bbox = image.getchannel("A").getbbox()
        if bbox is None:
            raise RuntimeError(f"{slug} rendered fully transparent")
        x0, y0, x1, y1 = bbox
        width, height = x1 - x0, y1 - y0
        svg_text = cfg["svg"].read_text()
        bone_paths = svg_text.split('id="ink-bone"', 1)[1].split("</g>", 1)[0].count("<path")
        red_paths = svg_text.split('id="ink-red"', 1)[1].split("</g>", 1)[0].count("<path")

        item = by_slug[slug]
        item.update(
            {
                "source_master": str(cfg["svg"].relative_to(PKG)).replace("\\", "/"),
                "source_image_pixels": None,
                "extracted_artwork_pixels": None,
                "placed_artwork_pixels": [width, height],
                "placed_artwork_inches": [round(width / 300, 3), round(height / 300, 3)],
                "offset_inches": [round(x0 / 300, 3), round(y0 / 300, 3)],
                "effective_original_raster_ppi_at_placed_size": None,
                "raster_png": str(cfg["raster"].relative_to(PKG)).replace("\\", "/"),
                "two_ink_svg": str(cfg["svg"].relative_to(PKG)).replace("\\", "/"),
                "two_ink_png": str(cfg["two_ink"].relative_to(PKG)).replace("\\", "/"),
                "preview_png_on_black": str(cfg["preview"].relative_to(PKG)).replace("\\", "/"),
                "preview_two_ink_on_black": str(cfg["two_preview"].relative_to(PKG)).replace("\\", "/"),
                "reference_only": str(cfg["reference"].relative_to(PKG)).replace("\\", "/"),
                "vector_contour_count": {"bone": bone_paths, "red": red_paths},
                "cross_like_motifs_removed": True,
                "art_revision": "2026-09-19-cross-free",
                "status": (
                    "Approved cross-free two-ink production artwork. All active raster, "
                    "vector, preview, and reference formats supersede earlier revisions. "
                    "Physical sample approval is still required."
                ),
            }
        )

    SPEC.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")


def collection_preview() -> None:
    sources = [
        PKG / "04_previews" / "lotus_of_the_void_PNG_preview_on_black.jpg",
        PKG / "04_previews" / "dharma_of_decay_PNG_preview_on_black.jpg",
        PKG / "04_previews" / "meditate_on_death_PNG_preview_on_black.jpg",
        PKG / "04_previews" / "longchenpa_rest_in_illusion_PNG_preview_on_black.jpg",
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


def write_checksums() -> None:
    rows = []
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path == SUMS:
            continue
        rel = path.relative_to(PKG)
        if any(part.startswith(".") for part in rel.parts):
            continue
        rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel.as_posix()}")
    SUMS.write_text("\n".join(rows) + "\n")


def main() -> None:
    rendered: dict[str, Image.Image] = {}
    for slug, cfg in REVISED.items():
        image = render_svg(cfg["svg"])
        rendered[slug] = image

        # For these two revised designs, 01 and 03 intentionally carry the same
        # approved two-ink production artwork. This guarantees every printable
        # format uses the cross-free revision.
        save_png(image, cfg["raster"])
        save_png(image, cfg["two_ink"])
        save_black_preview(image, cfg["preview"], (900, 1200))
        save_black_preview(image, cfg["two_preview"], (900, 1200))
        save_black_preview(image, cfg["reference"], (1122, 1402))

    collection_preview()
    update_spec(rendered)
    write_checksums()

    for slug, image in rendered.items():
        print(slug, image.getchannel("A").getbbox())


if __name__ == "__main__":
    main()
