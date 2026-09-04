#!/usr/bin/env python3
"""Apply the official Real-ESRGAN general-photo model to profile assets only.

The model natively produces 4× images.  We reduce that output to 2× using
Lanczos so the PWA stays reasonably small while retaining the model's restored
detail.  Maps are intentionally excluded: AI reconstruction can corrupt their
place names, borders, and legend text.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


RUNTIME = Path("/private/tmp/acts-now-ai-upscale")
MODEL = RUNTIME / "models" / "realesr-general-x4v3.pth"
ASSETS = Path(__file__).parent / "public" / "assets"

sys.path.insert(0, str(RUNTIME))

import torch  # noqa: E402
from PIL import Image  # noqa: E402
from torch import nn  # noqa: E402
from torch.nn import functional as F  # noqa: E402


class SRVGGNetCompact(nn.Module):
    """The small official network definition used by realesr-general-x4v3."""

    def __init__(self) -> None:
        super().__init__()
        layers: list[nn.Module] = [nn.Conv2d(3, 64, 3, 1, 1), nn.PReLU(64)]
        # This official "general" model was trained with 32 body convolutions.
        for _ in range(32):
            layers.extend([nn.Conv2d(64, 64, 3, 1, 1), nn.PReLU(64)])
        layers.append(nn.Conv2d(64, 48, 3, 1, 1))
        self.body = nn.ModuleList(layers)
        self.upsampler = nn.PixelShuffle(4)

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        output = image
        for layer in self.body:
            output = layer(output)
        output = self.upsampler(output)
        return output + F.interpolate(image, scale_factor=4, mode="nearest")


def load_model() -> SRVGGNetCompact:
    if not MODEL.exists():
        raise SystemExit(f"Missing model file: {MODEL}")
    checkpoint = torch.load(MODEL, map_location="cpu", weights_only=True)
    state = checkpoint.get("params_ema", checkpoint.get("params", checkpoint))
    model = SRVGGNetCompact().eval()
    model.load_state_dict(state, strict=True)
    return model


def enhance(path: Path, model: SRVGGNetCompact) -> None:
    with Image.open(path) as opened:
        source = opened.convert("RGB")
    width, height = source.size
    pixels = torch.from_numpy(__import__("numpy").asarray(source).copy()).permute(2, 0, 1).float()
    pixels = (pixels / 255.0).unsqueeze(0)
    with torch.inference_mode():
        result = model(pixels).squeeze(0).clamp(0, 1)
    output = result.permute(1, 2, 0).mul(255).round().byte().numpy()
    restored = Image.fromarray(output, "RGB")
    restored = restored.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
    temporary = path.with_suffix(path.suffix + ".upscaling")
    restored.save(temporary, format="PNG" if path.suffix.lower() == ".png" else "JPEG", quality=95, subsampling=0)
    temporary.replace(path)
    print(f"{path.name}: {width}×{height} → {width * 2}×{height * 2}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", type=int, help="Process one day only for a sample check")
    parser.add_argument("--first-day", type=int, default=1, help="First day to process in a batch")
    args = parser.parse_args()
    targets = [ASSETS / f"day-{args.day:02d}-person.jpeg"] if args.day else [
        ASSETS / f"day-{day:02d}-person.jpeg" for day in range(args.first_day, 32)
    ]
    targets = [path for path in targets if path.suffix.lower() in {".jpeg", ".jpg", ".png"}]
    if not targets:
        raise SystemExit("No profile assets found.")
    model = load_model()
    for target in targets:
        enhance(target, model)


if __name__ == "__main__":
    main()
