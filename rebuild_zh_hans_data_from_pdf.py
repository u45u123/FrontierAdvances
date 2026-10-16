#!/usr/bin/env python3
"""Build Simplified Chinese prayer data from the Simplified Chinese booklet."""

import rebuild_zh_hant_data_from_pdf as booklet


booklet.PDF = booklet.Path(
    "/Users/psj/Downloads/"
    "Chi Simplified Chinese_Prayer Booklet for Acts Now Frontier Advances (Oct 7).pdf"
)
booklet.OUTPUT_DIR = booklet.Path("public/data/zh-Hans")
booklet.REGIONS = {
    "非洲": {"color": "#CFA28F"},
    "阿拉伯世界": {"color": "#B7B281"},
    "印度": {"color": "#D66F4E"},
    "拉丁美洲": {"color": "#9DAFBE"},
    "亚洲其他地区": {"color": "#B69CB4"},
}
booklet.PEOPLE = [
    ("非洲", "富拉尼人"), ("非洲", "奥罗莫加雷人"), ("非洲", "索马里人"),
    ("阿拉伯世界", "阿拉伯文化亲缘群体"), ("阿拉伯世界", "也门人"),
    ("阿拉伯世界", "讲阿拉伯语的阿尔及利亚人"), ("阿拉伯世界", "费扎拉人"),
    ("阿拉伯世界", "苏丹阿拉伯人"), ("印度", "印度前沿民族群体"),
    ("印度", "巴格班人"), ("印度", "婆罗门"), ("印度", "多比人"),
    ("印度", "卡拉尔伊迪加人"), ("印度", "卡普人"), ("印度", "库姆哈尔人"),
    ("印度", "库尔米人"), ("印度", "马拉塔人"), ("印度", "拉杰普特人"),
    ("印度", "萨塔尼人"), ("印度", "谢赫人"), ("印度", "泰利人"),
    ("印度", "亚达夫人"), ("拉丁美洲", "亚马逊地区前沿民族群体"),
    ("亚洲其他地区", "达吉斯坦前沿民族群体"),
    ("亚洲其他地区", "苏拉威西图康贝西前沿民族群体"),
    ("亚洲其他地区", "伊朗前沿民族群体"), ("亚洲其他地区", "马来西亚马来人"),
    ("亚洲其他地区", "马尔代夫人"), ("亚洲其他地区", "努里斯坦人"),
    ("亚洲其他地区", "北大年马来人"), ("亚洲其他地区", "锡尔赫特人"),
]


def section_for_word(page_number, word):
    text, x, top, size = word["text"], word["x0"], word["top"], word["size"]
    if top < 15 or "(cid:" in text:
        return None
    odd_page = page_number % 2 == 1
    if odd_page and x < 215 and size >= 11.5:
        return "scripture"
    if 8.8 <= size <= 10.7 and ((not odd_page and x > 210) or (odd_page and x < 215)):
        return "generalInformation"
    if odd_page and x > 230 and 8.8 <= size <= 11.2:
        return "prayerPoints"
    return None


def is_bold(word, section):
    return section == "scripture" or "bold" in word["fontname"].lower()


booklet.section_for_word = section_for_word
booklet.is_bold = is_bold


if __name__ == "__main__":
    booklet.main()
    index_path = booklet.OUTPUT_DIR / "index.json"
    index = booklet.json.loads(index_path.read_text())
    for entry in index["days"]:
        entry["file"] = entry["file"].replace("data/zh-Hant/", "data/zh-Hans/")
    index_path.write_text(booklet.json.dumps(index, ensure_ascii=False, indent=2) + "\n")
