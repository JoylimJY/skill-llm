#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# ============================================================
# Create the accounting assistant scripts in the workspace
# These simulate the proprietary tools referenced in SKILL.md
# ============================================================

# --- beleg-analyse.py ---
cat > "$WORKSPACE/beleg-analyse.py" << 'PYEOF'
#!/usr/bin/env python3
"""
Beleg-Analyse Tool - Analysiert PDF-Rechnungen und extrahiert Beträge.
Usage: python3 beleg-analyse.py <rechnung.pdf>
"""
import sys
import os
import json
import re

def analyse_beleg(filepath):
    """Analysiert eine Rechnung und gibt strukturierte Daten aus."""
    if not os.path.exists(filepath):
        print(f"FEHLER: Datei nicht gefunden: {filepath}", file=sys.stderr)
        sys.exit(1)

    # Read file content (handles both real PDFs and text stubs)
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
        # Try to decode as text, ignore errors for binary PDF parts
        content = raw.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"FEHLER beim Lesen: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract key fields via pattern matching
    result = {
        "datei": os.path.basename(filepath),
        "analysiert": True,
        "felder": {}
    }

    # Rechnung Nr.
    m = re.search(r'Rechnung Nr\.?\s*([A-Za-z0-9\-]+)', content)
    if m:
        result["felder"]["rechnungsnummer"] = m.group(1)

    # Datum
    m = re.search(r'Datum:\s*(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})', content)
    if m:
        result["felder"]["datum"] = m.group(1)

    # Nettobetrag
    m = re.search(r'Nettobetrag:\s*([\d.,]+)\s*EUR', content)
    if m:
        netto = float(m.group(1).replace(',', '.'))
        result["felder"]["netto"] = netto
        result["felder"]["ust_19"] = round(netto * 0.19, 2)
        result["felder"]["brutto"] = round(netto * 1.19, 2)

    # Brutto fallback
    if "brutto" not in result["felder"]:
        m = re.search(r'Bruttobetrag:\s*([\d.,]+)\s*EUR', content)
        if m:
            brutto = float(m.group(1).replace(',', '.'))
            result["felder"]["brutto"] = brutto
            result["felder"]["netto"] = round(brutto / 1.19, 2)
            result["felder"]["ust_19"] = round(brutto - brutto / 1.19, 2)

    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python3 beleg-analyse.py <rechnung.pdf>", file=sys.stderr)
        sys.exit(1)
    analyse_beleg(sys.argv[1])
PYEOF

# --- eur-erstellung.py ---
cat > "$WORKSPACE/eur-erstellung.py" << 'PYEOF'
#!/usr/bin/env python3
"""
EÜR-Erstellung Tool - Erstellt Einnahmen-Überschuss-Rechnung.
Usage: python3 eur-erstellung.py > eur-2024.md

Reads buchungen.json from the current directory.
"""
import json
import sys
import os
from datetime import datetime

def load_buchungen(filepath="buchungen.json"):
    if not os.path.exists(filepath):
        print(f"FEHLER: {filepath} nicht gefunden.", file=sys.stderr)
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def berechne_eur(buchungen_data):
    """Berechnet EÜR-Positionen mit USt 19%."""
    einnahmen = []
    ausgaben = []

    for b in buchungen_data.get("buchungen", []):
        brutto = float(b["betrag_brutto"])
        netto = round(brutto / 1.19, 2)
        ust = round(brutto - netto, 2)
        eintrag = {
            "datum": b["datum"],
            "beschreibung": b["beschreibung"],
            "brutto": brutto,
            "netto": netto,
            "ust": ust
        }
        if b["art"] == "Einnahme":
            einnahmen.append(eintrag)
        else:
            ausgaben.append(eintrag)

    total_einnahmen_netto = round(sum(e["netto"] for e in einnahmen), 2)
    total_ausgaben_netto = round(sum(a["netto"] for a in ausgaben), 2)
    gewinn = round(total_einnahmen_netto - total_ausgaben_netto, 2)
    ust_einnahmen = round(sum(e["ust"] for e in einnahmen), 2)
    ust_ausgaben = round(sum(a["ust"] for a in ausgaben), 2)
    ust_zahllast = round(ust_einnahmen - ust_ausgaben, 2)

    return {
        "jahr": buchungen_data.get("jahr", datetime.now().year),
        "einnahmen": einnahmen,
        "ausgaben": ausgaben,
        "summen": {
            "einnahmen_netto": total_einnahmen_netto,
            "ausgaben_netto": total_ausgaben_netto,
            "gewinn": gewinn,
            "ust_einnahmen": ust_einnahmen,
            "ust_ausgaben": ust_ausgaben,
            "ust_zahllast": ust_zahllast
        }
    }

def render_markdown(eur):
    """Rendert EÜR als Markdown (Anlage EÜR Format)."""
    jahr = eur["jahr"]
    s = eur["summen"]

    lines = []
    lines.append(f"# Einnahmen-Überschuss-Rechnung {jahr}")
    lines.append(f"## Anlage EÜR | Steuerjahr {jahr}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📥 Betriebseinnahmen")
    lines.append("")
    lines.append("| Datum | Beschreibung | Netto (EUR) | USt 19% (EUR) | Brutto (EUR) |")
    lines.append("|-------|-------------|-------------|---------------|-------------|")
    for e in eur["einnahmen"]:
        lines.append(f"| {e['datum']} | {e['beschreibung']} | {e['netto']:.2f} | {e['ust']:.2f} | {e['brutto']:.2f} |")
    lines.append(f"| **Gesamt** | | **{s['einnahmen_netto']:.2f}** | **{s['ust_einnahmen']:.2f}** | |")
    lines.append("")
    lines.append("## 📤 Betriebsausgaben")
    lines.append("")
    lines.append("| Datum | Beschreibung | Netto (EUR) | USt 19% (EUR) | Brutto (EUR) |")
    lines.append("|-------|-------------|-------------|---------------|-------------|")
    for a in eur["ausgaben"]:
        lines.append(f"| {a['datum']} | {a['beschreibung']} | {a['netto']:.2f} | {a['ust']:.2f} | {a['brutto']:.2f} |")
    lines.append(f"| **Gesamt** | | **{s['ausgaben_netto']:.2f}** | **{s['ust_ausgaben']:.2f}** | |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📊 Zusammenfassung")
    lines.append("")
    lines.append(f"| Position | Betrag (EUR) |")
    lines.append(f"|----------|-------------|")
    lines.append(f"| Betriebseinnahmen (netto) | {s['einnahmen_netto']:.2f} |")
    lines.append(f"| Betriebsausgaben (netto) | {s['ausgaben_netto']:.2f} |")
    lines.append(f"| **Gewinn (§ 4 Abs. 3 EStG)** | **{s['gewinn']:.2f}** |")
    lines.append(f"| Umsatzsteuer Einnahmen | {s['ust_einnahmen']:.2f} |")
    lines.append(f"| Umsatzsteuer Ausgaben | {s['ust_ausgaben']:.2f} |")
    lines.append(f"| **USt-Zahllast** | **{s['ust_zahllast']:.2f}** |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Erstellt mit Accounting Assistant v1.0.0 | SKR03 Kontenplan*")

    return "\n".join(lines)

if __name__ == "__main__":
    data = load_buchungen()
    eur = berechne_eur(data)
    print(render_markdown(eur))
PYEOF

# --- datev-export.py ---
cat > "$WORKSPACE/datev-export.py" << 'PYEOF'
#!/usr/bin/env python3
"""
DATEV-Export Tool - Exportiert Buchungen im DATEV CSV-Format mit SKR03 Kontenplan.
Usage: python3 datev-export.py buchungen.json export.csv
"""
import json
import csv
import sys
import os
from datetime import datetime

# SKR03 Kontenplan (Standardkontenrahmen 03)
SKR03 = {
    "Einnahme": {
        "konto": "8400",          # Erlöse aus Lieferungen und Leistungen (19% USt)
        "gegenkonto": "1200",     # Bank
        "ust_konto": "1776",      # Umsatzsteuer 19%
        "steuercode": "9",        # USt 19%
    },
    "Ausgabe": {
        "konto": "1200",          # Bank
        "gegenkonto": "4980",     # Sonstige betriebliche Aufwendungen
        "vst_konto": "1576",      # Vorsteuer 19%
        "steuercode": "9",        # VSt 19%
    }
}

DATEV_HEADER = [
    "Umsatz (ohne Soll/Haben-Kz)",
    "Soll/Haben-Kennzeichen",
    "WKZ Umsatz",
    "Kurs",
    "Basis-Umsatz",
    "WKZ Basis-Umsatz",
    "Konto",
    "Gegenkonto (ohne BU-Schlüssel)",
    "BU-Schlüssel",
    "Belegdatum",
    "Belegfeld 1",
    "Belegfeld 2",
    "Skonto",
    "Buchungstext",
]

def format_datev_date(datum_str):
    """Konvertiert YYYY-MM-DD zu DDMM (DATEV-Format)."""
    try:
        d = datetime.strptime(datum_str, "%Y-%m-%d")
        return d.strftime("%d%m")
    except:
        return datum_str

def export_datev(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"FEHLER: {input_file} nicht gefunden.", file=sys.stderr)
        sys.exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = []
    for i, b in enumerate(data.get("buchungen", []), start=1):
        brutto = float(b["betrag_brutto"])
        netto = round(brutto / 1.19, 2)
        ust = round(brutto - netto, 2)
        art = b["art"]
        skr = SKR03[art]

        if art == "Einnahme":
            soll_haben = "H"  # Haben = Einnahme auf Erlöskonto
            konto = skr["konto"]          # 8400
            gegenkonto = skr["gegenkonto"]  # 1200
        else:
            soll_haben = "S"  # Soll = Ausgabe
            konto = skr["gegenkonto"]       # 4980
            gegenkonto = skr["konto"]       # 1200

        row = {
            "Umsatz (ohne Soll/Haben-Kz)": f"{netto:.2f}",
            "Soll/Haben-Kennzeichen": soll_haben,
            "WKZ Umsatz": "EUR",
            "Kurs": "",
            "Basis-Umsatz": "",
            "WKZ Basis-Umsatz": "",
            "Konto": konto,
            "Gegenkonto (ohne BU-Schlüssel)": gegenkonto,
            "BU-Schlüssel": skr["steuercode"],
            "Belegdatum": format_datev_date(b["datum"]),
            "Belegfeld 1": f"BLG{i:04d}",
            "Belegfeld 2": str(data.get("jahr", "")),
            "Skonto": "",
            "Buchungstext": b["beschreibung"][:30],
        }
        rows.append(row)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=DATEV_HEADER, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)

    print(f"DATEV-Export abgeschlossen: {output_file} ({len(rows)} Buchungen)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Verwendung: python3 datev-export.py buchungen.json export.csv", file=sys.stderr)
        sys.exit(1)
    export_datev(sys.argv[1], sys.argv[2])
PYEOF

chmod +x "$WORKSPACE/beleg-analyse.py"
chmod +x "$WORKSPACE/eur-erstellung.py"
chmod +x "$WORKSPACE/datev-export.py"

echo "Accounting assistant scripts installed and made executable."