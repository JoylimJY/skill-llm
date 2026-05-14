import sys
import json
import re
import subprocess
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []

RESERVED_IDS = {"end", "subgraph", "graph", "flowchart"}
SPECIAL_CHARS = re.compile(r"[(),:]+")

# ─── helpers ────────────────────────────────────────────────────────────────

def find_file(pattern: str):
    """Return first match of glob pattern under workspace, or None."""
    results = list(workspace.rglob(pattern))
    return results[0] if results else None

def read_file(p):
    try:
        return Path(p).read_text()
    except Exception as e:
        return None

def run_validator(*mmd_paths):
    """Run scripts/validate-mmd on given paths. Returns (returncode, stdout)."""
    validator = workspace / "scripts" / "validate-mmd"
    try:
        result = subprocess.run(
            ["python3", str(validator)] + [str(p) for p in mmd_paths],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return 99, str(e)


# ═══════════════════════════════════════════════════════════════════════════
# FILE DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════

intake_flow_file = find_file("intake-flow.mmd")
admission_sequence_file = find_file("admission-sequence.mmd")
patient_lifecycle_file = find_file("patient-lifecycle.mmd")

# ─── Check 1: All three files exist ─────────────────────────────────────────
all_exist = all([intake_flow_file, admission_sequence_file, patient_lifecycle_file])
checks.append({
    "name": "all_three_mmd_files_exist",
    "passed": all_exist,
    "detail": (
        f"intake-flow.mmd: {'found at ' + str(intake_flow_file) if intake_flow_file else 'MISSING'} | "
        f"admission-sequence.mmd: {'found at ' + str(admission_sequence_file) if admission_sequence_file else 'MISSING'} | "
        f"patient-lifecycle.mmd: {'found at ' + str(patient_lifecycle_file) if patient_lifecycle_file else 'MISSING'}"
    )
})

# ─── Read all files ──────────────────────────────────────────────────────────
intake_text = read_file(intake_flow_file) if intake_flow_file else ""
seq_text = read_file(admission_sequence_file) if admission_sequence_file else ""
lifecycle_text = read_file(patient_lifecycle_file) if patient_lifecycle_file else ""

intake_text = intake_text or ""
seq_text = seq_text or ""
lifecycle_text = lifecycle_text or ""


# ═══════════════════════════════════════════════════════════════════════════
# FLOWCHART CHECKS  (intake-flow.mmd)
# ═══════════════════════════════════════════════════════════════════════════

# Check 2: Starts with flowchart TD or LR
fc_header = bool(re.search(r"^\s*flowchart\s+(TD|LR|TB)\b", intake_text, re.MULTILINE))
checks.append({
    "name": "intake_flow_is_flowchart",
    "passed": fc_header,
    "detail": f"intake-flow.mmd must begin with 'flowchart TD' or 'flowchart LR'. Found header match: {fc_header}"
})

# Check 3: Contains a decision node (rhombus {})
has_decision = bool(re.search(r'\w+\s*\{[^}]+\}', intake_text))
checks.append({
    "name": "intake_flow_has_decision_node",
    "passed": has_decision,
    "detail": "intake-flow.mmd must contain at least one rhombus decision node using {} syntax."
})

# Check 4: Contains a subgraph with proper id [Label] syntax (no spaces in ID)
subgraph_ok = bool(re.search(r'subgraph\s+\S+\s+\[[^\]]+\]', intake_text))
checks.append({
    "name": "intake_flow_subgraph_proper_syntax",
    "passed": subgraph_ok,
    "detail": (
        "intake-flow.mmd must contain at least one subgraph using 'subgraph id [Label]' syntax "
        f"(no spaces in ID, bracketed label required). Found: {subgraph_ok}"
    )
})

# Check 5: No reserved word used as a node ID
def has_reserved_node_id(text):
    node_id_re = re.compile(r'\b([A-Za-z_]\w*)\s*[\[\{(]')
    for m in node_id_re.finditer(text):
        if m.group(1).lower() in RESERVED_IDS:
            return True, m.group(1)
    # also check subgraph IDs
    for m in re.finditer(r'subgraph\s+(\S+)', text):
        sg_id = m.group(1)
        if sg_id.lower() in RESERVED_IDS - {"end"}:  # "end" closes subgraph, not reserved here
            return True, sg_id
    return False, None

reserved_used, which_reserved = has_reserved_node_id(intake_text)
checks.append({
    "name": "intake_flow_no_reserved_ids",
    "passed": not reserved_used,
    "detail": (
        f"intake-flow.mmd must not use reserved IDs (end, subgraph, graph, flowchart) as node IDs. "
        f"Found reserved ID: '{which_reserved}'" if reserved_used else "No reserved IDs used — good."
    )
})

# Check 6: Labels with special chars (parens/colons/commas) are quoted
def unquoted_special_labels(text):
    """Return list of problematic label snippets."""
    bad = []
    # Match bracket content NOT starting with "
    for m in re.finditer(r'\w+\s*\[([^"\n][^\]\n]*)\]|\w+\s*\{([^"\n][^}\n]*)\}', text):
        inner = m.group(1) or m.group(2) or ""
        if SPECIAL_CHARS.search(inner):
            bad.append(inner[:50])
    return bad

bad_labels_fc = unquoted_special_labels(intake_text)
checks.append({
    "name": "intake_flow_special_labels_quoted",
    "passed": len(bad_labels_fc) == 0,
    "detail": (
        "All node labels in intake-flow.mmd that contain (, ), :, or , must use double-quoted strings. "
        f"Unquoted violations found: {bad_labels_fc}" if bad_labels_fc else "All special-char labels are properly quoted."
    )
})


# ═══════════════════════════════════════════════════════════════════════════
# SEQUENCE DIAGRAM CHECKS  (admission-sequence.mmd)
# ═══════════════════════════════════════════════════════════════════════════

# Check 7: Starts with sequenceDiagram
seq_header = bool(re.search(r"^\s*sequenceDiagram\b", seq_text, re.MULTILINE))
checks.append({
    "name": "admission_sequence_is_sequenceDiagram",
    "passed": seq_header,
    "detail": f"admission-sequence.mmd must begin with 'sequenceDiagram'. Found: {seq_header}"
})

# Check 8: Has participant declarations
has_participants = len(re.findall(r'^\s*participant\s+\S+', seq_text, re.MULTILINE)) >= 2
checks.append({
    "name": "admission_sequence_has_participants",
    "passed": has_participants,
    "detail": "admission-sequence.mmd must declare at least 2 participants."
})

# Check 9: Participant names have no spaces (PascalCase/camelCase)
def participants_have_spaces(text):
    bad = []
    for m in re.finditer(r'^\s*participant\s+(.+)', text, re.MULTILINE):
        name = m.group(1).strip()
        if ' ' in name:
            bad.append(name)
    return bad

bad_participants = participants_have_spaces(seq_text)
checks.append({
    "name": "admission_sequence_participant_names_no_spaces",
    "passed": len(bad_participants) == 0,
    "detail": (
        f"Participant names must not contain spaces (use PascalCase or camelCase). "
        f"Violations: {bad_participants}" if bad_participants else "All participant names are valid."
    )
})

# Check 10: Has activate/deactivate lifelines
has_activate = bool(re.search(r'^\s*activate\s+\S+', seq_text, re.MULTILINE))
has_deactivate = bool(re.search(r'^\s*deactivate\s+\S+', seq_text, re.MULTILINE))
checks.append({
    "name": "admission_sequence_has_activate_deactivate",
    "passed": has_activate and has_deactivate,
    "detail": (
        f"admission-sequence.mmd must use 'activate' and 'deactivate' for lifelines. "
        f"activate found: {has_activate}, deactivate found: {has_deactivate}"
    )
})

# Check 11: Contains both sync (->>) and async (-->>) arrows
has_sync = bool(re.search(r'->>', seq_text))
has_async = bool(re.search(r'-->>', seq_text))
checks.append({
    "name": "admission_sequence_has_sync_and_async_arrows",
    "passed": has_sync and has_async,
    "detail": (
        f"admission-sequence.mmd should use both ->> (sync) and -->> (async) arrows. "
        f"sync (->>) found: {has_sync}, async (-->>) found: {has_async}"
    )
})


# ═══════════════════════════════════════════════════════════════════════════
# STATE DIAGRAM CHECKS  (patient-lifecycle.mmd)
# ═══════════════════════════════════════════════════════════════════════════

# Check 12: Starts with stateDiagram-v2
state_header = bool(re.search(r"^\s*stateDiagram-v2\b", lifecycle_text, re.MULTILINE))
checks.append({
    "name": "patient_lifecycle_is_stateDiagram_v2",
    "passed": state_header,
    "detail": f"patient-lifecycle.mmd must begin with 'stateDiagram-v2'. Found: {state_header}"
})

# Check 13: Contains [*] start and [*] end transitions
has_start_star = bool(re.search(r'\[\*\]\s*-->', lifecycle_text))
has_end_star = bool(re.search(r'-->\s*\[\*\]', lifecycle_text))
checks.append({
    "name": "patient_lifecycle_has_star_transitions",
    "passed": has_start_star and has_end_star,
    "detail": (
        f"patient-lifecycle.mmd must have '[*] --> ...' (start) and '--> [*]' (terminal) transitions. "
        f"start [*]: {has_start_star}, end [*]: {has_end_star}"
    )
})

# Check 14: Contains at least 4 states (beyond [*])
state_names = re.findall(r'^\s*(\w[\w\s]*)\s*-->', lifecycle_text, re.MULTILINE)
unique_states = set(s.strip() for s in state_names if s.strip() != '[*]' and s.strip() != '*')
# also find states from the right side
right_states = re.findall(r'-->\s*(\w[\w\s]+?)(?:\s*:|$|\n)', lifecycle_text, re.MULTILINE)
unique_states.update(s.strip() for s in right_states if s.strip() not in ('[*]', '*'))
has_enough_states = len(unique_states) >= 4
checks.append({
    "name": "patient_lifecycle_has_minimum_states",
    "passed": has_enough_states,
    "detail": f"patient-lifecycle.mmd should model at least 4 distinct states. Found states: {unique_states}"
})

# Check 15: Transitions have labels (: label syntax)
labeled_transitions = re.findall(r'-->\s*\w+\s*:\s*\S+', lifecycle_text)
has_labeled_transitions = len(labeled_transitions) >= 2
checks.append({
    "name": "patient_lifecycle_transitions_are_labeled",
    "passed": has_labeled_transitions,
    "detail": (
        f"patient-lifecycle.mmd must have labeled transitions using ': label' syntax. "
        f"Found {len(labeled_transitions)} labeled transitions."
    )
})

# Check 16: No reserved IDs used as state names
def state_reserved(text):
    for m in re.finditer(r'^\s*(\w+)\s*-->', text, re.MULTILINE):
        sid = m.group(1)
        if sid.lower() in RESERVED_IDS:
            return True, sid
    return False, None

state_reserved_used, state_res_which = state_reserved(lifecycle_text)
checks.append({
    "name": "patient_lifecycle_no_reserved_ids",
    "passed": not state_reserved_used,
    "detail": (
        f"patient-lifecycle.mmd must not use reserved IDs as state names. "
        f"Found: '{state_res_which}'" if state_reserved_used else "No reserved IDs as state names."
    )
})


# ═══════════════════════════════════════════════════════════════════════════
# CROSS-CUTTING: VALIDATOR MUST PASS ON ALL THREE
# ═══════════════════════════════════════════════════════════════════════════

if all([intake_flow_file, admission_sequence_file, patient_lifecycle_file]):
    rc, vout = run_validator(intake_flow_file, admission_sequence_file, patient_lifecycle_file)
    validator_passed = (rc == 0)
    checks.append({
        "name": "validator_passes_all_three_files",
        "passed": validator_passed,
        "detail": f"Exit code: {rc}\nValidator output:\n{vout[:2000]}"
    })
else:
    checks.append({
        "name": "validator_passes_all_three_files",
        "passed": False,
        "detail": "Cannot run validator — one or more files are missing."
    })


# ═══════════════════════════════════════════════════════════════════════════
# CONTENT RELEVANCE: Healthcare domain terminology
# ═══════════════════════════════════════════════════════════════════════════

all_text = intake_text + seq_text + lifecycle_text
healthcare_terms = ["triage", "patient", "admission", "discharge", "ehr", "hl7", "registration", "billing", "ward", "insurance"]
found_terms = [t for t in healthcare_terms if t.lower() in all_text.lower()]
healthcare_relevant = len(found_terms) >= 3
checks.append({
    "name": "diagrams_contain_healthcare_domain_content",
    "passed": healthcare_relevant,
    "detail": f"Diagrams should model a healthcare patient intake workflow. Found terms: {found_terms}"
})


# ═══════════════════════════════════════════════════════════════════════════
# SCORE & RESULT
# ═══════════════════════════════════════════════════════════════════════════

total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3)
overall_passed = passed_count >= int(total * 0.85)  # 85% threshold

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))