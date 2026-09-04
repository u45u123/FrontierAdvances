"""Extract the Day 1-31 person and map images directly from the DOCX ZIP media folder.

This preserves the original image bytes from Word and only overwrites public/assets;
it never regenerates the manually edited daily JSON files.
"""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from build_prayer_data import DOCX as DOWNLOADS_DOCX, DATA, ASSETS

DOCX = DOWNLOADS_DOCX if DOWNLOADS_DOCX.exists() else Path('Prayer Booklet for Acts Now-Frontier Advances_082026.docx')

# The DOCX stores each day's person photo and map in this verified sequence.
# A few unrelated/duplicate images are also present, so page-flow proximity is not reliable.
MEDIA_PAIRS = {
    1: (118, 119), 2: (120, 121), 3: (122, 124), 4: (126, 127), 5: (129, 130),
    6: (132, 133), 7: (134, 135), 8: (136, 138), 9: (139, 141), 10: (142, 144),
    11: (145, 146), 12: (147, 148), 13: (150, 151), 14: (153, 154), 15: (156, 157),
    16: (159, 160), 17: (162, 163), 18: (165, 166), 19: (168, 169), 20: (171, 172),
    21: (174, 175), 22: (177, 178), 23: (180, 181), 24: (183, 184), 25: (186, 187),
    26: (189, 190), 27: (192, 193), 28: (195, 196), 29: (198, 199), 30: (201, 202),
    31: (204, 205),
}


def media_member(archive: zipfile.ZipFile, number: int) -> str:
    for extension in ('.jpeg', '.jpg', '.png'):
        member = f'word/media/image{number}{extension}'
        if member in archive.namelist():
            return member
    raise FileNotFoundError(f'No media file found for image{number}')


def main():
    written = []
    with zipfile.ZipFile(DOCX) as archive:
        for day, (person_number, map_number) in MEDIA_PAIRS.items():
            data_path = DATA / f'day-{day:02d}.json'
            entry = json.loads(data_path.read_text(encoding='utf-8'))
            for kind, number in (('personImage', person_number), ('mapImage', map_number)):
                source_name = media_member(archive, number)
                suffix = Path(source_name).suffix
                target = ASSETS / f"day-{day:02d}-{'person' if kind == 'personImage' else 'map'}{suffix}"
                previous = Path('public') / entry[kind]['src']
                if previous != target and previous.exists():
                    previous.unlink()
                with archive.open(source_name) as source, target.open('wb') as destination:
                    shutil.copyfileobj(source, destination)
                entry[kind]['src'] = str(target.relative_to(ASSETS.parent))
                written.append((day, target, source_name))
            data_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for day, target, member in written:
        print(f'Day {day:02d}: {target.name} <- {member}')
    print(f'Extracted {len(written)} original DOCX images.')


if __name__ == '__main__':
    main()
