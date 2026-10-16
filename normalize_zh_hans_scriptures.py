#!/usr/bin/env python3
"""Join PDF-wrapped Simplified Chinese scripture into verse and reference blocks."""

import json
from pathlib import Path


for path in Path("public/data/zh-Hans").glob("day-*.json"):
    payload = json.loads(path.read_text())
    blocks = payload["scripture"]
    verse = "".join(run["text"] for block in blocks[:-1] for run in block["runs"])
    reference = "".join(run["text"] for run in blocks[-1]["runs"])
    payload["scripture"] = [
        {"runs": [{"text": verse, "bold": True}]},
        {"runs": [{"text": reference, "bold": True}]},
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
