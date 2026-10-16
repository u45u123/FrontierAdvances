#!/usr/bin/env python3
"""Split Simplified Chinese body copy at the indented first line of each paragraph."""

import json
from pathlib import Path

import pdfplumber

import rebuild_zh_hans_data_from_pdf as hans


def merge_runs(runs):
    merged = []
    for run in runs:
        if merged and merged[-1]["bold"] == run["bold"]:
            merged[-1]["text"] += run["text"]
        else:
            merged.append(run)
    return merged


def paragraph_blocks(page_number, page):
    words = hans.booklet.page_section_words(page_number, page)["generalInformation"]
    lines = []
    for word in sorted(words, key=lambda item: (item["top"], item["x0"])):
        if not lines or word["top"] - lines[-1][0] > 2:
            lines.append([word["top"], [word]])
        else:
            lines[-1][1].append(word)

    if not lines:
        return []
    baseline = min(min(word["x0"] for word in line) for _, line in lines)
    blocks, active, last_top = [], [], None
    for top, line in lines:
        line_x = min(word["x0"] for word in line)
        # The booklet starts every paragraph with a roughly two-character
        # indent. A large vertical break remains a secondary delimiter.
        new_paragraph = bool(active) and (line_x > baseline + 12 or top - last_top > 20)
        if new_paragraph:
            blocks.append({"runs": merge_runs(active)})
            active = []
        previous = None
        for word in sorted(line, key=lambda item: item["x0"]):
            if previous and word["x0"] - previous["x1"] > 3:
                active.append({"text": " ", "bold": False})
            active.append({
                "text": word["text"],
                "bold": hans.booklet.is_bold(word, "generalInformation"),
            })
            previous = word
        last_top = top
    if active:
        blocks.append({"runs": merge_runs(active)})
    return blocks


with pdfplumber.open(hans.booklet.PDF) as document:
    for day, first_page in enumerate(hans.booklet.PAGE_STARTS, 1):
        path = Path("public/data/zh-Hans") / f"day-{day:02d}.json"
        payload = json.loads(path.read_text())
        payload["generalInformation"] = (
            paragraph_blocks(first_page, document.pages[first_page - 1])
            + paragraph_blocks(first_page + 1, document.pages[first_page])
        )
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        print(f"day-{day:02d}: {len(payload['generalInformation'])} paragraphs")
