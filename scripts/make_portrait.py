"""One-time: turn a photo into two ASCII portraits (light and dark cards).

Usage:
    python scripts/make_portrait.py <photo>

Writes data/portrait-light.txt (ink on paper: dark areas get dense characters)
and data/portrait-dark.txt (light ink on dark: bright areas get dense characters).
Needs Pillow:  pip install pillow

The cut-out settings below are tuned for the 400x400 lakeside photo (orange
T-shirt, sky, green hills and water behind). A different photo needs new values.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
COLS, ROWS = 96, 48           # character cells are about twice as tall as wide
RAMP = " .:-=+*#%@"           # light -> dense

HEAD = (150, 116, 246, 240)   # ellipse around head and hair, in photo pixels
HORIZON = 205                 # sky above this line, hills and water below
CROP = (45, 110, 335, 400)    # square around the person, in photo pixels


def subject_mask(img: Image.Image) -> Image.Image:
    """Keep the person: warm skin and shirt colours below the horizon, plus the
    head ellipse minus sky and green hills."""
    h, s, v = (band.load() for band in img.convert("HSV").split())
    head = Image.new("L", img.size, 0)
    ImageDraw.Draw(head).ellipse(HEAD, fill=255)
    hd = head.load()
    mask = Image.new("L", img.size, 0)
    px = mask.load()
    for y in range(img.height):
        for x in range(img.width):
            hh, ss, vv = h[x, y], s[x, y], v[x, y]
            green = 60 <= hh <= 140 and ss > 40
            if hd[x, y]:
                sky = y < HORIZON and vv > 140 and ss < 90
                keep = not green and not sky
            else:
                warm = (hh <= 32 or hh >= 225) and ss >= 70 and vv >= 15
                dark = vv < 30 and not 60 <= hh <= 140
                keep = y >= HORIZON and (warm or dark)
            if keep:
                px[x, y] = 255
    # Drop specks, then close small holes.
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    return mask.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))


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
