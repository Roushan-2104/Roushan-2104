"""One-time: subset the variable fonts to small WOFF files for embedding in SVGs.

Usage:
    python scripts/make_fonts.py <SpaceGrotesk[wght].ttf> <JetBrainsMono[wght].ttf>

Both fonts come from github.com/google/fonts (SIL Open Font License, see fonts/).
Needs fontTools:  pip install fonttools
"""
import sys
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fonts"

# Printable ASCII plus the few extra marks the cards use.
CODEPOINTS = list(range(0x20, 0x7F)) + [0xA0, 0xB7, 0x2013, 0x2014, 0x2019, 0x2192, 0x2197]

TARGETS = [
    # (source index, weight, output name)
    (0, 700, "grotesk-700.woff"),
    (0, 400, "grotesk-400.woff"),
    (1, 500, "mono-500.woff"),
]


def build(src: str, weight: int, name: str) -> None:
    font = TTFont(src)
    family = font["name"].getDebugName(1)
    if font["OS/2"].fsSelection & 1:
        raise SystemExit(f"{src} is an italic file ({family}); use the upright one")
    font = instantiateVariableFont(font, {"wght": weight})
    opts = Options()
    opts.flavor = "woff"
    opts.layout_features = ["kern", "liga", "calt"]
    opts.name_IDs = []
    opts.notdef_outline = True
    opts.hinting = False
    sub = Subsetter(opts)
    sub.populate(unicodes=CODEPOINTS)
    sub.subset(font)
    OUT.mkdir(exist_ok=True)
    font.flavor = "woff"
    font.save(OUT / name)
    missing = [hex(c) for c in CODEPOINTS if c not in font.getBestCmap()]
    print(f"{name}: {family} {weight}, {(OUT / name).stat().st_size / 1024:.1f} KB"
          + (f", missing {missing}" if missing else ""))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    for idx, weight, name in TARGETS:
        build(sys.argv[1 + idx], weight, name)
