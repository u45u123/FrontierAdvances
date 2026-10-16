#!/usr/bin/env python3
"""Center the visible (alpha-weighted) logo within each PWA icon canvas."""

import sys
from pathlib import Path

from PIL import Image


source = Path(sys.argv[1])
destination = Path(sys.argv[2])
image = Image.open(source).convert("RGBA")
alpha = image.getchannel("A")
total = sum(alpha.getdata())
center_x = sum(x * alpha.getpixel((x, y)) for y in range(image.height) for x in range(image.width)) / total
center_y = sum(y * alpha.getpixel((x, y)) for y in range(image.height) for x in range(image.width)) / total
offset_x = round((image.width - 1) / 2 - center_x)
offset_y = round((image.height - 1) / 2 - center_y)
canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
canvas.alpha_composite(image, (offset_x, offset_y))
canvas.save(destination)
print(f"{source.name}: moved {offset_x:+d}px horizontally, {offset_y:+d}px vertically")
