"""Upscale all PWA image assets 2x while preserving their visible content exactly."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ASSETS = Path('public/assets')


def main():
    images = sorted(path for path in ASSETS.iterdir() if path.suffix.lower() in {'.jpg', '.jpeg', '.png'})
    for path in images:
        with Image.open(path) as source:
            source.load()
            width, height = source.size
            mode = source.mode
            if mode not in ('RGB', 'RGBA'):
                source = source.convert('RGBA' if 'A' in mode else 'RGB')
            enlarged = source.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
            if path.suffix.lower() in {'.jpg', '.jpeg'}:
                if enlarged.mode != 'RGB':
                    enlarged = enlarged.convert('RGB')
                enlarged.save(path, 'JPEG', quality=95, subsampling=0, optimize=True)
            else:
                enlarged.save(path, 'PNG', optimize=True)
            print(f'{path.name}: {width}x{height} -> {width * 2}x{height * 2}')
    print(f'Upscaled {len(images)} image assets.')


if __name__ == '__main__':
    main()
