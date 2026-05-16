import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create distractor directory structure
dirs = [
    "crm_exports/archive/2025",
    "crm_exports/archive/2024",
    "crm_exports/raw",
    "crm_exports/processed",
    "scripts",
    "templates/ics",
    "templates/email",
    "outreach/campaigns",
    "outreach/responses",
    "config",
    "logs",
    "reports/q1",
    "reports/q2",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
(workspace / "crm_exports/archive/2025/old_contacts.csv").write_text(
    "Company,Contact,Email\nBosch GmbH,Hans Becker,becker@bosch.de\nFesto AG,Lena Vogel,vogel@festo.de\n"
)
(workspace / "crm_exports/archive/2024/q4_deals.json").write_text(
    json.dumps({"deals": [{"company": "Trumpf", "value": 80000, "status": "closed"}]}, indent=2)
)
(workspace / "crm_exports/processed/validated_leads.txt").write_text(
    "Lead: Krones AG | Score: 87 | Region: Bayern\nLead: Voith GmbH | Score: 72 | Region: BW\n"
)
(workspace / "templates/email/followup_template.txt").write_text(
    "Subject: Follow-up on our recent meeting\nDear {name},\nThank you for your time...\n"
)
(workspace / "templates/ics/legacy_format.txt").write_text(
    "BEGIN:VCALENDAR\nVERSION:2.0\n# Old format — do not use\nEND:VCALENDAR\n"
)
(workspace / "outreach/campaigns/spring_2026.txt").write_text(
    "Target segment: Automotive Tier-1\nGoal: 15 demos in April\nOwner: sales@visales.io\n"
)
(workspace / "outreach/responses/response_log.csv").write_text(
    "Date,Company,Response\n2026-03-15,Siemens,Positive\n2026-03-20,Schaeffler,Follow-up needed\n"
)
(workspace / "config/crm_settings.json").write_text(
    json.dumps({"default_alarm": 15, "default_duration": 30, "lang": "de"}, indent=2)
)
(workspace / "logs/activity_2026-03.log").write_text(
    "[INFO] 2026-03-10 Demo presented to Siemens\n[INFO] 2026-03-14 Proposal sent to Schaeffler\n[INFO] 2026-03-22 Budget call with Endress+Hauser\n"
)
(workspace / "reports/q1/pipeline_summary.txt").write_text(
    "Q1 2026 Pipeline\nTotal deals: 12\nWeighted value: €340,000\nAvg deal size: €28,300\n"
)
(workspace / "reports/q2/forecast.txt").write_text(
    "Q2 Forecast: 5 expected closes\nTop deal: Endress+Hauser €60k\n"
)
(workspace / "crm_exports/raw/miscellaneous_notes.txt").write_text(
    "Random notes from sales team kickoff.\nDo not use for scheduling.\n"
)

# --- THE ACTUAL PROBLEM FILE ---
# Three customers with messy, freeform, partially structured CRM data
crm_raw = """\
=== CRM FOLLOW-UP BATCH — APRIL 2026 ===
Exported by: M. Fischer <fischer@visales.io>
Export date: 2026-03-28
Note: Urgency flag set for all three. Please get calendar invites out ASAP.

--- CUSTOMER 1 ---
Firma: Schaeffler Technologies AG & Co. KG
Kontakt: Dipl.-Ing. Thomas Hartmann
Telefon: +49 9132 82-0
E-Mail: t.hartmann@schaeffler.com
Termin: 17. April 2026, 09:30 Uhr
Dauer: 45 Minuten
Alarm: 20 Minuten vorher
Thema: Predictive Maintenance Plattform – Angebotsverfolgung
Priorität: HOCH
Letzte Interaktion: 2026-03-14 — Angebot über 48.500 € verschickt
Deal-Phase: Verhandlung
Budget: 48.500 €
Nächster Schritt: Entscheider-Runde einberufen und ROI-Rechnung präsentieren
Notizen: Hartmann braucht interne Freigabe vom CFO. Entscheidung bis Ende April erwartet.

--- CUSTOMER 2 ---
Company: Endress+Hauser Messtechnik GmbH
Contact: Sandra Bühler, Head of Digital Operations
Phone: +41 61 715 81 00
Email: sandra.buehler@endress.com
Appointment: April 22, 2026 at 14:00
Duration: 30 min
Topic: IIoT Dashboard Pilot — Contract Review
Priority: high
Last contact: 22.03.2026 — Pilot scope agreed verbally
Deal stage: Closing
Budget: €62,000
Next step: Send final contract draft by April 18
Notes: Swiss entity — check VAT treatment. Legal sign-off needed from both sides.

--- CUSTOMER 3 ---
Firma: Voith GmbH & Co. KGaA
Ansprechpartner: Dr.-Ing. Petra Krause
Tel: +49 7321 37-0
Mail: p.krause@voith.com
Datum: 2026-04-29
Uhrzeit: 11:00
Thema: Digitalisierungsstrategie 2027 – Erstgespräch
Priorität: mittel
Letzte Interaktion: 2026-03-05 — Erstkontakt via LinkedIn
Deal-Phase: Nurture
Nächster Schritt: Bedarfsanalyse durchführen und Referenzprojekte vorstellen
Notizen: Krause evaluiert mehrere Anbieter. Langfristiges Potenzial ~150k. Kein Budget freigegeben.
"""

(workspace / "crm_exports/raw/april_followups.txt").write_text(crm_raw, encoding="utf-8")

# --- The generate_ics.py script (the actual skill script) ---
# This is the proprietary script the agent must call
generate_ics_script = r'''#!/usr/bin/env python3
"""
viSales ICS CRM Reminder Generator
Generates professional ICS calendar files with CRM data.
"""

import argparse
import sys
import os
import re
import uuid
from datetime import datetime, timedelta
import pytz

def slugify(text):
    """Replace special characters and spaces with hyphens."""
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def format_ics_text(text):
    """Fold long lines per RFC 5545."""
    result = []
    for line in text.splitlines():
        line = line.replace('\n', '\\n')
        if len(line.encode('utf-8')) <= 75:
            result.append(line)
        else:
            encoded = line.encode('utf-8')
            chunks = []
            while len(encoded) > 75:
                chunk = encoded[:75]
                chunks.append(chunk.decode('utf-8', errors='replace'))
                encoded = encoded[75:]
            if encoded:
                chunks.append(encoded.decode('utf-8', errors='replace'))
            result.append(chunks[0])
            for chunk in chunks[1:]:
                result.append(' ' + chunk)
    return '\r\n'.join(result)

def build_description(firma, ansprechpartner, telefon, email, thema, prioritaet,
                       letzte_interaktion, deal_phase, budget, naechster_schritt, notizen):
    prio_map = {'hoch': '⚡ HOCH', 'mittel': '🔵 MITTEL', 'niedrig': '🟢 NIEDRIG'}
    prio_display = prio_map.get(prioritaet.lower() if prioritaet else 'mittel', '🔵 MITTEL')

    lines = ['═══ viSales CRM Reminder ═══', '']
    lines += ['📋 KUNDE']
    lines += [f'Firma: {firma}']
    if ansprechpartner:
        lines += [f'Ansprechpartner: {ansprechpartner}']
    if telefon:
        lines += [f'Tel: {telefon}']
    if email:
        lines += [f'Mail: {email}']
    lines += ['']
    lines += ['🎯 ANLASS']
    if thema:
        lines += [f'Thema: {thema}']
    lines += [f'Priorität: {prio_display}']
    lines += ['']
    lines += ['📊 DEAL STATUS']
    if deal_phase:
        lines += [f'Phase: {deal_phase}']
    if budget:
        lines += [f'Budget: {budget}']
    if letzte_interaktion:
        lines += [f'Letzte Interaktion: {letzte_interaktion}']
    lines += ['']
    if naechster_schritt:
        lines += ['➡️ NÄCHSTER SCHRITT']
        lines += [naechster_schritt]
        lines += ['']
    if notizen:
        lines += ['📝 NOTIZEN']
        lines += [notizen]
        lines += ['']
    lines += ['───']
    lines += ['Generated by viSales CRM Reminder']

    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='viSales ICS CRM Reminder Generator')
    parser.add_argument('--firma', required=True, help='Company name')
    parser.add_argument('--datum', required=True, help='Date (YYYY-MM-DD)')
    parser.add_argument('--uhrzeit', required=True, help='Time (HH:MM)')
    parser.add_argument('--ansprechpartner', default='', help='Contact person')
    parser.add_argument('--telefon', default='', help='Phone number')
    parser.add_argument('--email', default='', help='Email address')
    parser.add_argument('--thema', default='', help='Topic/Reason')
    parser.add_argument('--prioritaet', default='mittel', help='Priority (hoch/mittel/niedrig)')
    parser.add_argument('--letzte-interaktion', default='', help='Last interaction')
    parser.add_argument('--deal-phase', default='', help='Deal phase')
    parser.add_argument('--budget', default='', help='Budget')
    parser.add_argument('--naechster-schritt', default='', help='Next step')
    parser.add_argument('--notizen', default='', help='Notes')
    parser.add_argument('--dauer', type=int, default=30, help='Duration in minutes')
    parser.add_argument('--alarm', type=int, default=15, help='Alarm in minutes before')
    parser.add_argument('--output', default='.', help='Output directory')

    args = parser.parse_args()

    # Parse datetime
    try:
        dt_str = f"{args.datum} {args.uhrzeit}"
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
    except ValueError as e:
        print(f"Error parsing date/time: {e}", file=sys.stderr)
        sys.exit(1)

    # Build description
    description = build_description(
        firma=args.firma,
        ansprechpartner=args.ansprechpartner,
        telefon=args.telefon,
        email=args.email,
        thema=args.thema,
        prioritaet=args.prioritaet,
        letzte_interaktion=args.letzte_interaktion,
        deal_phase=args.deal_phase,
        budget=args.budget,
        naechster_schritt=args.naechster_schritt,
        notizen=args.notizen
    )

    # Build ICS content
    uid = str(uuid.uuid4())
    dtstart = dt.strftime('%Y%m%dT%H%M%S')
    dtend = (dt + timedelta(minutes=args.dauer)).strftime('%Y%m%dT%H%M%S')
    dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

    summary = f"📞 {args.firma}"
    if args.thema:
        summary += f" — {args.thema}"

    # Escape description for ICS (commas, semicolons, newlines)
    ics_description = description.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')

    ics_lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//viSales CRM Reminder//DE',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'BEGIN:VEVENT',
        f'UID:{uid}',
        f'DTSTAMP:{dtstamp}',
        f'DTSTART:{dtstart}',
        f'DTEND:{dtend}',
        f'SUMMARY:{summary}',
        f'DESCRIPTION:{ics_description}',
        'BEGIN:VALARM',
        'TRIGGER:-PT' + str(args.alarm) + 'M',
        'ACTION:DISPLAY',
        f'DESCRIPTION:Reminder: {args.firma}',
        'END:VALARM',
        'END:VEVENT',
        'END:VCALENDAR',
    ]

    ics_content = '\r\n'.join(ics_lines) + '\r\n'

    # Determine filename
    slug = slugify(args.firma)
    filename = f"{args.datum}_{slug}_Reminder.ics"

    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    output_path = os.path.join(args.output, filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ics_content)

    print(f"✅ Created: {output_path}")
    return output_path

if __name__ == '__main__':
    main()
'''

(workspace / "scripts" / "generate_ics.py").write_text(generate_ics_script, encoding="utf-8")

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")