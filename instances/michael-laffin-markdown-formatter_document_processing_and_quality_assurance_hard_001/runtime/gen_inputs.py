import os
import random
import string

random.seed(42)

WORKSPACE = "/workspace"

# ── directory structure (distractors + real inputs) ──────────────────────────
dirs = [
    "pharma_docs/clinical_trials",
    "pharma_docs/regulatory_submissions",
    "pharma_docs/lab_protocols",
    "pharma_docs/safety_reports",
    "pharma_docs/meeting_notes",
    "internal/hr",
    "internal/finance",
    "internal/it_policies",
    "archive/2021",
    "archive/2022",
    "templates",
    "scripts_misc",
    "raw_docs",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files (non-markdown or already-good markdown not to be processed) ──
distractor_txts = [
    ("internal/hr/onboarding_guide.txt", "Onboarding guide - plain text version.\nWelcome to the team!\n"),
    ("internal/finance/budget_q3.csv", "department,amount\nRD,150000\nClinical,300000\n"),
    ("internal/it_policies/vpn_setup.rst", "VPN Setup\n=========\n\nFollow these steps.\n"),
    ("archive/2021/old_protocol.bak", "Archived protocol v1 - do not use.\n"),
    ("archive/2022/trial_results_summary.json", '{"trial": "XR-2022", "result": "success"}\n'),
    ("templates/cover_letter_template.docx.txt", "Cover letter placeholder.\n"),
    ("scripts_misc/convert.sh", "#!/bin/bash\necho converting...\n"),
    ("scripts_misc/validate.py", "#!/usr/bin/env python3\nprint('validator stub')\n"),
    ("internal/hr/leave_policy.txt", "Leave policy details here.\n"),
    ("internal/it_policies/password_rules.txt", "Passwords must be 12+ chars.\n"),
    ("archive/2022/meeting_minutes_old.txt", "Minutes from 2022-03-14 meeting.\n"),
]
for rel_path, content in distractor_txts:
    full = os.path.join(WORKSPACE, rel_path)
    with open(full, "w") as f:
        f.write(content)

# ── messy markdown files that MUST be processed ──────────────────────────────

messy_md_files = {}

# File 1: clinical_trial_protocol.md  (in pharma_docs/clinical_trials)
messy_md_files["pharma_docs/clinical_trials/clinical_trial_protocol.md"] = """\
# Clinical Trial Protocol XR-447   


## 1. Introduction


This protocol outlines the phase III clinical trial for compound XR-447.   
The study aims to evaluate efficacy and safety in adult patients.   

### 1.1 Objectives   

* Primary objective: Establish non-inferiority versus placebo
* Secondary objective: Evaluate tolerability  
* Tertiary objective: Assess quality-of-life metrics  

## 2 . Study Design

The trial is __double-blind__ and *randomized*.   

* Participants: 450 adults aged 18-65
* Duration: 52 weeks   
* Sites: 12 international centers   

### 2.1 Inclusion Criteria   

1) Age 18-65  
1) Diagnosed with condition XR  
1) No prior treatment with compound class Y  

## 3. Methodology   


    def enroll_patient(patient_id):
        # validate patient
        return True

### 3.1 Randomization

The randomization scheme uses a 1:1:1 ratio.   

* Treatment arm A  
* Treatment arm B  
+ Control arm  

## 4. Endpoints


Primary endpoint: Reduction in symptom score by >=50%
Secondary endpoints:
- Adverse event rate   
- Quality of life score   

## 4. Safety Monitoring   


The Data Safety Monitoring Board (DSMB) will meet quarterly.   

"""

# File 2: lab_protocol_synthesis.md (in pharma_docs/lab_protocols)
messy_md_files["pharma_docs/lab_protocols/lab_protocol_synthesis.md"] = """\
## Synthesis Protocol for Compound XR-447  


### Materials Required   

+ Reagent A (CAS 12345-67-8)   
+ Reagent B (CAS 98765-43-2)   
* Solvent: anhydrous ethanol   
* Catalyst: palladium on carbon   

## Equipment   

1. Round-bottom flask (500 mL)
2. Magnetic stirrer   
3. Reflux condenser   
4. Rotary evaporator   

### Step-by-Step Procedure   

#### Step 1: Preparation   

Dissolve Reagent A in 200 mL of anhydrous ethanol.   

#### Step 2: Reaction   

Add Reagent B slowly under nitrogen atmosphere.   

Heat to reflux (78°C) for 4 hours.   

#### Step 3: Workup   

Cool the reaction mixture to room temperature.   

Filter off the catalyst.   

#### Step 4: Purification   

```
python
def purify(crude_product):
    # column chromatography
    fractions = run_column(crude_product, solvent_system="EtOAc:Hex 3:7")
    return collect_fractions(fractions, rf_target=0.35)
```   

### Quality Control   

- Purity must be >= 99.5% by HPLC   
- Identity confirmed by NMR   
- Melting point: 142-144°C   

## Storage Conditions   

Store at -20°C under inert atmosphere.   
Shelf life: 24 months when properly stored.   

## References   

[1] Smith et al. _Journal of Medicinal Chemistry_ 2019.   
[2] Johnson & Lee, __Organic Synthesis Handbook__, 3rd ed.   

"""

# File 3: safety_report_q2.md (in pharma_docs/safety_reports)
messy_md_files["pharma_docs/safety_reports/safety_report_q2.md"] = """\
# Quarterly Safety Report - Q2 2024   


## Executive Summary   


No serious adverse events (SAEs) were reported during Q2 2024.   


## 1. Adverse Event Summary   


### 1.1 Total Events   

| Event Type | Count | Severity |   
|---|---|---|   
| Mild | 12 | Grade 1 |   
| Moderate | 3 | Grade 2 |   
| Severe | 0 | Grade 3 |   

### 1.2 Event Details   

* Nausea (Grade 1): 7 cases   
+ Headache (Grade 1): 5 cases   
* Fatigue (Grade 2): 3 cases   

## 2. Laboratory Findings   


All laboratory values remained within normal reference ranges.   

### 2.1 Hematology   

- WBC: 4.5-10.5 × 10³/μL (normal)   
- RBC: 4.0-5.5 × 10⁶/μL (normal)   
- Platelets: 150-400 × 10³/μL (normal)   

### 2.2 Chemistry Panel   

- Liver enzymes: within 2× ULN   
- Creatinine: <1.5× baseline   
- Electrolytes: stable   

## 3. Signal Detection   


No new safety signals identified.   
Previous signals from Q1 have been resolved.   

### 3.1 Signal Evaluation Method   

```
import signal_detector

def evaluate_signals(events_df):
    detector = signal_detector.PRR()
    results = detector.run(events_df, threshold=2.0)
    return results
```   

## 4. Regulatory Notifications   


No regulatory notifications were required this quarter.   

## 5. DSMB Recommendations   


The DSMB recommends continuing the trial without modification.   

"""

# File 4: regulatory_submission_cover.md (in pharma_docs/regulatory_submissions)
messy_md_files["pharma_docs/regulatory_submissions/regulatory_submission_cover.md"] = """\
# Regulatory Submission Cover Sheet   


## NDA Application: XR-447-NDA-2024   


### Applicant Information   

__Company:__ Vernox Pharmaceuticals Inc.   
__Address:__ 1234 Research Blvd, Cambridge, MA 02139   
__Contact:__ Dr. Jane Smith (j.smith@vernox-pharma.com)   

### Submission Details   

* Submission Type: New Drug Application (NDA)   
+ Drug Name: Compound XR-447   
* Proposed Indication: Treatment of moderate-to-severe XR syndrome   
+ Route of Administration: Oral   
* Dosage Form: Film-coated tablets   
+ Strengths: 10 mg, 25 mg, 50 mg   

## Table of Contents   


1. Module 1 - Administrative   
2. Module 2 - Summaries   
3. Module 3 - Quality   
4. Module 4 - Nonclinical   
5. Module 5 - Clinical   

## Certification   


The undersigned certifies that the information submitted herein is truthful.   

### Authorized Signatory   

_Name:_ Dr. Jane Smith   
_Title:_ Chief Medical Officer   
_Date:_ 2024-07-01   

## Attachments   


Refer to the eCTD submission package for complete documentation.   

"""

# File 5: meeting_notes_dsmb.md (in pharma_docs/meeting_notes)
messy_md_files["pharma_docs/meeting_notes/meeting_notes_dsmb.md"] = """\
## DSMB Meeting Notes - June 2024   


### Attendees   

* Dr. Alan Torres (Chair)   
+ Dr. Maria Chen (Biostatistician)   
* Dr. Robert Kim (Clinician)   
+ Dr. Sarah Patel (Independent Expert)   

### Agenda   

1. Review of Q2 Safety Data   
2. Interim Efficacy Analysis   
3. Protocol Amendments   
4. Action Items   

## Q2 Safety Review   


The DSMB reviewed all adverse events from Q2 2024.   

Key findings:
- No SAEs recorded
- Mild AE profile consistent with prior quarters   
- No dose modifications required   

## Interim Efficacy   


The interim analysis shows *promising* results:   

+ 58% of patients achieved primary endpoint   
* Response rate exceeds pre-specified threshold   
* p-value: 0.023 (pre-specified alpha: 0.025)   

## Protocol Amendments   


No amendments proposed at this time.   

## Action Items   


1) Continue monitoring per protocol   
2) Prepare Q3 safety report by September 30   
3) Schedule next DSMB meeting for October   

"""

for rel_path, content in messy_md_files.items():
    full = os.path.join(WORKSPACE, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

print("Input generation complete.")
print(f"Created {len(messy_md_files)} messy markdown files and {len(distractor_txts)} distractor files.")