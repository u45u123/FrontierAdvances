#!/usr/bin/env python3
"""Create Spanish prayer data from the Spanish booklet PDF and Vision OCR."""

import difflib
import json
import re
import shutil
import unicodedata
from pathlib import Path

import pdfplumber


PDF = Path("/Users/psj/Downloads/Esp_Prayer Booklet for Acts Now-Frontier Advances - Spanish Revison (Sept 26).pdf")
OCR_DIR = Path("tmp/pdfs/es-booklet-300")
SOURCE_DIR = Path("public/data/en")
OUTPUT_DIR = Path("public/data/es")
PAGE_STARTS = [14, 16, 18, 22, 24, 26, 28, 30, *range(34, 62, 2), 64, *range(68, 84, 2)]
SECTIONS = ("generalInformation", "scripture", "prayerPoints")
PEOPLE = [
    "Fulani / Fulbe", "Oromo Garre", "Somalí", "Árabes como grupo de afinidad", "Yemenís",
    "Argelinos de habla árabe", "Fezara", "Árabes sudaneses", "PF en India", "Baghban",
    "Brahmin", "Dhobi", "Kalal Idiga", "Kapu", "Kumhar", "Kurmi", "Mahratta", "Rajput",
    "Satani", "Shaikh", "Teli", "Yadav", "PF en Las Amazonas", "PF en Daguestán",
    "PF en Tukangbesi de Sulawesi", "PF en Irán", "Malayos de Malasia", "Maldivos", "Nuristani",
    "Malayos Pattani", "Sylheti",
]
REGIONS = ["África"] * 3 + ["Árabes"] * 5 + ["India"] * 14 + ["América Latina"] + ["Asia otros"] * 8


def is_bold(font):
    return "bold" in font.lower() or "semibold" in font.lower()


def source_section(page_number, word):
    # Running headers sit at ~12pt; body copy begins around 20pt on a few pages.
    if word["top"] < 15 or "(cid:" in word["text"]:
        return None
    font, size, x = word["fontname"].lower(), word["size"], word["x0"]
    odd = page_number % 2 == 1
    if "zalandosans" in font and 9 <= size <= 10:
        if (not odd and x > 215) or (odd and x < 215):
            return "generalInformation"
        if odd and x > 230:
            return "prayerPoints"
    if odd and x < 215 and size >= 13:
        return "scripture"
    return None


def source_lines(page_number, page):
    by_section = {section: [] for section in SECTIONS}
    words = []
    for word in page.extract_words(extra_attrs=["fontname", "size"], use_text_flow=True):
        section = source_section(page_number, word)
        if section:
            words.append((section, word))
    for section in SECTIONS:
        section_words = [word for item_section, word in words if item_section == section]
        lines = []
        for word in sorted(section_words, key=lambda item: (item["top"], item["x0"])):
            if not lines or word["top"] - lines[-1]["top"] > 2:
                lines.append({"top": word["top"], "words": [word]})
            else:
                lines[-1]["words"].append(word)
        for line in lines:
            line["words"].sort(key=lambda item: item["x0"])
            line["x0"] = line["words"][0]["x0"]
            line["x1"] = line["words"][-1]["x1"]
        by_section[section] = lines
    return by_section


def nearest_source_line(ocr_line, source_by_section, page_height):
    top = (1 - ocr_line["y"] - ocr_line["height"]) * page_height
    x0, x1 = ocr_line["x"] * 419.528, (ocr_line["x"] + ocr_line["width"]) * 419.528
    candidates = []
    for section, lines in source_by_section.items():
        for line in lines:
            y_distance = abs(line["top"] - top)
            x_distance = max(0, line["x0"] - x1, x0 - line["x1"])
            candidates.append((y_distance * 3 + x_distance, section, line, top))
    _, section, line, _ = min(candidates, key=lambda item: item[0])
    return section, line, top


def bold_runs(ocr_text, pdf_words):
    """Transfer PDF font weight to OCR text using a whitespace-free alignment."""
    source_text = "".join(word["text"] for word in pdf_words)
    source_bold = []
    for word in pdf_words:
        source_bold.extend([is_bold(word["fontname"])] * len(word["text"]))
    target_positions = [index for index, char in enumerate(ocr_text) if not char.isspace()]
    target_text = "".join(ocr_text[index] for index in target_positions)
    target_bold = set()
    fold = lambda value: "".join(
        character for character in unicodedata.normalize("NFD", value.lower()) if not unicodedata.combining(character)
    )
    matcher = difflib.SequenceMatcher(None, fold(source_text), fold(target_text), autojunk=False)
    target_characters = list(ocr_text)
    for tag, source_start, source_end, target_start, _ in matcher.get_opcodes():
        if tag != "equal":
            continue
        for offset, source_index in enumerate(range(source_start, source_end)):
            if source_bold[source_index]:
                target_bold.add(target_positions[target_start + offset])
            # Retain accents, capitalization, and punctuation from the PDF text
            # layer while retaining spaces restored by Vision OCR.
            target_characters[target_positions[target_start + offset]] = source_text[source_index]
    runs, active_text, active_bold = [], "", False
    for index, char in enumerate(target_characters):
        bold = index in target_bold if not char.isspace() else active_bold
        if active_text and bold != active_bold:
            runs.append({"text": active_text, "bold": active_bold})
            active_text = ""
        active_text += char
        active_bold = bold
    if active_text:
        runs.append({"text": active_text, "bold": active_bold})
    return merge_runs(runs)


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


def extract_day(pdf, first_page):
    collected = {section: [] for section in SECTIONS}
    for page_number in (first_page, first_page + 1):
        ocr_lines = json.loads((OCR_DIR / f"page-{page_number}.json").read_text())
        source_by_section = source_lines(page_number, pdf.pages[page_number - 1])
        for ocr_line in ocr_lines:
            text = ocr_line["text"].lstrip("• ").strip()
            # Vision occasionally misses the one space at a wrapped PDF word
            # boundary. These corrections are verified against the page image.
            text = text.replace("principalmenteen", "principalmente en")
            if not text:
                continue
            # Ignore the hero/statistics column on even pages and the narrow
            # gutter between columns. On odd pages the right column is prayer.
            if page_number % 2 == 0 and ocr_line["x"] < 0.5:
                continue
            if page_number % 2 == 1 and 0.5 <= ocr_line["x"] <= 0.53:
                continue
            section, source_line, top = nearest_source_line(ocr_line, source_by_section, pdf.pages[page_number - 1].height)
            if page_number % 2 == 1 and ocr_line["x"] > 0.53 and section != "prayerPoints":
                continue
            if page_number % 2 == 1 and ocr_line["x"] < 0.5 and section == "prayerPoints":
                continue
            # OCR may see page headers or source credits near the text columns.
            if abs(source_line["top"] - top) > 7:
                continue
            collected[section].append((page_number, top, bold_runs(text, source_line["words"])))

    result = {}
    for section, lines in collected.items():
        blocks = []
        for page_number, top, runs in sorted(lines, key=lambda item: (item[0], item[1])):
            if not blocks or page_number != blocks[-1]["page"] or top - blocks[-1]["top"] > 18:
                blocks.append({"page": page_number, "top": top, "runs": []})
            elif blocks[-1]["runs"]:
                blocks[-1]["runs"].append({"text": " ", "bold": False})
            blocks[-1]["runs"].extend(runs)
            blocks[-1]["top"] = top
        result[section] = [{"runs": merge_runs(block["runs"])} for block in blocks]
    return result


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_DIR / "index.json", OUTPUT_DIR / "index.json")
    index = json.loads((OUTPUT_DIR / "index.json").read_text())
    index["regions"] = {
        "África": {"color": "#CFA28F"}, "Árabes": {"color": "#9B8DB7"}, "India": {"color": "#D4945D"},
        "América Latina": {"color": "#AA8B72"}, "Asia otros": {"color": "#6D9EAE"},
    }
    with pdfplumber.open(PDF) as pdf:
        for day, (first_page, people_name, region) in enumerate(zip(PAGE_STARTS, PEOPLE, REGIONS), start=1):
            payload = json.loads((SOURCE_DIR / f"day-{day:02d}.json").read_text())
            payload["peopleName"] = people_name
            payload["region"] = region
            payload.update(extract_day(pdf, first_page))
            (OUTPUT_DIR / f"day-{day:02d}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            index["days"][day - 1].update({"peopleName": people_name, "region": region, "file": f"data/es/day-{day:02d}.json"})
            print(f"day-{day:02d}: " + ", ".join(f"{key}={len(payload[key])}" for key in SECTIONS))
    (OUTPUT_DIR / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
