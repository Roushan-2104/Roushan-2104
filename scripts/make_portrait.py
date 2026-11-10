"""One-time: turn a photo into two ASCII portraits (light and dark cards).

Usage:
    python scripts/make_portrait.py <photo>

Writes data/portrait-light.txt (ink on paper: dark areas get dense characters)
and data/portrait-dark.txt (light ink on dark: bright areas get dense characters).
Needs Pillow:  pip install pillow

The outline below is traced by hand for the 400x400 cafe photo (beige T-shirt,
warm wooden background). The background is the same colour family as skin and
shirt, so a traced outline cuts it out more cleanly than colour rules.
A different photo needs a new outline and crop.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
COLS, ROWS = 96, 48           # character cells are about twice as tall as wide
RAMP = " .:-=+*#%@"           # light -> dense

# Outline of head, neck and shoulders, in photo pixels, clockwise from the left temple.
OUTLINE = [
    (146, 165), (144, 140), (152, 118), (170, 104), (195, 97), (220, 99), (240, 110),
    (251, 128), (253, 150), (250, 172), (248, 195), (243, 212), (236, 228), (240, 246),
    (262, 254), (290, 264), (318, 276), (338, 295), (352, 320), (364, 350), (372, 380),
    (378, 400), (95, 400), (97, 360), (100, 325), (105, 300), (115, 282), (135, 268),
    (158, 258), (176, 250), (178, 238), (168, 226), (160, 212), (152, 200), (148, 185),
]
CROP = (82, 96, 382, 396)     # square around the person, in photo pixels


def subject_mask(img: Image.Image) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon(OUTLINE, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(1.5))


def despeckle(lines, y):
    """Blank out lone characters with no neighbour within two cells."""
    row = list(lines[y])
    for x, ch in enumerate(row):
        if ch == " ":
            continue
        near = sum(
            1
            for yy in range(max(0, y - 2), min(len(lines), y + 3))
            for xx in range(max(0, x - 2), min(len(lines[yy]), x + 3))
            if (yy, xx) != (y, x) and lines[yy][xx] != " "
        )
        if near < 3:
            row[x] = " "
    return "".join(row)


def render(gray: Image.Image, mask: Image.Image, dense_is_dark: bool) -> str:
    g = gray.resize((COLS, ROWS), Image.LANCZOS)
    m = mask.resize((COLS, ROWS), Image.LANCZOS)
    # Stretch contrast using the person's pixels only, so the background can't flatten it.
    vals = sorted(g.getpixel((x, y)) for y in range(ROWS) for x in range(COLS) if m.getpixel((x, y)) >= 128)
    lo, hi = vals[len(vals) * 2 // 100], vals[len(vals) * 98 // 100]
    lines = []
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            if m.getpixel((x, y)) < 128:
                row.append(" ")
                continue
            v = min(1, max(0, (g.getpixel((x, y)) - lo) / max(1, hi - lo)))
            t = 1 - v if dense_is_dark else v
            # keep every subject cell visible, so the silhouette reads
            row.append(RAMP[max(1, min(len(RAMP) - 1, round(t * (len(RAMP) - 1))))])
        lines.append("".join(row))
    lines = [despeckle(lines, y).rstrip() for y in range(len(lines))]
    while lines and not lines[0].strip():
        lines.pop(0)
    return "\n".join(lines) + "\n"


def main(src: str) -> None:
    img = Image.open(src).convert("RGB")
    mask = subject_mask(img).crop(CROP)
    gray = ImageOps.grayscale(img.crop(CROP))
    out = ROOT / "data"
    out.mkdir(exist_ok=True)
    (out / "portrait-light.txt").write_text(render(gray, mask, True), encoding="utf-8")
    (out / "portrait-dark.txt").write_text(render(gray, mask, False), encoding="utf-8")
    print("wrote data/portrait-light.txt and data/portrait-dark.txt")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
