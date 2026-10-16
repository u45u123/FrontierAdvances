#!/usr/bin/env python3
"""Rebuild Korean rich text from the booklet PDF, preserving JSON metadata.

The booklet is the source of truth for general information, Scripture, prayer
points, and inline bold. All other fields in each day JSON are preserved.
"""

import argparse
import json
from pathlib import Path

import pdfplumber


DEFAULT_PDF = Path(
    "/Users/psj/Downloads/"
    "Korean_Prayer Booklet for Acts Now-Frontier Advances - Korean Revison (Sept 30).pdf"
)
DATA_DIR = Path("public/data/ko")
PAGE_STARTS = [14, 16, 18, 22, 24, 26, 28, 30, *range(34, 62, 2), 64, *range(68, 84, 2)]
SECTIONS = ("generalInformation", "scripture", "prayerPoints")


def is_bold(font_name):
    font_name = font_name.lower()
    return "bold" in font_name or "dotumpb" in font_name


def section_for_word(page_number, word):
    """Classify only the three text areas used by the web app."""
    if word["top"] < 30 or "(cid:" in word["text"]:
        return None
    font = word["fontname"].lower()
    size = word["size"]
    x = word["x0"]
    odd_page = page_number % 2 == 1
    if "kopubdotump" in font and 9.5 <= size <= 10.5:
        if (not odd_page and x > 210) or (odd_page and x < 210):
            return "generalInformation"
        if odd_page and x > 230:
            return "prayerPoints"
    if odd_page and x < 215 and size >= 13:
        return "scripture"
    return None


def page_section_words(page_number, page):
    """Return de-duplicated words for every target section on one PDF page."""
    result = {section: [] for section in SECTIONS}
    seen = set()
    for word in page.extract_words(extra_attrs=["fontname", "size"], use_text_flow=True):
        # Zero-width bullets are duplicate drawing instructions, not content.
        if word["text"] == "•" and word["x1"] - word["x0"] < 0.1:
            continue
        section = section_for_word(page_number, word)
        if not section:
            continue
        key = (section, round(word["x0"], 2), round(word["x1"], 2), round(word["top"], 2), word["text"])
        if key in seen:
            continue
        seen.add(key)
        result[section].append(word)
    return result


def as_lines(words):
    """Put PDF words back into visual lines, including inline bold metadata."""
    lines = []
    for word in sorted(words, key=lambda item: (item["top"], item["x0"])):
        if not lines or word["top"] - lines[-1][0] > 2:
            lines.append([word["top"], [word]])
        else:
            lines[-1][1].append(word)

    rendered = []
    for top, line in lines:
        runs = []
        sorted_line = sorted(line, key=lambda item: item["x0"])
        for index, word in enumerate(sorted_line):
            if index and word["x0"] - sorted_line[index - 1]["x1"] > 1:
                runs.append({"text": " ", "bold": False})
            runs.append({"text": word["text"], "bold": is_bold(word["fontname"])})
        rendered.append((top, merge_runs(runs)))
    return rendered


def merge_runs(runs):
    merged = []
    for run in runs:
        if not run["text"]:
            continue
        if merged and merged[-1]["bold"] == run["bold"]:
            merged[-1]["text"] += run["text"]
        else:
            merged.append(dict(run))
    return merged


def lines_to_blocks(lines):
    """A vertical gap marks a new source paragraph or prayer point."""
    blocks = []
    for top, line_runs in lines:
        if not blocks or top - blocks[-1]["last_top"] > 20:
            blocks.append({"last_top": top, "runs": []})
        blocks[-1]["runs"].extend(line_runs)
        blocks[-1]["last_top"] = top
    return [{"runs": merge_runs(block["runs"])} for block in blocks]


def extract_day(pdf, first_page):
    by_section = {section: [] for section in SECTIONS}
    for page_number in (first_page, first_page + 1):
        page_words = page_section_words(page_number, pdf.pages[page_number - 1])
        for section in SECTIONS:
            # Pages are separate physical columns; never join their final and
            # initial paragraphs merely because their y coordinates are close.
            lines = as_lines(page_words[section])
            if by_section[section] and lines:
                by_section[section].append((None, None))
            by_section[section].extend(lines)

    output = {}
    for section, lines in by_section.items():
        blocks = []
        for top, runs in lines:
            if top is None:
                blocks.append(None)
                continue
            if not blocks or blocks[-1] is None or top - blocks[-1]["last_top"] > 20:
                blocks.append({"last_top": top, "runs": []})
            elif blocks[-1]["runs"]:
                # PDF line wrapping replaces an ordinary word space. Restore it
                # so the extracted web text reads naturally after reflowing.
                blocks[-1]["runs"].append({"text": " ", "bold": False})
            blocks[-1]["runs"].extend(runs)
            blocks[-1]["last_top"] = top
        output[section] = [
            {"runs": merge_runs(block["runs"])}
            for block in blocks
            if block is not None
        ]
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--write", action="store_true", help="Write extracted sections; defaults to a dry run.")
    args = parser.parse_args()
    if not args.pdf.is_file():
        raise SystemExit(f"PDF not found: {args.pdf}")

    with pdfplumber.open(args.pdf) as pdf:
        for day, first_page in enumerate(PAGE_STARTS, start=1):
            path = DATA_DIR / f"day-{day:02d}.json"
            payload = json.loads(path.read_text())
            extracted = extract_day(pdf, first_page)
            for section in SECTIONS:
                payload[section] = extracted[section]
            print(
                f"day-{day:02d}: "
                + ", ".join(f"{section}={len(extracted[section])}" for section in SECTIONS)
            )
            if args.write:
                path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
