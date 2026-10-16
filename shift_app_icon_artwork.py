#!/usr/bin/env python3
"""Offset a transparent app icon artwork while preserving its canvas size."""

import sys
from pathlib import Path

from PIL import Image


source = Path(sys.argv[1])
destination = Path(sys.argv[2])
offset_x, offset_y = int(sys.argv[3]), int(sys.argv[4])
image = Image.open(source).convert("RGBA")
canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
canvas.alpha_composite(image, (offset_x, offset_y))
canvas.save(destination)
