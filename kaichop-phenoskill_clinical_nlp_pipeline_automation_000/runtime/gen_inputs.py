import os
import random
import json
from pathlib import Path

random.seed(42)

BASE = Path("/workspace")

# --- Create distractor directory tree (10+ distractor files) ---
distractor_dirs = [
    BASE / "legacy_pipeline" / "v1" / "scripts",
    BASE / "legacy_pipeline" / "v2" / "configs",
    BASE / "notes" / "clinical" / "drafts",
    BASE / "notes" / "clinical" / "archived",
    BASE / "resources_old",
    BASE / "scratch" / "temp_outputs",
    BASE / "scratch" / "temp_inputs",
    BASE / "third_party_backup",
    BASE / "docs" / "internal",
    BASE / "exports" / "csv",
]

for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = [
    (BASE / "legacy_pipeline" / "v1" / "scripts" / "old_extract.py",
     "# Deprecated extractor\nimport sys\nprint('deprecated')\n"),
    (BASE / "legacy_pipeline" / "v1" / "scripts" / "config.json",
     json.dumps({"hpo_path": "/data/hp_legacy.obo", "version": "1.0"}, indent=2)),
    (BASE / "legacy_pipeline" / "v2" / "configs" / "pipeline.yaml",
     "hpo_obo: /data/hp_v2.obo\noutput_dir: /tmp/out\n"),
    (BASE / "legacy_pipeline" / "v2" / "configs" / "overrides.ini",
     "[paths]\nhpo=/usr/share/hp.obo\n"),
    (BASE / "notes" / "clinical" / "drafts" / "patient_note_draft.txt",
     "Draft: Patient presents with fatigue and weight gain.\n"),
    (BASE / "notes" / "clinical" / "archived" / "archived_note_2021.txt",
     "Archived: History of hypertension, type 2 diabetes.\n"),
    (BASE / "resources_old" / "hp_2021.obo",
     "format-version: 1.2\ndata-version: releases/2021-01-01\n[Term]\nid: HP:0000001\nname: All\n"),
    (BASE / "scratch" / "temp_outputs" / "raw_output.txt",
     "phenotype: ataxia\nmedication: levetiracetam\n"),
    (BASE / "scratch" / "temp_inputs" / "sample_input.txt",
     "Symptoms: headache, nausea. Meds: ibuprofen 400mg daily.\n"),
    (BASE / "third_party_backup" / "phenosnap_backup.zip",
     "placeholder zip content"),
    (BASE / "docs" / "internal" / "workflow_notes.md",
     "# Internal Workflow\nSee pipeline v2 for updated steps.\n"),
    (BASE / "exports" / "csv" / "phenotype_export_2023.csv",
     "patient_id,phenotype,medication\n001,ataxia,valproate\n"),
]

for fpath, content in distractor_files:
    fpath.write_text(content)

# --- Create the HPO OBO file at a CUSTOM (non-default) location ---
# The default path {baseDir}/resources/hp.obo will NOT exist.
# The custom path is set via HPO_OBO_PATH env var in setup_script.
custom_obo_dir = BASE / "data" / "hpo_custom"
custom_obo_dir.mkdir(parents=True, exist_ok=True)

# Minimal valid-looking hp.obo (enough for PhenoSnap to load)
hp_obo_content = """format-version: 1.2
data-version: releases/2024-01-15
ontology: hp

[Term]
id: HP:0000001
name: All
comment: Root of all terms in the Human Phenotype Ontology.

[Term]
id: HP:0001250
name: Seizures
def: "Seizures are an intermittent abnormality of the central nervous system." [HPO:probinson]
is_a: HP:0000001 ! All

[Term]
id: HP:0001251
name: Ataxia
def: "Cerebellar ataxia refers to ataxia due to dysfunction of the cerebellum." [HPO:probinson]
is_a: HP:0000001 ! All

[Term]
id: HP:0001263
name: Global developmental delay
def: "A delay in the achievement of motor or mental milestones." [HPO:probinson]
is_a: HP:0000001 ! All

[Term]
id: HP:0000365
name: Hearing loss
is_a: HP:0000001 ! All

[Term]
id: HP:0001518
name: Small for gestational age
is_a: HP:0000001 ! All

[Term]
id: HP:0002315
name: Headache
is_a: HP:0000001 ! All

[Term]
id: HP:0000822
name: Hypertension
is_a: HP:0000001 ! All

[Term]
id: HP:0000819
name: Diabetes mellitus
is_a: HP:0000001 ! All
"""

obo_path = custom_obo_dir / "hp.obo"
obo_path.write_text(hp_obo_content)

print(f"Custom hp.obo written to: {obo_path}")

# --- Create the messy clinical input that the AGENT will receive as a prompt ---
# This is stored for reference by the eval script; the agent is given the raw text in the prompt.
raw_clinical_note = """Name: Jonathan Reyes
DOB: 1987-03-22
MRN: 100298374
Phone: 555-867-5309
Email: j.reyes@personalmail.com
Address: 44 Birchwood Lane, Springfield, IL 62704

Chief Complaint: Follow-up for known seizure disorder and progressive ataxia.

PMH: Global developmental delay, seizures (onset age 3), ataxia. History of recurrent otitis media with mild hearing loss.

Current Medications:
- levetiracetam 500 mg BID
- valproate 250 mg TID
- vitamin D 1000 units daily

Clinician notes: Patient's mother reports worsening balance over past 3 months. EEG pending.
"""

agent_input_dir = BASE / "agent_task"
agent_input_dir.mkdir(parents=True, exist_ok=True)
(agent_input_dir / "clinical_note_raw.txt").write_text(raw_clinical_note)

# Store expected redacted patterns for eval
expected_redactions = {
    "name_field": "Name: [REDACTED_NAME]",
    "email": "[REDACTED_EMAIL]",
    "phone": "[REDACTED_PHONE]",
    "mrn": "[REDACTED_ID]",
    "address": "[REDACTED_ADDRESS]",
}
(agent_input_dir / "expected_redactions.json").write_text(
    json.dumps(expected_redactions, indent=2)
)

print("Workspace initialized successfully.")
print(f"Agent raw input note at: {agent_input_dir / 'clinical_note_raw.txt'}")