#!/usr/bin/env python3
"""Apply the Spanish booklet's verified statistics to every Spanish day file."""

import json
from pathlib import Path


DATA_DIR = Path("public/data/es")
STATS = {
    1: [("Población", "13,877,900 (PF solamente desde agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Fula"), ("Cristianos", "Menos de 0.1%"), ("Biblia-Porciones", "Sí; Nuevo Testamento: Sí")],
    2: [("Población", "741,000 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Garre, algunos hablan somalí"), ("Cristianos", "Menos de 0.01%"), ("Traducción bíblica", "Empezada")],
    3: [("Población", "16,288,200 en 16 países (PF solamente desde agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Somalí y árabe"), ("Cristianos", "Menos de 0.03%"), ("Biblia", "Completa y publicada por la Sociedad de la Biblia de Kenia en los 1970")],
    4: [("Población", "139,929,000 (PF solamente desde agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Árabe"), ("Cristianos", "0-0.1%")],
    5: [("Población", "34,350,000 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Árabe (varios dialectos)"), ("Cristianos", "Menos de 0.1%"), ("Biblia", "Disponible, pero la distribución es difícil")],
    6: [("Población", "36,947,700 esparcidos en más de 8 países (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Árabe argelino"), ("Cristianos", "Menos de 0.1%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: No")],
    7: [("Población", "407,000 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Árabe sudanés"), ("Cristianos", "0.00%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: No")],
    8: [("Población", "15,087,000 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Árabe sudanés"), ("Cristianos", "Menos de 0.05%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: No")],
    9: [("Población", "1,051,877,000 (en agosto 2025)"), ("Religión", "Islam"), ("Cristianos", "Número desconocido")],
    10: [("Población", "884,000 (en agosto 2025)"), ("Religión", "Hinduismo e Islam"), ("Idioma", "Urdu e hindi"), ("Cristianos", "0-0.1%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    11: [("Población", "48,000,000 (en agosto 2025)"), ("Religión", "Hinduismo"), ("Idioma", "Hindi, dialectos locales"), ("Cristianos", "0.04%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    12: [("Población", "17,000,000 (en agosto 2025)"), ("Religión", "Hinduismo"), ("Idioma", "Hindi"), ("Cristianos", "0.02%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    13: [("Población", "2,026,000 (en agosto 2025)"), ("Religión", "Hinduismo"), ("Idioma", "Telugu y Kannada"), ("Cristianos", "0.01%")],
    14: [("Población", "16,085,000 (en agosto 2025)"), ("Religión", "Hinduismo"), ("Idioma", "Telugu"), ("Cristianos", "0.01%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    15: [("Población", "18,279,000 (en agosto 2025)"), ("Religión", "Hinduismo"), ("Idioma", "Hindi"), ("Cristianos", "0.01%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    16: [("Población", "15,630,000 (en agosto 2025)"), ("Religión", "Hinduismo"), ("Idioma", "Hindi"), ("Cristianos", "0.01%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    17: [("Población", "36,204,000 (en agosto 2025)"), ("Religión", "Hinduismo"), ("Idioma", "Marathi"), ("Cristianos", "0.00%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    18: [("Población", "31,894,000 (en agosto 2025)"), ("Religión", "Hinduismo"), ("Idioma", "Hindi"), ("Cristianos", "0.01%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    19: [("Población", "489,000 (en agosto 2025)"), ("Religión", "Hinduismo"), ("Idioma", "Telugu"), ("Cristianos", "0.00%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    20: [("Población", "82,690,000 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Urdu"), ("Cristianos", "0.00%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    21: [("Población", "21,850,000 (en agosto 2025)"), ("Religión", "Hinduismo"), ("Idioma", "Hindi"), ("Cristianos", "0.01%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    22: [("Población", "57,595,000 (en agosto 2025)"), ("Religión", "Hinduismo"), ("Idioma", "Hindi"), ("Cristianos", "0-0.1%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    23: [("Población", "400 (en agosto 2025)"), ("Religión", "Étnica"), ("Idioma", "Matis"), ("Cristianos", "0.01%"), ("Biblia", "Traducción empezada")],
    24: [("Población", "3,182,054 (en agosto 2025)"), ("Religión", "Islam"), ("Cristianos", "0.01%")],
    25: [("Población", "252,000 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Wolio"), ("Cristianos", "0.01%"), ("Biblia", "Nuevo Testamento: No; Biblia completa: No")],
    26: [("Población", "2,588,000 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Luri (del norte)"), ("Cristianos", "0.01%"), ("Biblia", "Nuevo Testamento: Sí")],
    27: [("Población", "14,258,000 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Malay"), ("Cristianos", "0-0.1%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: Sí")],
    28: [("Población", "529,676 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Maldivo"), ("Cristianos", "0.01%"), ("Biblia", "Nuevo Testamento: Solamente Lucas y Hechos; Biblia completa: No")],
    29: [("Población", "356,300 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "5 locales"), ("Cristianos", "0.0%"), ("Biblia", "Nuevo Testamento: No; Biblia completa: No")],
    30: [("Población", "1,567,000 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Malayo Pattani"), ("Cristianos", "0.01%"), ("Biblia", "Nuevo Testamento: Sí; Biblia completa: No")],
    31: [("Población", "13,406,000 (en agosto 2025)"), ("Religión", "Islam"), ("Idioma", "Sylheti"), ("Cristianos", "Menos de 0.1%"), ("Biblia completa", "Sí"), ("La película de Jesús", "disponible en sylheti")],
}


for day, rows in STATS.items():
    path = DATA_DIR / f"day-{day:02d}.json"
    payload = json.loads(path.read_text())
    payload["statistics"] = [{"label": label, "value": value} for label, value in rows]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
