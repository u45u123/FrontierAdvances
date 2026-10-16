#!/usr/bin/env python3
"""Extract Simplified Chinese statistics from the booklet's left-hand panels."""

import json
import re
from pathlib import Path

import pdfplumber


PDF = Path("/Users/psj/Downloads/Chi Simplified Chinese_Prayer Booklet for Acts Now Frontier Advances (Oct 7).pdf")
DATA_DIR = Path("public/data/zh-Hans")
PAGE_STARTS = [14, 16, 18, 22, 24, 26, 28, 30, *range(34, 62, 2), 64, *range(68, 84, 2)]


def statistics_from_page(page):
    text = page.crop((20, 0, 215, page.height)).extract_text(use_text_flow=True) or ""
    rows, current = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("DAY "):
            break
        if line.startswith("•"):
            if current:
                rows.append(current)
            current = line[1:].strip()
        elif current and line:
            current += line
    if current:
        rows.append(current)

    statistics = []
    for row in rows:
        match = re.match(r"(.+?)[：:](.+)", row)
        if match:
            label, value = match.groups()
        elif row.endswith("已启动"):
            label, value = row[:-3], "已启动"
        elif row.endswith("已有"):
            label, value = row[:-2], "已有"
        elif row.endswith("无"):
            label, value = row[:-1], "无"
        else:
            label, value = row, ""
        statistics.append({"label": label.strip(), "value": value.strip()})
    return statistics


with pdfplumber.open(PDF) as document:
    for day, page_number in enumerate(PAGE_STARTS, 1):
        path = DATA_DIR / f"day-{day:02d}.json"
        payload = json.loads(path.read_text())
        payload["statistics"] = statistics_from_page(document.pages[page_number - 1])
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        print(f"day-{day:02d}: {len(payload['statistics'])} rows")
