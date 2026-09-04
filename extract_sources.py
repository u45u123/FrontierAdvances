from __future__ import annotations

import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def docx_paragraphs(path: Path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    results = []
    for p in root.iter(W + "p"):
        pieces = []
        for node in p.iter():
            if node.tag == W + "r":
                text = "".join(t.text or "" for t in node.iter(W + "t"))
                if not text:
                    continue
                props = node.find(W + "rPr")
                bold = props is not None and props.find(W + "b") is not None
                pieces.append({"text": text, "bold": bold})
            elif node.tag == W + "tab":
                pieces.append({"text": "\t", "bold": False})
            elif node.tag == W + "br":
                pieces.append({"text": "\n", "bold": False})
        text = "".join(x["text"] for x in pieces).strip()
        if text:
            style = p.find(W + "pPr/" + W + "pStyle")
            results.append({"style": style.get(W + "val") if style is not None else None, "runs": pieces, "text": text})
    return results


def docx_flow(path: Path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
        rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    relation_map = {item.get("Id"): item.get("Target") for item in rels.iter(PKG + "Relationship")}
    flow = []
    for p in root.iter(W + "p"):
        text = "".join(t.text or "" for t in p.iter(W + "t")).strip()
        image_ids = [node.get(R + "embed") for node in p.iter() if node.tag.endswith("}blip")]
        if text or image_ids:
            flow.append({"text": text, "images": [relation_map.get(x) for x in image_ids]})
    return flow


def xlsx_rows(path: Path):
    with zipfile.ZipFile(path) as z:
        shared_root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        shared = ["".join(t.text or "" for t in item.iter(S + "t")) for item in shared_root.iter(S + "si")]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        rels = ET.fromstring(z.read("xl/worksheets/_rels/sheet1.xml.rels"))
    links = {r.get("Id"): r.get("Target") for r in rels.iter(PKG + "Relationship")}
    hyperlinks = {}
    for h in sheet.iter(S + "hyperlink"):
        cell = h.get("ref")
        rid = h.get(R + "id")
        if cell and rid:
            hyperlinks[cell] = links.get(rid)
    rows = []
    for row in sheet.iter(S + "row"):
        values = {}
        for cell in row.iter(S + "c"):
            ref = cell.get("r")
            value = cell.find(S + "v")
            if value is None:
                continue
            raw = value.text or ""
            value_text = shared[int(raw)] if cell.get("t") == "s" else raw
            values[ref] = {"value": value_text, "url": hyperlinks.get(ref)}
        if values:
            rows.append(values)
    return rows


if __name__ == "__main__":
    kind, file_name = sys.argv[1], Path(sys.argv[2])
    content = docx_paragraphs(file_name) if kind == "docx" else docx_flow(file_name) if kind == "docflow" else xlsx_rows(file_name)
    print(json.dumps(content, ensure_ascii=False, indent=2))
