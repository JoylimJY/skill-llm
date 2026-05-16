import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "clinical_docs/discharge_letters",
    "clinical_docs/referrals",
    "clinical_docs/lab_reports",
    "admin/patient_admin",
    "admin/billing",
    "nlp_pipeline/input_staging",
    "nlp_pipeline/processed",
    "nlp_pipeline/models",
    "governance/audit_logs",
    "governance/policies",
    "it_support/logs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "clinical_docs/referrals/referral_template.txt": (
        "REFERRAL TEMPLATE\n"
        "Patient: [PATIENT_NAME]\n"
        "Referred to: Cardiology\n"
        "Priority: Urgent\n"
        "Reason: Chest pain, SOB\n"
    ),
    "clinical_docs/lab_reports/hba1c_ranges.csv": (
        "level,mmol_mol,interpretation\n"
        "normal,<42,Non-diabetic\n"
        "prediabetes,42-47,At risk\n"
        "diabetes,>=48,Diabetic\n"
    ),
    "admin/billing/invoice_q1_2026.txt": (
        "Invoice #4421\nDate: 01/04/2026\nAmount: £12,400\nService: NLP licences\n"
    ),
    "admin/patient_admin/registration_form_blank.txt": (
        "PATIENT REGISTRATION FORM\n"
        "NHS Number: ___________\n"
        "Full Name: ___________\n"
        "Date of Birth: ___________\n"
        "Address: ___________\n"
    ),
    "nlp_pipeline/models/model_config.json": (
        '{"model": "bert-base-uncased", "max_len": 512, "batch_size": 32}\n'
    ),
    "nlp_pipeline/processed/sample_output.json": (
        '{"doc_id": "anon_001", "entities": ["medication", "diagnosis"]}\n'
    ),
    "governance/policies/data_handling_policy_v3.txt": (
        "Policy: All patient data must be pseudonymised before AI processing.\n"
        "Review date: 31 March 2027\n"
        "Owner: Information Governance Team\n"
    ),
    "governance/audit_logs/access_log_2026-06.txt": (
        "2026-06-01 08:14:33 user=nlp_svc action=READ doc=disch_001\n"
        "2026-06-01 08:14:35 user=nlp_svc action=WRITE doc=anon_001\n"
    ),
    "it_support/logs/pipeline_error.log": (
        "[ERROR] 2026-06-03 02:11:07 NullPointerException in tokenizer\n"
        "[INFO]  2026-06-03 02:12:00 Service restarted\n"
    ),
    "nlp_pipeline/input_staging/readme_staging.txt": (
        "Files placed here are picked up by the ingestion daemon every 5 minutes.\n"
        "Files must be plain text (.txt). Max size 1 MB.\n"
    ),
    "admin/patient_admin/ward_list_redacted_example.txt": (
        "Ward 7B Census — REDACTED COPY\n"
        "Bed 1: [PATIENT_NAME], [DATE_OF_BIRTH], [NHS_NUMBER]\n"
        "Bed 2: [PATIENT_NAME], [DATE_OF_BIRTH], [NHS_NUMBER]\n"
    ),
}

for rel_path, content in distractors.items():
    (workspace / rel_path).write_text(content)

# ── THE MAIN INPUT DOCUMENT ──────────────────────────────────────────────────
# This is the messy, real-world discharge letter the agent must pseudonymise.
# Traps embedded:
#  1. Two clinician names (Dr. Amelia Thornton, Mr. Rajiv Kapoor) → must NOT be redacted
#  2. Patient name appears 3× (Mrs Dorothy Fielding, Fielding, Mrs Fielding) → same token each time
#  3. NHS number 485 777 3606 — valid Modulus 11 → [NHS_NUMBER]
#  4. A second "NHS-like" number 123 456 7890 — fails Mod11 — but still looks like NHS number context → still [NHS_NUMBER] per "when uncertain" rule
#  5. Date of birth clearly labelled → [DATE_OF_BIRTH]
#  6. Appointment date → must be PRESERVED (clinical date)
#  7. Procedure date → must be PRESERVED
#  8. NI number AB 12 34 56 C → [NI_NUMBER]
#  9. Postcode LS6 3PJ and WC2N 5DU → [POSTCODE] (two instances)
# 10. Phone numbers (UK mobile and UK landline) → [PHONE_NUMBER]
# 11. Email address → [EMAIL]
# 12. Hospital number RXH-3849201 → [HOSPITAL_NUMBER]
# 13. Address (house number + street) → [ADDRESS]
# 14. Age "71" inline → [AGE]
# 15. "St. James's University Hospital" → must NOT be redacted (institutional)
# 16. Second patient briefly referenced (Next of kin) → [PATIENT_NAME_2] if name given, but here it's just "husband" — so NO second patient token needed
# Note: Line numbers in the file matter for the Redaction Report.

discharge_letter = """\
St. James's University Hospital
Department of Cardiology
Beckett Street, Leeds LS9 7TF

26 June 2026

Dear Mrs Dorothy Fielding,

DOB: 12/08/1954   (age 71)
NHS Number: 485 777 3606
Previous NHS Ref: 123 456 7890
Hospital Number: RXH-3849201
NI Number: AB123456C

I am writing to summarise the outcome of Mrs Fielding's admission to the Coronary Care Unit at St. James's University Hospital following an episode of chest pain on 18 June 2026.

Mrs Fielding was admitted via the Emergency Department on 18 June 2026 and underwent coronary angiography on 21 June 2026 under the care of Mr. Rajiv Kapoor, Interventional Cardiologist. A drug-eluting stent was placed in the left anterior descending artery. She tolerated the procedure well.

Echocardiography performed on 22 June 2026 demonstrated an ejection fraction of 52%, with no significant valvular abnormality.

Current Medications on Discharge:
- Aspirin 75 mg once daily
- Ticagrelor 90 mg twice daily (continue for 12 months)
- Atorvastatin 80 mg at night
- Bisoprolol 2.5 mg once daily
- Ramipril 5 mg once daily

Please arrange follow-up in the Cardiology Outpatient Clinic in 6 weeks. The next appointment has been booked for 5 August 2026 at 10:30.

Home address: 47 Balmoral Crescent, Chapel Allerton, Leeds LS7 4NP
Mobile: 07821 334 991
Alternative tel: 0113 265 8847
Email: dorothy.fielding@btinternet.com

Emergency contact: Husband, Gerald (same address, tel as above).

For queries, please contact the Cardiology Secretariat:
Tel: 0113 206 5320  |  Email: cardio.secretary@leedsth.nhs.uk

Yours sincerely,

Dr. Amelia Thornton
Consultant Cardiologist
St. James's University Hospital
""".rstrip()

input_path = workspace / "clinical_docs/discharge_letters/discharge_letter_fielding.txt"
input_path.write_text(discharge_letter)

print("Workspace generated successfully.")
print(f"Input document: {input_path}")
print(f"Total files created: {len(distractors) + 1}")