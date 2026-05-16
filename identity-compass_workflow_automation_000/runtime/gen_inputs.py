import os
import json
import yaml
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# ─── Directory structure ───────────────────────────────────────────────────────
dirs = [
    "obsidian-vault/compass/prior",
    "obsidian-vault/compass/vectors",
    "obsidian-vault/compass/clusters",
    "obsidian-vault/compass/signals",
    "obsidian-vault/templates",
    "obsidian-vault/daily",
    "scripts",
    "docs",
    "logs",
    "exports/archive",
    "exports/temp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ──────────────────────────────────────────────────────────
(workspace / "obsidian-vault/daily/2026-03-20.md").write_text(
    "# Daily Note\nHad a great meeting about the product roadmap.\nThinking about switching teams.\n"
)
(workspace / "obsidian-vault/daily/2026-03-21.md").write_text(
    "# Daily Note\nFelt really drained after the standup. The micromanagement is getting worse.\nSaw a job posting for a research role — looked interesting.\n"
)
(workspace / "obsidian-vault/templates/vector-template.md").write_text(
    "# Vector Template\nFill in the frontmatter fields below.\n---\ntype: vector\ndate: YYYY-MM-DD\n...\n"
)
(workspace / "obsidian-vault/compass/_MOC.md").write_text(
    "# Compass MOC\n- [[magnetization]]\n- [[timeline]]\n"
)
(workspace / "obsidian-vault/compass/clusters/autonomy-first.md").write_text(
    "# Autonomy First\nCore cluster: prefers self-directed work over structured execution.\n"
)
(workspace / "obsidian-vault/compass/clusters/depth-builder.md").write_text(
    "# Depth Builder\nCore cluster: values deep mastery over shallow breadth.\n"
)
(workspace / "docs/system-overview.md").write_text(
    "# System Overview\nThis system tracks personal decision vectors over time.\nSee scripts/ for pipeline tools.\n"
)
(workspace / "logs/session_2026-03-19.txt").write_text(
    "Session log: user discussed career pivot, mentioned 'research roles feel right'.\n"
)
(workspace / "logs/session_2026-03-20.txt").write_text(
    "Session log: user rejected management track offer ('not my thing at all').\n"
)
(workspace / "exports/archive/vectors_backup_2026-02.json").write_text(
    json.dumps({"backup": True, "date": "2026-02-01", "vectors": []}, indent=2)
)
(workspace / "exports/temp/scratch.txt").write_text("temp notes\n")

# ─── Existing MALFORMED vector notes (agent must NOT use these as-is) ──────────
bad_vector_1 = """\
---
type: vector
date: 2026-01-10
what: "management track rejection"
why_surface: "not interested in people management"
direction: [0.9, 0.5, 0.4]
weight: 8
domain: career
---
Notes: This vector is missing several required fields.
"""
(workspace / "obsidian-vault/compass/vectors/mgmt-rejection.md").write_text(bad_vector_1)

bad_vector_2 = """\
---
type: vector
date: 2026-02-14
what: "coffee shop freelance day"
why_surface: "wanted a change of scenery"
why_essence: "craves autonomy in work environment"
direction: [0.7, 0.3, 0.1]
intensity: 0.4
confidence: 0.5
weight: 2
domain: life
---
Missing cluster and tags fields.
"""
(workspace / "obsidian-vault/compass/vectors/freelance-day.md").write_text(bad_vector_2)

# ─── raw_signals.md (background signal log) ───────────────────────────────────
raw_signals = """\
# Raw Signals Log

## 2026-03-19
- Signal: ENVY | "That researcher at DeepMind gets to just think all day — honestly jealous" | → deep research work → core_values candidate
- Signal: FLOW | "I lost track of time reading that ML paper last week" | → ML research = flow state → core_values
- Signal: FATIGUE | "Three meetings in a row about nothing — I can't keep doing this" | → meeting-heavy culture → anti_values

## 2026-03-20
- Signal: FATIGUE | "The micromanagement is exhausting" | → low-autonomy environments → anti_values
- Signal: INTEREST | "That new research engineering role at Meridian AI looked really interesting" | → Meridian AI opportunity candidate
- Signal: REPEAT | User mentioned "research" in contexts: 1) career goals, 2) ideal day, 3) company search | → weight boost candidate

## 2026-03-21
- Signal: ENVY | "Wish I could work on foundational problems, not just features" | → foundational/deep work → core_values
- Signal: CONTRADICTION | Said "stability matters" but also "I'd take a pay cut to work on interesting problems" | → H confidence should be reviewed
- Signal: INTEREST | "NeuroScale is hiring ML researchers — seems like a good culture fit" | → NeuroScale opportunity candidate
"""
(workspace / "obsidian-vault/compass/signals/raw_signals.md").write_text(raw_signals)

# ─── Prior H vector (Phase 1 output, partial) ─────────────────────────────────
prior_h = """\
# H Vector — Prior (Phase 1 Output)

Extracted from dialectical sessions 2026-03-18 through 2026-03-21.

```yaml
H:
  core_values: ["autonomous thinking", "deep research", "foundational problem-solving"]
  anti_values: ["micromanagement", "execution-only roles", "meeting-heavy culture"]
  direction: [0.82, 0.75, 0.55]
  domain_weights:
    career: 0.85
    family: 0.5
    health: 0.4
    finance: 0.35
    growth: 0.75
  confidence: 0.72
  one_liner: "A researcher at heart who needs the freedom to go deep, not wide"
  last_updated: "2026-03-21"
```
"""
(workspace / "obsidian-vault/compass/prior/h-vector-phase1.md").write_text(prior_h)

# ─── The task input: a structured batch of new vectors to register ─────────────
# This is the raw data the agent must convert into proper vault notes + run pipeline
new_vectors_raw = {
    "batch_date": "2026-03-22",
    "source": "session_2026-03-21_extraction",
    "extracted_vectors": [
        {
            "id": "vec_001",
            "what": "rejected senior PM role",
            "why_surface": "Would mean less coding and more coordination work",
            "why_essence": "Prioritizes technical depth over organizational influence",
            "direction": [0.80, 0.85, 0.30],
            "intensity": 0.88,
            "confidence": 0.90,
            "weight": 9,
            "domain": "career",
            "cluster": "autonomy-first",
            "tags": ["career", "rejection", "anti"],
            "date": "2026-03-21"
        },
        {
            "id": "vec_002",
            "what": "deep-dive ML paper reading session",
            "why_surface": "Spent 4 hours reading without noticing",
            "why_essence": "Deep intellectual engagement is intrinsically rewarding",
            "direction": [0.60, 0.90, 0.40],
            "intensity": 0.95,
            "confidence": 0.88,
            "weight": 7,
            "domain": "growth",
            "cluster": "depth-builder",
            "tags": ["growth", "preference", "flow"],
            "date": "2026-03-20"
        },
        {
            "id": "vec_003",
            "what": "Meridian AI Research Engineer role",
            "why_surface": "Strong research culture, autonomy in project selection",
            "why_essence": "Alignment with deep autonomous research values",
            "direction": [0.85, 0.78, 0.52],
            "intensity": 0.80,
            "confidence": 0.75,
            "weight": 8,
            "domain": "career",
            "cluster": "autonomy-first",
            "tags": ["career", "opportunity", "company"],
            "date": "2026-03-21",
            "status": "considering"
        },
        {
            "id": "vec_004",
            "what": "NeuroScale ML Research role",
            "why_surface": "Interesting problems but unclear autonomy level",
            "why_essence": "Potential depth alignment but structural uncertainty",
            "direction": [0.55, 0.80, 0.25],
            "intensity": 0.65,
            "confidence": 0.60,
            "weight": 7,
            "domain": "career",
            "cluster": "depth-builder",
            "tags": ["career", "opportunity", "company"],
            "date": "2026-03-21",
            "status": "considering"
        },
        {
            "id": "vec_005",
            "what": "TechCorp Staff Engineer offer",
            "why_surface": "High salary, but very process-heavy team",
            "why_essence": "Financial security conflicts with autonomy and depth values",
            "direction": [-0.30, -0.20, 0.60],
            "intensity": 0.70,
            "confidence": 0.82,
            "weight": 8,
            "domain": "career",
            "cluster": "autonomy-first",
            "tags": ["career", "opportunity", "company", "tension"],
            "date": "2026-03-21",
            "status": "received"
        }
    ]
}
(workspace / "new_vectors_batch.json").write_text(json.dumps(new_vectors_raw, indent=2))

# ─── scripts/export_vectors.py ────────────────────────────────────────────────
export_script = """\
#!/usr/bin/env python3
\"\"\"
Export all vector notes from obsidian-vault/compass/vectors/ to scripts/vectors.json
Reads YAML frontmatter from each .md file.
\"\"\"
import sys
import json
import yaml
import re
from pathlib import Path

def extract_frontmatter(text):
    \"\"\"Extract YAML frontmatter from markdown file.\"\"\"
    match = re.match(r'^---\\s*\\n(.*?)\\n---', text, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None

def main():
    vault_dir = Path("obsidian-vault/compass/vectors")
    output_path = Path("scripts/vectors.json")
    
    vectors = []
    errors = []
    
    for md_file in sorted(vault_dir.glob("*.md")):
        text = md_file.read_text()
        fm = extract_frontmatter(text)
        if fm is None:
            errors.append(f"No valid frontmatter: {md_file.name}")
            continue
        
        # Validate required fields
        required = ["type", "date", "what", "why_surface", "why_essence", 
                    "direction", "intensity", "confidence", "weight", "domain",
                    "cluster", "tags"]
        missing = [f for f in required if f not in fm]
        if missing:
            errors.append(f"Missing fields {missing} in {md_file.name}")
            continue
        
        if fm.get("type") != "vector":
            continue
            
        vectors.append(fm)
    
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(vectors, indent=2, default=str))
    
    print(f"Exported {len(vectors)} vectors to {output_path}")
    if errors:
        print(f"Skipped {len(errors)} files with errors:")
        for e in errors:
            print(f"  - {e}")

if __name__ == "__main__":
    main()
"""
(workspace / "scripts/export_vectors.py").write_text(export_script)

# ─── scripts/calculate_magnetization.py ──────────────────────────────────────
calc_script = """\
#!/usr/bin/env python3
\"\"\"
Calculate magnetization (M) from vectors.json against H vector.
Outputs magnetization.json.
\"\"\"
import json
import math
import sys
from pathlib import Path
from datetime import datetime, date

def cosine_similarity(v1, v2):
    \"\"\"Compute cosine similarity between two 3D vectors.\"\"\"
    dot = sum(a*b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a**2 for a in v1))
    norm2 = math.sqrt(sum(b**2 for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def compute_decay(date_str, days_old=None):
    \"\"\"Compute time decay: 0.95^(days/30)\"\"\"
    try:
        if isinstance(date_str, (datetime, date)):
            vec_date = date_str if isinstance(date_str, date) else date_str.date()
        else:
            vec_date = datetime.strptime(str(date_str), "%Y-%m-%d").date()
        today = date(2026, 3, 22)
        days = (today - vec_date).days
        return 0.95 ** (days / 30)
    except Exception:
        return 1.0

def main():
    vectors_path = Path("scripts/vectors.json")
    output_path = Path("scripts/magnetization.json")
    
    if not vectors_path.exists():
        print("Error: scripts/vectors.json not found. Run export_vectors.py first.")
        sys.exit(1)
    
    vectors = json.loads(vectors_path.read_text())
    
    # H vector from prior
    H_dir = [0.82, 0.75, 0.55]
    H_anti_values = ["micromanagement", "execution-only roles", "meeting-heavy culture"]
    
    # Normalize H
    h_norm = math.sqrt(sum(x**2 for x in H_dir))
    H_unit = [x/h_norm for x in H_dir]
    
    total_weight = 0.0
    weighted_sum = 0.0
    cluster_data = {}
    
    for v in vectors:
        direction = v.get("direction", [0, 0, 0])
        weight = float(v.get("weight", 1))
        date_val = v.get("date", "2026-03-22")
        
        # Apply decay
        decay = compute_decay(date_val)
        
        # Old bead rule: 6+ months old and weight <= 3
        try:
            if isinstance(date_val, (datetime, date)):
                vec_date = date_val if isinstance(date_val, date) else date_val.date()
            else:
                vec_date = datetime.strptime(str(date_val), "%Y-%m-%d").date()
            today = date(2026, 3, 22)
            days_old = (today - vec_date).days
            if days_old >= 180 and weight <= 3:
                decay *= 0.5  # halve influence
        except Exception:
            pass
        
        effective_weight = weight * decay
        
        # Compute alignment
        cos_sim = cosine_similarity(direction, H_unit)
        
        # Check anti-value overlap (simplified: check tags)
        tags = v.get("tags", [])
        anti_overlap = 0.1 if "anti" in tags else 0.0
        
        alignment = cos_sim - anti_overlap
        
        weighted_sum += effective_weight * alignment
        total_weight += effective_weight
        
        # Cluster aggregation
        cluster = str(v.get("cluster", "")).replace("[[", "").replace("]]", "")
        if cluster:
            if cluster not in cluster_data:
                cluster_data[cluster] = {"weighted_sum": 0.0, "total_weight": 0.0}
            cluster_data[cluster]["weighted_sum"] += effective_weight * alignment
            cluster_data[cluster]["total_weight"] += effective_weight
    
    M = weighted_sum / total_weight if total_weight > 0 else 0.0
    
    clusters = {}
    for name, data in cluster_data.items():
        if data["total_weight"] > 0:
            clusters[name] = {
                "magnetization": round(data["weighted_sum"] / data["total_weight"], 4),
                "vector_count": sum(1 for v in vectors if str(v.get("cluster","")).replace("[[","").replace("]]","") == name)
            }
    
    result = {
        "magnetization_magnitude": round(M, 4),
        "magnetization_vector": H_unit,
        "H_confidence": 0.72,
        "H_one_liner": "A researcher at heart who needs the freedom to go deep, not wide",
        "H_last_updated": "2026-03-21",
        "clusters": clusters,
        "computed_at": "2026-03-22",
        "vector_count": len(vectors)
    }
    
    output_path.write_text(json.dumps(result, indent=2))
    print(f"Magnetization M = {M:.4f}")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()
"""
(workspace / "scripts/calculate_magnetization.py").write_text(calc_script)

# ─── sample_data.json (demo, must not be modified) ───────────────────────────
sample_data = {
    "_note": "Demo data only — do not modify",
    "identity": [
        {"what": "sample identity bead", "why": "demo", "dir": [1,0,0], "w": 5, "cl": "identity"}
    ],
    "opportunities": [],
    "H": {"dir": [0.82, 0.75, 0.55], "mag": 0.75},
    "oneLiner": "Demo one-liner",
    "clusters": []
}
(workspace / "scripts/sample_data.json").write_text(json.dumps(sample_data, indent=2))

# ─── visualize_2d.html (stub — just needs to exist) ──────────────────────────
html_stub = """\
<!DOCTYPE html>
<html>
<head><title>Identity Compass 2D</title></head>
<body>
<script>
// Loads compass_data.json for visualization
fetch('compass_data.json').then(r=>r.json()).then(data=>{
  document.body.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
});
</script>
</body>
</html>
"""
(workspace / "scripts/visualize_2d.html").write_text(html_stub)

# ─── Partial/broken magnetization.json (stale, agent must regenerate) ─────────
stale_magnetization = {
    "magnetization_magnitude": 0.1234,
    "magnetization_vector": [0.5, 0.5, 0.5],
    "H_confidence": 0.3,
    "H_one_liner": "STALE DATA - needs recomputation",
    "clusters": {},
    "computed_at": "2026-01-01",
    "vector_count": 0
}
(workspace / "scripts/magnetization.json").write_text(json.dumps(stale_magnetization, indent=2))

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")