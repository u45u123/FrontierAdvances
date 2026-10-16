#!/usr/bin/env python3
"""Transfer Traditional Chinese prayer-point emphasis from PDF font sizes."""

import difflib
import json
from collections import Counter
from pathlib import Path

import pdfplumber


PDF = Path("/Users/psj/Downloads/Chi Traditional Chinese_Prayer Booklet for Acts Now Frontier Advances (Oct 7).pdf")
DATA_DIR = Path("public/data/zh-Hant")
PAGE_STARTS = [14, 16, 18, 22, 24, 26, 28, 30, *range(34, 62, 2), 64, *range(68, 84, 2)]


def source_prayer(page):
    words = []
    for word in page.extract_words(extra_attrs=["fontname", "size"], use_text_flow=True):
        if word["x0"] <= 230 or word["top"] <= 15 or not 9 <= word["size"] < 15:
            continue
        if word["text"] == "•" or word["x1"] - word["x0"] < .1:
            continue
        words.append(word)
    base_size = Counter(round(word["size"], 2) for word in words).most_common(1)[0][0]
    source = []
    for word in sorted(words, key=lambda item: (item["top"], item["x0"])):
        # This PDF represents bold as a 0.2pt smaller run than neighboring
        # prayer copy: 9.41/9.60, 10.82/11.04, 9.88/10.08, or 10.35/10.56.
        bold = round(word["size"], 2) < base_size - .1
        source.extend((char, bold) for char in word["text"])
    return source


def merge_runs(runs):
    merged = []
    for run in runs:
        if merged and merged[-1]["bold"] == run["bold"]:
            merged[-1]["text"] += run["text"]
        else:
            merged.append(run)
    return merged


with pdfplumber.open(PDF) as document:
    for day, first_page in enumerate(PAGE_STARTS, 1):
        path = DATA_DIR / f"day-{day:02d}.json"
        payload = json.loads(path.read_text())
        source = source_prayer(document.pages[first_page])
        source_text = "".join(char for char, _ in source)
        target_text = "".join(
            run["text"] for block in payload["prayerPoints"] for run in block["runs"]
        )
        target_bold = {}
        matcher = difflib.SequenceMatcher(None, source_text, target_text, autojunk=False)
        for tag, start_source, end_source, start_target, _ in matcher.get_opcodes():
            if tag == "equal":
                for offset, source_index in enumerate(range(start_source, end_source)):
                    target_bold[start_target + offset] = source[source_index][1]

        position = 0
        for block in payload["prayerPoints"]:
            text = "".join(run["text"] for run in block["runs"])
            old_bold = [run["bold"] for run in block["runs"] for _ in run["text"]]
            runs, active, active_bold = [], "", False
            for index, char in enumerate(text):
                bold = target_bold.get(position + index, old_bold[index])
                if active and bold != active_bold:
                    runs.append({"text": active, "bold": active_bold})
                    active = ""
                active += char
                active_bold = bold
            if active:
                runs.append({"text": active, "bold": active_bold})
            block["runs"] = merge_runs(runs)
            position += len(text)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
