#!/usr/bin/env python3
"""
Generate the sandbox workspace for the accounting-assistant task.
Creates a realistic messy freelancer bookkeeping workspace.
"""

import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
WORKSPACE.mkdir(parents=True, exist_ok=True)

# --- Distractor directory structure ---
dirs = [
    "rechnungen/2023",
    "rechnungen/2024/Q1",
    "rechnungen/2024/Q2",
    "steuern/2022",
    "steuern/2023",
    "bank/kontoauszuege",
    "vertraege",
    "buchhaltung/archiv",
    "buchhaltung/vorlagen",
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
(WORKSPACE / "rechnungen/2023/rechnung_2023_001.txt").write_text(
    "Rechnung Nr. 2023-001\nDatum: 15.03.2023\nBetrag: 1190.00 EUR (inkl. 19% USt)"
)
(WORKSPACE / "rechnungen/2023/rechnung_2023_002.txt").write_text(
    "Rechnung Nr. 2023-002\nDatum: 22.07.2023\nBetrag: 595.00 EUR (inkl. 19% USt)"
)
(WORKSPACE / "rechnungen/2024/Q1/rechnung_2024_001.txt").write_text(
    "Rechnung Nr. 2024-001\nDatum: 10.01.2024\nBetrag: 2380.00 EUR (inkl. 19% USt)"
)
(WORKSPACE / "rechnungen/2024/Q2/rechnung_2024_002.txt").write_text(
    "Rechnung Nr. 2024-002\nDatum: 15.04.2024\nBetrag: 714.00 EUR (inkl. 19% USt)"
)
(WORKSPACE / "steuern/2022/eur_2022_draft.txt").write_text(
    "EÜR 2022 ENTWURF\nEinnahmen: 45000\nAusgaben: 12000\nGewinn: 33000"
)
(WORKSPACE / "steuern/2023/umsatzsteuer_2023.txt").write_text(
    "USt-Voranmeldung 2023\nQ1: 1200 EUR\nQ2: 980 EUR\nQ3: 1450 EUR\nQ4: 1100 EUR"
)
(WORKSPACE / "bank/kontoauszuege/januar_2024.csv").write_text(
    "Datum,Empfaenger,Betrag\n2024-01-05,Kunde GmbH,2380.00\n2024-01-12,Miete Buero,-800.00\n2024-01-20,Telekom,-59.50"
)
(WORKSPACE / "bank/kontoauszuege/februar_2024.csv").write_text(
    "Datum,Empfaenger,Betrag\n2024-02-03,Mustermann AG,1190.00\n2024-02-14,Software Lizenz,-238.00"
)
(WORKSPACE / "vertraege/freelance_vertrag_2024.txt").write_text(
    "Freiberuflicher Dienstleistungsvertrag\nAuftraggeber: Muster GmbH\nAuftragnehmer: Max Mustermann\nHonorar: 120 EUR/Stunde"
)
(WORKSPACE / "buchhaltung/archiv/buchungen_2023.json").write_text(json.dumps({
    "jahr": 2023,
    "buchungen": [
        {"datum": "2023-03-15", "art": "Einnahme", "beschreibung": "Beratung Kunde A", "betrag_brutto": 1190.00},
        {"datum": "2023-07-22", "art": "Ausgabe", "beschreibung": "Bueromaterial", "betrag_brutto": 119.00},
    ]
}, indent=2))
(WORKSPACE / "buchhaltung/vorlagen/buchungsvorlage.txt").write_text(
    "Buchungsvorlage:\nDatum | Art | Beschreibung | Betrag (Brutto)\n"
    "YYYY-MM-DD | Einnahme/Ausgabe | Beschreibung | 0.00"
)
(WORKSPACE / "tmp/notizen.txt").write_text(
    "TODO: Buchungen 2024 nachtragen\nSteuerberater Termin: 15.03.2025\nBelege scannen nicht vergessen!"
)

# --- The ACTUAL input file the agent must use ---
buchungen = {
    "jahr": 2024,
    "buchungen": [
        {
            "datum": "2024-01-10",
            "art": "Einnahme",
            "beschreibung": "Webentwicklung Projekt Alpha",
            "betrag_brutto": 2380.00
        },
        {
            "datum": "2024-02-03",
            "art": "Einnahme",
            "beschreibung": "Beratung Mustermann AG",
            "betrag_brutto": 1190.00
        },
        {
            "datum": "2024-02-14",
            "art": "Ausgabe",
            "beschreibung": "Software Lizenz Adobe",
            "betrag_brutto": 238.00
        },
        {
            "datum": "2024-03-05",
            "art": "Einnahme",
            "beschreibung": "SEO Optimierung Kunde B",
            "betrag_brutto": 595.00
        },
        {
            "datum": "2024-03-18",
            "art": "Ausgabe",
            "beschreibung": "Buerobedarf Staples",
            "betrag_brutto": 59.50
        },
        {
            "datum": "2024-04-15",
            "art": "Einnahme",
            "beschreibung": "Consulting Projekt Beta",
            "betrag_brutto": 3570.00
        },
        {
            "datum": "2024-04-22",
            "art": "Ausgabe",
            "beschreibung": "Fortbildung Online-Kurs",
            "betrag_brutto": 476.00
        },
        {
            "datum": "2024-05-08",
            "art": "Ausgabe",
            "beschreibung": "Telefon und Internet",
            "betrag_brutto": 119.00
        }
    ]
}

(WORKSPACE / "buchungen.json").write_text(json.dumps(buchungen, indent=2, ensure_ascii=False))

# --- Create a dummy PDF file for beleg-analyse.py ---
# Using fpdf2 to create a real (minimal) PDF
try:
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, txt="Rechnung Nr. 2024-005", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(200, 10, txt="Datum: 2024-06-01", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(200, 10, txt="Leistung: Webdesign Paket Premium", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(200, 10, txt="Nettobetrag: 1000.00 EUR", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(200, 10, txt="USt 19%: 190.00 EUR", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(200, 10, txt="Bruttobetrag: 1190.00 EUR", new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(WORKSPACE / "rechnung.pdf"))
    print("PDF created with fpdf2")
except Exception as e:
    # Fallback: write a minimal valid-looking PDF text stub
    print(f"fpdf2 not available: {e}, writing text stub")
    (WORKSPACE / "rechnung.pdf").write_bytes(
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        b"%%EOF\nRechnung Nr. 2024-005\nDatum: 2024-06-01\n"
        b"Nettobetrag: 1000.00 EUR\nUSt 19%: 190.00 EUR\nBruttobetrag: 1190.00 EUR\n"
    )

print("Workspace initialized successfully.")
print(f"Files created in: {WORKSPACE}")