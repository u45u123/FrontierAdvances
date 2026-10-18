#!/usr/bin/env python3
"""Remove release-date and contact footer bands without changing closing art."""

from pathlib import Path

from PIL import Image, ImageDraw


ASSETS = [
    Path("public/assets/closing-en.png"),
    Path("public/assets/closing-es.png"),
    Path("public/assets/closing-ko.png"),
    Path("public/assets/closing-zh-Hant.png"),
    Path("public/assets/closing-zh-Hans.png"),
]

for path in ASSETS:
    image = Image.open(path).convert("RGBA")
    # All booklets reserve the lower fifth solely for release and contact copy.
    start_y = round(image.height * 0.79)
    background = image.getpixel((16, 16))
    ImageDraw.Draw(image).rectangle((0, start_y, image.width, image.height), fill=background)
    image.save(path)
    print(f"{path}: cleared footer from y={start_y}")
