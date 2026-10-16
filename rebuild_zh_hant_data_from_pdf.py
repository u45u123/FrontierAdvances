#!/usr/bin/env python3
"""Build Traditional Chinese prayer data directly from the source booklet PDF.

The PDF text layer supplies the text, position, paragraph boundaries, and
inline emphasis.  In this booklet inline bold is encoded as a slightly smaller
font size rather than a bold font name, so that difference is preserved too.
"""

import json
from pathlib import Path

import pdfplumber


PDF = Path(
    "/Users/psj/Downloads/"
    "Chi Traditional Chinese_Prayer Booklet for Acts Now Frontier Advances (Oct 7).pdf"
)
SOURCE_DIR = Path("public/data/en")
OUTPUT_DIR = Path("public/data/zh-Hant")
PAGE_STARTS = [14, 16, 18, 22, 24, 26, 28, 30, *range(34, 62, 2), 64, *range(68, 84, 2)]
SECTIONS = ("generalInformation", "scripture", "prayerPoints")

REGIONS = {
    "非洲": {"color": "#CFA28F"},
    "阿拉伯世界": {"color": "#B7B281"},
    "印度": {"color": "#D66F4E"},
    "拉丁美洲": {"color": "#9DAFBE"},
    "亞洲其他地區": {"color": "#B69CB4"},
}
PEOPLE = [
    ("非洲", "富拉尼人"), ("非洲", "奧羅莫加雷人"), ("非洲", "索馬利亞人"),
    ("阿拉伯世界", "阿拉伯文化親緣群體"), ("阿拉伯世界", "葉門人"),
    ("阿拉伯世界", "阿拉伯語阿爾及利亞人"), ("阿拉伯世界", "費扎拉人"),
    ("阿拉伯世界", "蘇丹阿拉伯人"), ("印度", "印度前沿民族群體"),
    ("印度", "巴格班人"), ("印度", "婆羅門"), ("印度", "多比人"),
    ("印度", "卡拉爾伊迪加人"), ("印度", "卡普人"), ("印度", "庫姆哈爾人"),
    ("印度", "庫爾米人"), ("印度", "馬拉塔人"), ("印度", "拉傑普特人"),
    ("印度", "薩塔尼人"), ("印度", "謝赫人"), ("印度", "泰利人"),
    ("印度", "亞達夫人"), ("拉丁美洲", "亞馬遜地區前沿民族群體"),
    ("亞洲其他地區", "達吉斯坦前沿民族群體"),
    ("亞洲其他地區", "蘇拉威西圖康貝西前沿民族群體"),
    ("亞洲其他地區", "伊朗前沿民族群體"), ("亞洲其他地區", "馬來西亞馬來人"),
    ("亞洲其他地區", "馬爾地夫人"), ("亞洲其他地區", "努里斯坦人"),
    ("亞洲其他地區", "北大年馬來人"), ("亞洲其他地區", "錫爾赫特人"),
]


def section_for_word(page_number, word):
    """Classify just the body areas rendered by the web app."""
    text, x, top, size = word["text"], word["x0"], word["top"], word["size"]
    if top < 15 or "(cid:" in text:
        return None
    odd_page = page_number % 2 == 1
    if odd_page and x < 215 and size >= 13:
        return "scripture"
    # General copy is on the right of an even page and left of an odd page.
    if 9.2 <= size <= 10.5 and ((not odd_page and x > 210) or (odd_page and x < 215)):
        return "generalInformation"
    # Prayer columns use 9.6pt early in the booklet and 11.04pt in most
    # later pages; the heading is 20.71pt and is intentionally excluded.
    if odd_page and x > 230 and 9.2 <= size <= 11.2:
        return "prayerPoints"
    return None


def page_section_words(page_number, page):
    result = {section: [] for section in SECTIONS}
    seen = set()
    for word in page.extract_words(extra_attrs=["fontname", "size"], use_text_flow=True):
        # A few bullet marks are duplicated zero-width drawing instructions.
        if word["text"] == "•" or word["x1"] - word["x0"] < 0.1:
            continue
        section = section_for_word(page_number, word)
        if not section:
            continue
        key = (section, round(word["x0"], 2), round(word["x1"], 2), round(word["top"], 2), word["text"])
        if key not in seen:
            result[section].append(word)
            seen.add(key)
    return result


def is_bold(word, section):
    # Body emphasis is encoded at 9.88pt (general) or 9.41pt (prayers), while
    # the neighboring regular copy is 10.08pt / 9.60pt respectively.
    if section == "generalInformation":
        return word["size"] < 10
    if section == "prayerPoints":
        return word["size"] < 9.5
    # Scripture is visually a display treatment in the booklet.
    return True


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


def as_lines(words, section):
    lines = []
    for word in sorted(words, key=lambda item: (item["top"], item["x0"])):
        if not lines or word["top"] - lines[-1][0] > 2:
            lines.append([word["top"], [word]])
        else:
            lines[-1][1].append(word)
    rendered = []
    for top, line in lines:
        runs = []
        previous = None
        for word in sorted(line, key=lambda item: item["x0"]):
            # Chinese prose has no word spaces. Retain only intentional wide
            # gaps, which occur around Latin-script terms in the booklet.
            if previous and word["x0"] - previous["x1"] > 3:
                runs.append({"text": " ", "bold": False})
            runs.append({"text": word["text"], "bold": is_bold(word, section)})
            previous = word
        rendered.append((top, merge_runs(runs)))
    return rendered


def extract_day(pdf, first_page):
    collected = {section: [] for section in SECTIONS}
    for page_number in (first_page, first_page + 1):
        sections = page_section_words(page_number, pdf.pages[page_number - 1])
        for section in SECTIONS:
            lines = as_lines(sections[section], section)
            if collected[section] and lines:
                collected[section].append((None, None))
            collected[section].extend(lines)

    extracted = {}
    for section, lines in collected.items():
        blocks = []
        for top, runs in lines:
            if top is None:
                blocks.append(None)
            elif not blocks or blocks[-1] is None or top - blocks[-1]["last_top"] > 20:
                blocks.append({"last_top": top, "runs": list(runs)})
            else:
                blocks[-1]["runs"].extend(runs)
                blocks[-1]["last_top"] = top
        extracted[section] = [
            {"runs": merge_runs(block["runs"])} for block in blocks if block is not None
        ]
    return extracted


def main():
    if not PDF.is_file():
        raise SystemExit(f"PDF not found: {PDF}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index_days = []
    with pdfplumber.open(PDF) as pdf:
        for day, (first_page, (region, people_name)) in enumerate(zip(PAGE_STARTS, PEOPLE), start=1):
            payload = json.loads((SOURCE_DIR / f"day-{day:02d}.json").read_text())
            payload["region"] = region
            payload["peopleName"] = people_name
            payload.update(extract_day(pdf, first_page))
            destination = OUTPUT_DIR / f"day-{day:02d}.json"
            destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            index_days.append({"day": day, "region": region, "peopleName": people_name, "file": f"data/zh-Hant/day-{day:02d}.json"})
            print(f"day-{day:02d}: " + ", ".join(f"{name}={len(payload[name])}" for name in SECTIONS))
    (OUTPUT_DIR / "index.json").write_text(json.dumps({"regions": REGIONS, "days": index_days}, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
