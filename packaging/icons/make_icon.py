"""Draw the app's monogram icon, `nexus-scholar.ico` (M13 Part W).

A plain "NS" monogram in the brand's archive blue (`brand` #24456e, `on-brand`
#ffffff, `docs/ux/brand/tokens.json`) until a logo exists; `nexus-scholar.svg`
beside it is the same design as a vector. Pillow draws it with its own built-in
font, so the result does not depend on the fonts of the computer that runs it.

Run it in a throw-away environment and commit the result:

    uv run --no-project --with "pillow>=11" python packaging/icons/make_icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BRAND = (0x24, 0x45, 0x6E, 255)
ON_BRAND = (255, 255, 255, 255)
SIZES = [16, 24, 32, 48, 64, 128, 256]
HERE = Path(__file__).resolve().parent


def draw(size: int = 256) -> Image.Image:
    scale = 4  # drawn large, then reduced, for smooth edges
    big = size * scale
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    canvas = ImageDraw.Draw(image)
    inset = big // 32
    canvas.rounded_rectangle((inset, inset, big - inset, big - inset), radius=big // 5, fill=BRAND)
    font = ImageFont.load_default(size=int(big * 0.46))
    box = canvas.textbbox((0, 0), "NS", font=font, stroke_width=big // 96)
    width, height = box[2] - box[0], box[3] - box[1]
    origin = ((big - width) / 2 - box[0], (big - height) / 2 - box[1])
    canvas.text(origin, "NS", font=font, fill=ON_BRAND, stroke_width=big // 96, stroke_fill=ON_BRAND)
    return image.resize((size, size), Image.LANCZOS)


def main() -> None:
    art = draw(256)
    art.save(HERE / "nexus-scholar.ico", sizes=[(s, s) for s in SIZES])
    art.save(HERE / "nexus-scholar-256.png")
    print(f"wrote {HERE / 'nexus-scholar.ico'} and the 256 px PNG")


if __name__ == "__main__":
    main()
