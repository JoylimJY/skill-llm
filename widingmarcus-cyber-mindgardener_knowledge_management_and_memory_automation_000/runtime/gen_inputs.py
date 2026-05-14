import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────
dirs = [
    "lab/protocols",
    "lab/compounds",
    "lab/researchers",
    "lab/experiments/phase1",
    "lab/experiments/phase2",
    "reports/weekly",
    "reports/monthly",
    "archive/2023",
    "archive/2024",
    "notes/meetings",
    "notes/ideas",
    "data/raw",
    "data/processed",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────
distractors = {
    "lab/protocols/centrifuge_sop.md": "# Centrifuge SOP\nSpin at 3000 rpm for 10 min.",
    "lab/protocols/pcr_protocol.md": "# PCR Protocol\nCycles: 35. Annealing: 58°C.",
    "lab/compounds/compound_index.csv": "id,name,mw\nCPD-001,Veratromine,291.4\nCPD-002,Synaptinol,318.7\nCPD-003,Neuroflux,204.2",
    "lab/researchers/team_roster.txt": "Dr. Amara Osei\nDr. Lena Kirchner\nPostdoc: Ryo Tanaka\nPhD: Sofia Reyes",
    "lab/experiments/phase1/results_jan.csv": "sample,inhibition_pct\nA1,34.2\nA2,67.8\nA3,22.1",
    "lab/experiments/phase1/results_feb.csv": "sample,inhibition_pct\nB1,55.0\nB2,89.3\nB3,41.7",
    "lab/experiments/phase2/protocol_draft.md": "# Phase 2 Notes\nIncrease dosage to 50mg/kg.",
    "reports/weekly/week_42.md": "Nothing unusual. Compound CPD-002 shows promise.",
    "reports/monthly/oct_summary.md": "October: 3 experiments completed. CPD-001 de-prioritized.",
    "archive/2023/old_results.csv": "legacy data - do not use",
    "archive/2024/backup_notes.txt": "backup created 2024-03-01",
    "notes/meetings/2024-10-15.md": "Discussed synergy between Veratromine and Synaptinol.",
    "notes/meetings/2024-11-02.md": "Dr. Kirchner proposed new assay for CPD-003.",
    "notes/ideas/future_directions.md": "Consider CRISPR validation for top 3 compounds.",
    "data/raw/sensor_log_001.txt": "\n".join(f"t={i*10}ms val={random.uniform(0,5):.3f}" for i in range(20)),
    "data/processed/cleaned_sensor.csv": "time_ms,value\n" + "\n".join(f"{i*10},{random.uniform(0,5):.3f}" for i in range(20)),
}
for path, content in distractors.items():
    (workspace / path).write_text(content)

# ── PRIMARY INPUT: raw conversation transcripts ─────────────────────
# These are the messy, real-world conversation logs the agent must feed
# into the memory pipeline. Placed in a "conversations" folder.
(workspace / "conversations").mkdir(exist_ok=True)

conv1 = """\
[2024-11-10 09:14] Dr. Amara Osei: We confirmed yesterday that Veratromine inhibits kinase KX-7 at IC50 of 120 nM.
[2024-11-10 09:15] AI Assistant: That's significant. Is this consistent with previous assays?
[2024-11-10 09:16] Dr. Amara Osei: Yes, but the earlier test showed 145 nM — slight improvement. We should update the compound profile.
[2024-11-10 09:17] AI Assistant: Noted. Should we also link this to the downstream pathway work Ryo Tanaka is doing?
[2024-11-10 09:18] Dr. Amara Osei: Absolutely. Ryo is studying the KX-7 → NF-κB cascade. This is directly relevant.
[2024-11-10 09:20] Dr. Amara Osei: Also, CPD-002 (Synaptinol) failed the hepatotoxicity screen last week. We're putting it on hold.
"""

conv2 = """\
[2024-11-12 14:00] Dr. Lena Kirchner: New data just in — Neuroflux (CPD-003) shows off-target binding to serotonin receptor 5-HT2A.
[2024-11-12 14:02] AI Assistant: That could be a safety concern. What's the binding affinity?
[2024-11-12 14:03] Dr. Lena Kirchner: Ki of about 80 nM. We didn't expect this at all.
[2024-11-12 14:05] AI Assistant: Do we have prior data on 5-HT2A interactions for the Neuroflux class?
[2024-11-12 14:06] Dr. Lena Kirchner: No prior data — this is completely new. It contradicts our earlier clean profile assumption.
[2024-11-12 14:08] Dr. Lena Kirchner: Ryo Tanaka is running a counter-screen this Friday to validate.
[2024-11-12 14:10] AI Assistant: Understood. I'll flag this as a potential conflict with the Phase 2 go/no-go criteria.
"""

conv3 = """\
[2024-11-14 10:30] Sofia Reyes: Quick update — I've been cross-referencing KX-7 inhibitors from literature. Three compounds structurally similar to Veratromine show IC50 < 100 nM.
[2024-11-14 10:32] AI Assistant: Interesting. What are their selectivity profiles?
[2024-11-14 10:33] Sofia Reyes: Two have clean ADMET. One has hERG liability.
[2024-11-14 10:35] Sofia Reyes: Also, I want to flag that the IC50 for Veratromine might actually be 110 nM based on a repeat assay I ran this morning. Could be measurement noise.
[2024-11-14 10:37] AI Assistant: So we have 120 nM from Dr. Osei's run, 145 nM from the earlier test, and now 110 nM from you?
[2024-11-14 10:38] Sofia Reyes: Correct. We need to reconcile. The compound card currently says 145 nM which is outdated.
"""

(workspace / "conversations" / "session_2024-11-10.txt").write_text(conv1)
(workspace / "conversations" / "session_2024-11-12.txt").write_text(conv2)
(workspace / "conversations" / "session_2024-11-14.txt").write_text(conv3)

# ── a fake partial garden.yaml (wrong/incomplete) to confuse naive agent
# Agent must NOT use this — must run `garden init` to get the real one
(workspace / "garden.yaml.broken").write_text("""\
# INCOMPLETE - do not use
version: 0.0.1
memory_dir: wrong_path/
""")

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")