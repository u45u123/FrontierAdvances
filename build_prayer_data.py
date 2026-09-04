from __future__ import annotations

import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

from extract_sources import docx_flow, docx_paragraphs, xlsx_rows

ROOT = Path(__file__).parent
DOCX = Path('/Users/psj/Downloads/Prayer Booklet for Acts Now-Frontier Advances_082026.docx')
XLSX = Path('/Users/psj/Downloads/FPG people and map 4.xlsx')
OUT = ROOT / 'public'
ASSETS = OUT / 'assets'
DATA = OUT / 'data'

NAMES = [
    'Fulani / Fulbe', 'Oromo Garre', 'Somali', 'Arabs as an Affinity Group', 'Yemeni',
    'Arabic-speaking Algerian', 'Fezara', 'Sudanese Arab', 'FPGs in India', 'Baghban',
    'Brahmin', 'Dhobi', 'Kalal Idiga', 'Kapu', 'Kumhar', 'Kurmi', 'Mahratta', 'Rajput',
    'Satani', 'Shaikh', 'Teli', 'Yadav', 'FPGs in the Amazon', 'FPGs in Dagestan',
    'FPGs in Tukangbesi of Sulawesi', 'FPGs in Iran', 'Malay of Malaysia', 'Maldivian',
    'Nuristani', 'Pattani Malay', 'Sylheti'
]

# Sampled from the region title panels in the supplied PDF.
REGIONS = {
    'Africa': {'color': '#CFA28F'},
    'Arabs': {'color': '#B7B281'},
    'India': {'color': '#D66F4E'},
    'Latin America': {'color': '#9DAFBE'},
    'Other Asia': {'color': '#B69CB4'},
}

def clean(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()

def source_records():
    groups, active = {}, None
    for row in xlsx_rows(XLSX):
        values = {cell[0]: value for cell, value in row.items()}
        name = values.get('A', {}).get('value')
        if name:
            active = clean(name)
            groups[active] = {}
        if active and values.get('B', {}).get('value') in ('Person', 'Map'):
            kind = values['B']['value'].lower()
            groups[active][kind] = {
                'source': values.get('C', {}).get('value', ''),
            }
    aliases = {
        'Fulani / Fulbe': 'Fulani',
        'Arabs as an Affinity Group': 'Arabs as an Affinity Group',
        'FPGs in Tukangbesi of Sulawesi': 'FPGs in Tukangbesi of Sulawesi',
    }
    return {name: groups.get(aliases.get(name, name), {}) for name in NAMES}

def day_blocks(paragraphs):
    starts = []
    for i, p in enumerate(paragraphs):
        match = re.match(r'^DAY\s*(\d{2})DAY', clean(p['text']))
        if match:
            starts.append((int(match.group(1)), i))
    return {day: (start, starts[pos + 1][1] if pos + 1 < len(starts) else len(paragraphs)) for pos, (day, start) in enumerate(starts)}

def compact_runs(runs):
    merged = []
    for run in runs:
        value = clean(run['text'])
        if not value:
            continue
        if merged and merged[-1]['bold'] == run['bold']:
            merged[-1]['text'] += ' ' + value
        else:
            merged.append({'text': value, 'bold': bool(run['bold'])})
    return merged

def paragraphs_to_blocks(items):
    return [{'runs': compact_runs(p['runs'])} for p in items if clean(p['text']) and compact_runs(p['runs'])]

def get_stats(segment):
    first = next((i for i, p in enumerate(segment) if clean(p['text']).startswith('Population:')), None)
    if first is None:
        return []
    result, pending = [], None
    for p in segment[first:first + 18]:
        text = clean(p['text'])
        if not text or text.startswith('Photo Source:'):
            continue
        if len(text) > 115 and ':' not in text:
            break
        if ':' in text:
            label, value = text.split(':', 1)
            if label in ('Population', 'Religion', 'Language', 'Christian') or label.startswith('Bible') or label.startswith('Jesus'):
                pending = {'label': label, 'value': value.strip()}
                result.append(pending)
                continue
        if pending and len(text) < 60 and not text.startswith(('DAY', 'Prayer')):
            pending['value'] = clean(pending['value'] + ' ' + text)
        elif len(text) > 100:
            break
    return result

def text_index(segment, predicate, start=0):
    for i in range(start, len(segment)):
        if predicate(clean(segment[i]['text'])):
            return i
    return None

def section_content(segment):
    stats = get_stats(segment)
    stat_start = text_index(segment, lambda s: s.startswith('Population:')) or 0
    content_start = stat_start + 1
    for i in range(stat_start, min(len(segment), stat_start + 22)):
        text = clean(segment[i]['text'])
        if len(text) > 115 and ':' not in text:
            content_start = i
            break
    prayer_positions = [i for i, p in enumerate(segment) if clean(p['text']) == 'Prayer Points']
    prayer_start = prayer_positions[-1] if prayer_positions else len(segment)
    refs = [i for i, p in enumerate(segment[:prayer_start]) if re.match(r'^(Psalm|John|Matthew|Mark|Luke|Acts|Romans|[1-3] (?:Corinthians|Timothy|Peter|John)|Genesis|Philippians|Isaiah|Ephesians|Hebrews)\b', clean(p['text']))]
    ref = refs[-1] if refs else prayer_start
    verse_start = max(content_start, ref - 3)
    while verse_start < ref and clean(segment[verse_start]['text']).startswith(('Photo Source:', 'DAY')):
        verse_start += 1
    general = [p for p in segment[content_start:verse_start] if not clean(p['text']).startswith(('Photo Source:',)) and ' | ' not in clean(p['text'])]
    scripture = [p for p in segment[verse_start:ref + 1] if clean(p['text']) and ' | ' not in clean(p['text'])]
    prayers = [p for p in segment[prayer_start + 1:] if clean(p['text']) and ' | ' not in clean(p['text']) and not clean(p['text']).startswith('Photo Source:')]
    # The Somali map is editable text in the DOCX and follows its prayer list. It is not prayer content.
    if len(prayers) > 20:
        prayers = prayers[:7]
    return stats, paragraphs_to_blocks(general), paragraphs_to_blocks(scripture), paragraphs_to_blocks(prayers)

def image_for_block(flow, start, end, before=False):
    scan = range(start - 1, max(-1, start - 8), -1) if before else range(start, end)
    for i in scan:
        images = flow[i]['images']
        if images:
            return images[-1] if before else images[0]
    return None

def images_in_block(flow, start, end):
    return [image for item in flow[start:end] for image in item['images']]

def media_url(member, slug):
    if not member:
        return ''
    suffix = Path(member).suffix.lower() or '.jpg'
    target = ASSETS / f'{slug}{suffix}'
    with zipfile.ZipFile(DOCX) as archive, archive.open('word/' + member) as source, target.open('wb') as dest:
        shutil.copyfileobj(source, dest)
    return f'assets/{target.name}'

def main():
    OUT.mkdir(exist_ok=True)
    if DATA.exists():
        shutil.rmtree(DATA)
    DATA.mkdir()
    if ASSETS.exists():
        shutil.rmtree(ASSETS)
    ASSETS.mkdir()
    paragraphs = docx_paragraphs(DOCX)
    flow = docx_flow(DOCX)
    blocks = day_blocks(paragraphs)
    sources = source_records()
    # The DOCX page flow is used for embedded visuals; day pages contain a person image before the Day marker and a map image later on the page.
    flow_starts = day_blocks([{'text': p['text']} for p in flow])
    data = []
    for day, name in enumerate(NAMES, 1):
        start, end = blocks[day]
        stats, general, scripture, prayers = section_content(paragraphs[start:end])
        fstart, fend = flow_starts[day]
        in_block = images_in_block(flow, fstart, fend)
        person_member = image_for_block(flow, fstart, fend, before=True) or (in_block[0] if in_block else None)
        map_member = in_block[-1] if in_block else person_member
        slug = f'day-{day:02d}'
        source = sources[name]
        data.append({
            'day': day,
            'region': next((clean(p['text']) for p in paragraphs[start:start + 8] if clean(p['text']) in ('Africa', 'Arabs', 'India', 'Latin America', 'Other Asia')), ''),
            'peopleName': name,
            'personImage': {'src': media_url(person_member, slug + '-person'), **source.get('person', {})},
            'statistics': stats,
            'generalInformation': general,
            'scripture': scripture,
            'prayerPoints': prayers,
            'mapImage': {'src': media_url(map_member, slug + '-map'), **source.get('map', {})},
        })
    index = []
    for entry in data:
        filename = f"day-{entry['day']:02d}.json"
        (DATA / filename).write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding='utf-8')
        index.append({
            'day': entry['day'],
            'region': entry['region'],
            'peopleName': entry['peopleName'],
            'file': f'data/{filename}',
        })
    (DATA / 'index.json').write_text(json.dumps({'regions': REGIONS, 'days': index}, ensure_ascii=False, indent=2), encoding='utf-8')
    legacy = OUT / 'prayers.json'
    if legacy.exists():
        legacy.unlink()
    print(f'Created {len(data)} entries and {len(list(ASSETS.iterdir()))} local image assets.')

if __name__ == '__main__':
    main()
