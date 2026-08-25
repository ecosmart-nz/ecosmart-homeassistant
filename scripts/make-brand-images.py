#!/usr/bin/env python3
"""Build the brand/ PNGs for the home-assistant/brands pull request.

Sources are the ecosmart website's brand masters plus the vector mark. Nothing
here upscales: every output is either a master copied verbatim, or a fresh
render of the vector at the size required.

    icon.png     256x256  mark-256.png, byte-for-byte
    icon@2x.png  512x512  favicon.svg rendered at 512, laid out exactly as
                          mark-256.png lays the mark out (17/256 padding)
    logo.png     640x128  lockup-640.png, byte-for-byte

There is no logo@2x.png: the widest wordmark master is 640px, and doubling it
would mean inventing detail. See brand/README.md.

Needs cairosvg, which needs libcairo -- present on Linux/WSL, not on Windows:

    wsl -d Ubuntu-24.04 -u root --cd /root -- \
        /root/.venvs/svgrender/bin/python \
        /mnt/c/synergy/homeassistant/ecosmart-ha/scripts/make-brand-images.py
"""

from __future__ import annotations

import io
import shutil
import sys
from pathlib import Path

import cairosvg
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "brand"

# The website repo is read-only from here; adjust if it is not mounted at /mnt/c.
WEBSITE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/mnt/c/synergy/ecosmart_website")
BRAND = WEBSITE / "public" / "images" / "brand"
MARK_256 = BRAND / "mark-256.png"
LOCKUP_640 = BRAND / "lockup-640.png"
FAVICON_SVG = WEBSITE / "public" / "favicon.svg"


def render_icon_2x() -> Image.Image:
    """Render the vector mark at 512, positioned as the 256 master positions it."""
    master = Image.open(MARK_256).convert("RGBA")
    box = master.getbbox()
    assert master.size == (256, 256), f"mark-256 is {master.size}"
    assert box is not None
    offset = (box[0], box[1])
    content = (box[2] - box[0], box[3] - box[1])

    # Render far larger than needed, then crop to the ink and scale down once.
    big = Image.open(
        io.BytesIO(cairosvg.svg2png(url=str(FAVICON_SVG), output_width=4096, output_height=4096))
    ).convert("RGBA")
    ink_box = big.getbbox()
    assert ink_box is not None
    ink = big.crop(ink_box)

    ink_aspect = (ink_box[2] - ink_box[0]) / (ink_box[3] - ink_box[1])
    master_aspect = content[0] / content[1]
    drift = abs(ink_aspect - master_aspect) / master_aspect
    assert drift < 0.01, f"vector and raster mark disagree on shape by {drift:.2%}"
    print(f"vector/raster aspect agreement: {drift:.3%}")

    out = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    out.paste(
        ink.resize((content[0] * 2, content[1] * 2), Image.LANCZOS),
        (offset[0] * 2, offset[1] * 2),
    )
    return out


def verify(path: Path, size: tuple[int, int]) -> None:
    """Re-open a written file and assert what the brands repo will see."""
    image = Image.open(path)
    assert image.size == size, f"{path.name}: {image.size}, expected {size}"
    assert image.mode == "RGBA", f"{path.name}: mode {image.mode}, expected RGBA"
    low, high = image.getchannel("A").getextrema()
    assert low == 0, f"{path.name}: no fully transparent pixel -- background is not clear"
    assert high == 255, f"{path.name}: nothing fully opaque -- the artwork is washed out"
    print(f"OK {path.name}: {image.size[0]}x{image.size[1]} {image.mode} alpha {low}-{high}")


def main() -> int:
    """Write the three brand files and verify each one."""
    OUT.mkdir(exist_ok=True)

    shutil.copyfile(MARK_256, OUT / "icon.png")
    render_icon_2x().save(OUT / "icon@2x.png")
    shutil.copyfile(LOCKUP_640, OUT / "logo.png")

    verify(OUT / "icon.png", (256, 256))
    verify(OUT / "icon@2x.png", (512, 512))
    verify(OUT / "logo.png", (640, 128))
    return 0


if __name__ == "__main__":
    sys.exit(main())
