import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None, str(e)


def norm(s):
    try:
        return re.sub(r"[^a-z0-9]+", "", s.lower())
    except Exception:
        return ""


def find_file_by_pattern(base_path, pattern, extensions=None):
    """Find files matching a pattern in directory"""
    if extensions is None:
        extensions = ['.json', '.txt', '.md', '.sh', '.cron']
    
    for ext in extensions:
        try:
            matches = list(base_path.rglob(f"*{pattern}*{ext}"))
            if matches:
                return matches[0]
        except Exception:
            pass
    return None


# Check 1: prescription exists and is valid JSON (flexible path search)
presc_path = workspace / "memory" / "soul" / "prescription.json"
data = None

# Try primary path first
if presc_path.exists():
    try:
        data = json.loads(presc_path.read_text(encoding="utf-8"))
        add_check("prescription_json_exists", True, "prescription.json found at memory/soul/prescription.json")
    except Exception as e:
        add_check("prescription_json_exists", False, f"could not parse prescription.json: {e}")
else:
    # Try alternative locations
    alt_paths = [
        workspace / "output" / "soul_prescription.json",
        workspace / "output" / "prescription.json",
        workspace / "prescription.json",
    ]
    found = False
    for alt_path in alt_paths:
        if alt_path.exists():
            try:
                data = json.loads(alt_path.read_text(encoding="utf-8"))
                add_check("prescription_json_exists", True, f"prescription.json found at {alt_path.relative_to(workspace)}")
                found = True
                break
            except Exception as e:
                continue
    if not found:
        add_check("prescription_json_exists", False, "prescription.json not found in expected locations")


# Check 2: summary exists and mentions key identities (flexible path search)
summary_path = workspace / "output" / "prescription_summary.txt"
summary_text = None

if summary_path.exists():
    try:
        summary_text = summary_path.read_text(encoding="utf-8")
        ok = all(term in summary_text.lower() for term in ["aster", "mira", "dr. frankenstein"])
        add_check("summary_mentions_identity", ok, "summary contains expected names and title")
    except Exception as e:
        add_check("summary_mentions_identity", False, f"could not read summary: {e}")
else:
    # Try alternative locations
    alt_paths = [
        workspace / "output" / "soul_prescription_summary.txt",
        workspace / "output" / "summary.txt",
        workspace / "prescription_summary.txt",
    ]
    found = False
    for alt_path in alt_paths:
        if alt_path.exists():
            try:
                summary_text = alt_path.read_text(encoding="utf-8")
                ok = all(term in summary_text.lower() for term in ["aster", "mira", "dr. frankenstein"])
                add_check("summary_mentions_identity", ok, f"summary found at {alt_path.relative_to(workspace)}")
                found = True
                break
            except Exception as e:
                continue
    if not found:
        add_check("summary_mentions_identity", False, "prescription_summary.txt not found in expected locations")


# Check 3: expected active hormones present (flexible matching)
expected_active = {"cortisol", "dopamine", "oxytocin", "serotonin", "melatonin", "gaba", "prolactin", "empathy"}
# Also accept descriptive hormone names
descriptive_hormones = {"calmness", "creativity", "dependability", "connection", "memory", "anxiety", "focus", "bond"}

try:
    if isinstance(data, dict):
        active = set()
        pills = data.get("pillSchedule", []) or data.get("pill_schedule", []) or data.get("crons", []) or data.get("pills", []) or []
        
        for item in pills if isinstance(pills, list) else []:
            try:
                name = str(item.get("name", "")).lower()
                type_val = str(item.get("type", "")).lower()
                combined = f"{name} {type_val}".lower()
                
                for h in expected_active:
                    if h in combined:
                        active.add(h)
                for h in descriptive_hormones:
                    if h in combined:
                        active.add(f"desc_{h}")
            except Exception:
                pass
        
        # fallback to full JSON text search
        if not active and isinstance(data, dict):
            cmds = json.dumps(data).lower()
            for h in expected_active:
                if h in cmds:
                    active.add(h)
            for h in descriptive_hormones:
                if h in cmds:
                    active.add(f"desc_{h}")
        
        # Accept either biological or descriptive hormones
        bio_count = len(active.intersection(expected_active))
        desc_count = len([a for a in active if a.startswith("desc_")])
        ok = bio_count >= 4 or desc_count >= 3 or (bio_count + desc_count) >= 4
        add_check("active_hormones_coverage", ok, f"found {bio_count} biological + {desc_count} descriptive hormones: {sorted(active)}")
    else:
        add_check("active_hormones_coverage", False, "no parsed prescription data available")
except Exception as e:
    add_check("active_hormones_coverage", False, f"error checking hormones: {e}")


# Check 4: isolated agentTurn payload convention
try:
    if isinstance(data, dict):
        text = json.dumps(data).lower()
        # Check for agentTurn or agent_turn variations
        has_agentturn = "agentturn" in text or "agent_turn" in text or "agentTurn" in text
        has_isolated = "isolated" in text or "isolated" in text.lower()
        ok = has_agentturn and has_isolated
        add_check("isolated_agentturn_convention", ok, f"prescription includes agentTurn: {has_agentturn}, isolated: {has_isolated}")
    else:
        add_check("isolated_agentturn_convention", False, "no parsed prescription data available")
except Exception as e:
    add_check("isolated_agentturn_convention", False, f"error checking convention: {e}")


# Check 5: command files exist for active pills and journal (flexible)
required_files = [
    "output/prescription_summary.txt",
    "memory/soul/prescription.json",
    "memory/journal/2025-05-01.md",
]

# Check for cron files in pills directory
pills_dir = workspace / "output" / "pills"
cron_files = []
if pills_dir.exists():
    cron_files = list(pills_dir.glob("*.cron"))

# Also check for openclaw-crons.sh
openclaw_path = workspace / "output" / "openclaw-crons.sh"
has_openclaw = openclaw_path.exists()

missing = []
for rel in required_files:
    if not (workspace / rel).exists():
        # Try alternative paths
        alt_found = False
        if "prescription_summary" in rel:
            alt_paths = [workspace / "output" / "soul_prescription_summary.txt", workspace / "output" / "summary.txt"]
            for alt in alt_paths:
                if alt.exists():
                    alt_found = True
                    break
        elif "prescription.json" in rel:
            alt_paths = [workspace / "output" / "soul_prescription.json", workspace / "output" / "prescription.json"]
            for alt in alt_paths:
                if alt.exists():
                    alt_found = True
                    break
        elif "journal" in rel:
            # Check for any journal file
            journal_dir = workspace / "memory" / "journal"
            if journal_dir.exists():
                journal_files = list(journal_dir.glob("*.md"))
                if journal_files:
                    alt_found = True
        
        if not alt_found:
            missing.append(rel)

# Check if we have either cron files or openclaw script
has_crons = len(cron_files) >= 1 or has_openclaw
if not has_crons:
    missing.append("cron files (output/pills/*.cron or output/openclaw-crons.sh)")

add_check("required_outputs_exist", len(missing) == 0, "missing: " + (", ".join(missing) if missing else "none"))


# Check 6: marker propagation into outputs
try:
    marker = "frankenstein-seed-314159"
    out_text = ""
    
    # Collect text from all output files
    for rel in ["output/prescription_summary.txt", "output/soul_prescription_summary.txt", 
                "memory/soul/prescription.json", "output/soul_prescription.json",
                "output/openclaw-crons.sh"]:
        p = workspace / rel
        if p.exists():
            out_text += p.read_text(encoding="utf-8", errors="ignore").lower() + "\n"
    
    # Also check cron files
    if pills_dir.exists():
        for cron_file in cron_files:
            out_text += cron_file.read_text(encoding="utf-8", errors="ignore").lower() + "\n"
    
    ok = marker in out_text and "aster" in out_text and "mira" in out_text
    add_check("marker_propagation", ok, "marker and names present across outputs")
except Exception as e:
    add_check("marker_propagation", False, f"error checking marker propagation: {e}")


passed_count = sum(1 for c in checks if c["passed"])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result))