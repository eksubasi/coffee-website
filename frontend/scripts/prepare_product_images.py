"""Prepare product images for the storefront (KAN-31).

Takes the raw images you generated (PNG/JPG/WebP/AVIF, any size), and writes them as
800x800 WebP files to frontend/public/products/, named exactly as in the
"Image File" column of the catalog sheet. Then reports which products still
have no image and checks that all images together stay under 5 MB.

Name each raw file after the product's image file or its model code, e.g.
    db-eth-250.png   or   DB-ETH-250.jpg   (case does not matter)

Usage (from the repo root, with the backend virtualenv active):
    pip install -U pillow         # once; Pillow 11.3+ reads AVIF. openpyxl is in backend/requirements.txt
    python frontend/scripts/prepare_product_images.py path/to/raw-images

Options:
    --sheet PATH     catalog spreadsheet (default: backend/catalog/data/Brewnook_Product_List.xlsx)
    --out PATH       output folder (default: frontend/public/products)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import openpyxl
    from PIL import Image, ImageOps
except ImportError as exc:  # pragma: no cover - friendly message instead of a traceback
    sys.exit(f"Missing package: {exc.name}. Run: pip install pillow openpyxl")

REPO = Path(__file__).resolve().parents[2]
DEFAULT_SHEET = REPO / "backend" / "catalog" / "data" / "Brewnook_Product_List.xlsx"
DEFAULT_OUT = REPO / "frontend" / "public" / "products"

SIZE = 800  # px, square
TOTAL_BUDGET = 5 * 1024 * 1024  # KAN-31 acceptance: all images < 5 MB
PER_IMAGE_TARGET = 140 * 1024  # 32 x 140 KB ~ 4.4 MB, leaves headroom
QUALITIES = (82, 76, 70, 64, 58)  # tried in order until the image fits PER_IMAGE_TARGET
RAW_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".avif"}


def read_catalog(sheet: Path) -> list[tuple[str, str, str]]:
    """Returns (model, name, image file path like 'products/db-eth-250.webp') for every product."""
    ws = openpyxl.load_workbook(sheet, read_only=True)["Products"]
    rows = ws.iter_rows(values_only=True)
    header = list(next(rows))
    try:
        i_model, i_name, i_image = header.index("Model"), header.index("Name"), header.index("Image File")
    except ValueError as exc:
        sys.exit(f"Sheet is missing a column: {exc}")
    return [
        (str(r[i_model]).strip(), str(r[i_name]).strip(), str(r[i_image]).strip())
        for r in rows
        if r[i_model] and r[i_image]
    ]


def find_raw(raw_dir: Path, model: str, stem: str) -> Path | None:
    wanted = {model.lower(), stem.lower()}
    for path in sorted(raw_dir.iterdir()):
        if path.suffix.lower() in RAW_EXTENSIONS and path.stem.lower() in wanted:
            return path
    return None


def convert(src: Path, dest: Path) -> int:
    """Center-crops to a square, resizes to SIZE x SIZE, saves as WebP. Returns the file size."""
    try:
        img_file = Image.open(src)
    except Exception as exc:  # e.g. AVIF with an old Pillow
        hint = " (AVIF needs Pillow 11.3+: pip install -U pillow)" if src.suffix.lower() == ".avif" else ""
        sys.exit(f"Could not open {src.name}: {exc}{hint}")
    with img_file as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img = ImageOps.fit(img, (SIZE, SIZE), method=Image.Resampling.LANCZOS)
        for quality in QUALITIES:
            img.save(dest, "WEBP", quality=quality, method=6)
            if dest.stat().st_size <= PER_IMAGE_TARGET:
                break
    return dest.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("raw_dir", type=Path, help="folder with the generated images")
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if not args.raw_dir.is_dir():
        sys.exit(f"Not a folder: {args.raw_dir}")
    args.out.mkdir(parents=True, exist_ok=True)

    products = read_catalog(args.sheet)
    missing: list[str] = []
    converted = 0

    for model, name, image_file in products:
        dest = args.out / Path(image_file).name
        raw = find_raw(args.raw_dir, model, dest.stem)
        if raw:
            size = convert(raw, dest)
            converted += 1
            print(f"  ok   {dest.name:<22} {size / 1024:6.0f} KB   <- {raw.name}")
        elif dest.exists():
            print(f"  kept {dest.name:<22} {dest.stat().st_size / 1024:6.0f} KB   (no new raw image)")
        else:
            missing.append(f"{model:<12} {dest.name:<22} {name}")

    expected = {Path(f).name for _, _, f in products}
    total = sum(p.stat().st_size for p in args.out.glob("*.webp") if p.name in expected)

    print(f"\nConverted {converted} image(s) into {args.out}")
    print(f"Total size: {total / 1024 / 1024:.2f} MB (limit 5 MB)")
    ok = True
    if missing:
        ok = False
        print(f"\nStill missing {len(missing)} of {len(products)} products:")
        print("\n".join(f"  {m}" for m in missing))
    if total > TOTAL_BUDGET:
        ok = False
        print("\nOver the 5 MB budget: lower QUALITIES or PER_IMAGE_TARGET at the top of this script.")
    if ok:
        print("\nAll products have an image and the total is under 5 MB.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
