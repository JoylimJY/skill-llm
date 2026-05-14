import os
import random

random.seed(42)

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "workspace/patient_portal/incoming",
    "workspace/patient_portal/processed",
    "workspace/patient_portal/archive/2023",
    "workspace/patient_portal/archive/2024",
    "workspace/patient_portal/config",
    "workspace/patient_portal/templates",
    "workspace/patient_portal/logs",
    "workspace/admin/staff_notes",
    "workspace/admin/system",
    "workspace/tools/parsers",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "workspace/patient_portal/templates/adult_template.txt": (
        "Dear Patient,\nThank you for registering with our portal.\n"
        "Your results will be available within 5 working days.\n"
    ),
    "workspace/patient_portal/templates/carer_template.txt": (
        "Dear Carer,\nPlease ensure you have appropriate consent forms signed.\n"
        "Contact the ward sister for further information.\n"
    ),
    "workspace/patient_portal/archive/2023/processed_001.json": (
        '{"patient_id":"P001","status":"archived","year":2023}\n'
    ),
    "workspace/patient_portal/archive/2024/processed_099.json": (
        '{"patient_id":"P099","status":"archived","year":2024}\n'
    ),
    "workspace/patient_portal/logs/portal_access.log": (
        "2024-11-01 09:14:22 INFO  Patient P201 accessed portal\n"
        "2024-11-01 09:22:05 INFO  Patient P202 accessed portal\n"
        "2024-11-02 11:05:43 WARN  Session timeout P201\n"
    ),
    "workspace/admin/staff_notes/ward_round_notes.txt": (
        "Ward round 2024-11-05:\n"
        "- Bed 4: patient stable, awaiting cardiology review\n"
        "- Bed 7: discharge planned for Friday\n"
        "- Bed 12: chest X-ray pending\n"
    ),
    "workspace/admin/system/db_config.ini": (
        "[database]\nhost=localhost\nport=5432\nname=portal_db\nuser=portaladmin\n"
    ),
    "workspace/tools/parsers/pdf_extractor.py": (
        "# PDF text extraction utility\n"
        "import re\n\n"
        "def extract_text(path):\n"
        "    raise NotImplementedError('PDF extraction not configured')\n"
    ),
    "workspace/tools/parsers/hl7_parser.py": (
        "# HL7 message parser stub\n"
        "def parse_hl7(msg):\n"
        "    segments = msg.split('\\r')\n"
        "    return {'segments': segments}\n"
    ),
    "workspace/patient_portal/processed/sample_output_old.txt": (
        "Patient explanation (legacy format):\n"
        "Your blood test showed normal results.\n"
        "Please see your GP if you have concerns.\n"
    ),
    "workspace/patient_portal/config/portal_settings.json": (
        '{\n'
        '  "portal_name": "HealthConnect Patient Portal",\n'
        '  "default_language": "en",\n'
        '  "max_upload_size_mb": 10,\n'
        '  "supported_formats": ["pdf","jpg","png","docx","txt"]\n'
        '}\n'
    ),
    "workspace/admin/staff_notes/handover_2024_11.txt": (
        "Handover notes November 2024:\n"
        "Reminder: all outgoing letters must be reviewed by senior clinician.\n"
        "New e-referral system goes live 2024-12-01.\n"
    ),
}

for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# ── personalisation config (the agent must read and honour this) ─────────────
personalisation_cfg = """\
# Patient Personalisation Preferences
# These preferences must be applied when generating the simplified explanation.

patient_id: P247
reading_level: Teen
tone: Reassuring
length: Brief
language: Spanish
"""

with open("workspace/patient_portal/config/patient_P247_preferences.cfg", "w") as f:
    f.write(personalisation_cfg)

# ── the clinical letter (messy, realistic, contains deliberate ambiguity) ────
clinical_letter = """\
NHS TRUST — OUTPATIENT CLINIC LETTER
Confidential

Date: 14 November 2024
Patient: Jamie Whitmore  DOB: 03/06/2009  NHS No: 487 362 1095
Referring GP: Dr. K. Patel, Ashfield Surgery

Dear Dr. Patel,

Thank you for referring Jamie, a 15-year-old, to our Paediatric Gastroenterology outpatient clinic. 
I reviewed Jamie on 12 November 2024 in the presence of their parent/guardian.

PRESENTING COMPLAINT:
Jamie has experienced intermittent abdominal pain (predominantly left lower quadrant), 
loose stools (3–4 per day), occasional blood-streaked stools, and a 3 kg weight loss 
over the preceding 4 months. Symptoms have been present for approximately 6 months 
in total, with a 2-month period of relative improvement followed by recent deterioration.

EXAMINATION:
On examination, Jamie appeared comfortable at rest. Abdomen was soft with mild 
left iliac fossa tenderness on deep palpation. No guarding or rigidity. No palpable 
organomegaly. Perianal region was normal. Weight 52 kg, height 168 cm (both tracking 
below the 25th centile for age, though prior growth data was not available for comparison).

INVESTIGATIONS REQUESTED:
The following investigations have been arranged:
- Full blood count (FBC)
- C-reactive protein (CRP)
- Erythrocyte sedimentation rate (ESR)
- Coeliac antibody screen (anti-tTG IgA)
- Faecal calprotectin
- Stool microscopy, culture and sensitivity (MC&S)

Results are pending at the time of dictation and were not available for this letter.

IMPRESSION:
The clinical picture is consistent with several possible diagnoses. It has not been 
possible at this stage to determine a single cause. Possibilities being considered 
include, but are not limited to, inflammatory bowel conditions and infective or 
functional aetiologies. No diagnosis has been confirmed.

PLAN:
1. Await investigation results.
2. Jamie to be reviewed in clinic in 6 weeks or sooner if symptoms worsen significantly.
3. If Jamie experiences severe abdominal pain, high fever, or significantly increased 
   rectal bleeding, parent/guardian to attend the nearest emergency department.

I will write again once investigations are available.

Yours sincerely,

Dr. F. Okonkwo MBBS MRCPCH
Consultant Paediatric Gastroenterologist
Paediatric Gastroenterology Department
NHS Trust Hospital
"""

with open("workspace/patient_portal/incoming/letter_P247_20241114.txt", "w") as f:
    f.write(clinical_letter)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("workspace"):
    for file in files:
        print(f"  {os.path.join(root, file)}")