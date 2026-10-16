#!/usr/bin/env python3
"""Join PDF-wrapped Traditional Chinese scripture into a single verse block."""

import json
from pathlib import Path


for path in Path("public/data/zh-Hant").glob("day-*.json"):
    payload = json.loads(path.read_text())
    blocks = payload["scripture"]
    if len(blocks) == 1:
        # A single page keeps the final book name and chapter in the same PDF
        # line; split that exceptional form into verse and reference.
        combined = "".join(run["text"] for run in blocks[0]["runs"])
        marker = max(combined.rfind(name) for name in ("詩篇", "約翰福音", "彼得前書", "提摩太後書", "提摩太后書", "腓立比書"))
        if marker < 0:
            raise ValueError(f"Could not find scripture reference in {path}")
        verse, reference = combined[:marker], combined[marker:]
    else:
        verse = "".join(run["text"] for block in blocks[:-1] for run in block["runs"])
        reference = "".join(run["text"] for run in blocks[-1]["runs"])
    payload["scripture"] = [
        {"runs": [{"text": verse, "bold": True}]},
        {"runs": [{"text": reference, "bold": True}]},
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
