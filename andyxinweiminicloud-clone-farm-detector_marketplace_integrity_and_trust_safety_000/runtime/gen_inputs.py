import json
import os
import random
import hashlib
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ────────────────────────────────────────────────────────
dirs = [
    "submissions",
    "submissions/metadata",
    "submissions/schemas",
    "registry/publishers",
    "registry/audit_logs",
    "registry/dependency_graph",
    "internal/trust_scores",
    "internal/reports_archive",
    "internal/flagged_history",
    "tools",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Helper ─────────────────────────────────────────────────────────────────────
def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def make_skill(name, node_id, published_at, capsule_code, gene_summary, dependencies=None, description=None, emoji="⚙️"):
    src = capsule_code
    return {
        "skill_id": f"skill_{sha256(name)[:12]}",
        "name": name,
        "publisher": {"node_id": node_id, "alias": f"pub_{node_id[:6]}"},
        "published_at": published_at,
        "description": description or f"A utility skill for {name}",
        "emoji": emoji,
        "capsule": {
            "sha256": sha256(src),
            "source": src,
        },
        "gene": {
            "summary": gene_summary,
        },
        "dependencies": dependencies or [],
        "downloads": random.randint(10, 500),
        "reputation_score": round(random.uniform(3.0, 5.0), 2),
    }

# ── Cluster A: 4 near-identical JSON formatter skills (variable rename + comment injection) ──
# Functional core: same algorithm, names changed, comments added/removed, whitespace tweaked
base_code_a = """\
def format_json(data):
    import json
    result = json.dumps(data, indent=4, sort_keys=True)
    return result

def validate_schema(payload):
    if not isinstance(payload, dict):
        raise ValueError("payload must be dict")
    return True
"""

code_a1 = base_code_a  # original

code_a2 = """\
def format_json_output(data):
    import json
    # Format the JSON with indentation
    output = json.dumps(data, indent=4, sort_keys=True)
    return output

def check_schema(payload):
    if not isinstance(payload, dict):
        raise ValueError("payload must be dict")
    return True
"""

code_a3 = """\
def format_json(input_data):
    import json
    # Beautify JSON
    res = json.dumps(input_data, indent=4, sort_keys=True)

    return res

def validate_schema(p):
    # Check type
    if not isinstance(p, dict):
        raise ValueError("payload must be dict")
    return True
"""

code_a4 = """\
def format_json(d):
    import json
    formatted = json.dumps(d, indent=4, sort_keys=True)
    return formatted  # return formatted string

def validate_schema(payload):
    # Validate
    if not isinstance(payload, dict):
        raise ValueError("payload must be dict")
    return True
"""

skills_cluster_a = [
    make_skill(
        "json-formatter-pro", "node_c4f9a1b2e3d0", "2024-12-05T09:01:00Z",
        code_a1,
        "Formats and validates JSON payloads with configurable indentation and key sorting.",
        description="Professional JSON formatting utility for agent pipelines",
        emoji="🔧"
    ),
    make_skill(
        "json-beautifier-plus", "node_c4f9a1b2e3d0", "2024-12-05T09:04:00Z",
        code_a2,
        "Formats and validates JSON payloads with configurable indentation and key sorting.",
        description="Professional JSON formatting utility for agent pipelines",
        emoji="🔧"
    ),
    make_skill(
        "format-json-fast", "node_c4f9a1b2e3d0", "2024-12-05T09:08:00Z",
        code_a3,
        "Formats and validates JSON payloads with configurable indentation and key sorting.",
        description="Professional JSON formatting utility for agent pipelines",
        emoji="🔧"
    ),
    make_skill(
        "json-style-fixer", "node_c4f9a1b2e3d0", "2024-12-05T09:13:00Z",
        code_a4,
        "Formats and validates JSON payloads with configurable indentation and key sorting.",
        description="Professional JSON formatting utility for agent pipelines",
        emoji="🔧"
    ),
]

# ── Cluster B: 3 YAML validator skills (whitespace injection + cross-citation ring) ──
base_code_b = """\
def validate_yaml(content):
    import yaml
    try:
        parsed = yaml.safe_load(content)
        return parsed is not None
    except yaml.YAMLError as e:
        return False

def lint_yaml_keys(data, required_keys):
    missing = [k for k in required_keys if k not in data]
    return missing
"""

code_b2 = """\
def validate_yaml(content):


    import yaml
    try:
        parsed = yaml.safe_load(content)
        return parsed is not None
    except yaml.YAMLError as e:
        return False

def lint_yaml_keys(data, required_keys):

    missing = [k for k in required_keys if k not in data]
    return missing
"""

code_b3 = """\
def validate_yaml(content):
    import yaml


    try:
        parsed = yaml.safe_load(content)

        return parsed is not None
    except yaml.YAMLError as e:
        return False


def lint_yaml_keys(data, required_keys):
    missing = [k for k in required_keys if k not in data]
    return missing

"""

# Cross-citation: B skills depend on A skills and each other
cluster_a_ids = [s["skill_id"] for s in skills_cluster_a]

skills_cluster_b = [
    make_skill(
        "yaml-validator-core", "node_c4f9a1b2e3d0", "2024-12-06T11:00:00Z",
        base_code_b,
        "Validates and lints YAML configuration files for agent deployment pipelines.",
        dependencies=[cluster_a_ids[0], cluster_a_ids[1]],
        description="Core YAML validation utility for deployment configs",
        emoji="✅"
    ),
    make_skill(
        "yaml-lint-helper", "node_c4f9a1b2e3d0", "2024-12-06T11:02:00Z",
        code_b2,
        "Validates and lints YAML configuration files for agent deployment pipelines.",
        dependencies=[cluster_a_ids[2], "skill_yaml_validator_core_placeholder"],
        description="Core YAML validation utility for deployment configs",
        emoji="✅"
    ),
    make_skill(
        "yaml-check-tool", "node_c4f9a1b2e3d0", "2024-12-06T11:05:00Z",
        code_b3,
        "Validates and lints YAML configuration files for agent deployment pipelines.",
        dependencies=["skill_yaml_lint_helper_placeholder", cluster_a_ids[3]],
        description="Core YAML validation utility for deployment configs",
        emoji="✅"
    ),
]

# Fix cross-citation deps to use actual IDs
skills_cluster_b[1]["dependencies"] = [cluster_a_ids[2], skills_cluster_b[0]["skill_id"]]
skills_cluster_b[2]["dependencies"] = [skills_cluster_b[1]["skill_id"], cluster_a_ids[3]]

# ── 3 Genuine clean skills from different publishers ──────────────────────────
code_clean1 = """\
import subprocess
import shlex

def run_shell_command(cmd: str, timeout: int = 30) -> dict:
    args = shlex.split(cmd)
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
"""

code_clean2 = """\
from typing import List, Dict, Any
import statistics

def aggregate_metrics(records: List[Dict[str, Any]], field: str) -> Dict[str, float]:
    values = [r[field] for r in records if field in r and isinstance(r[field], (int, float))]
    if not values:
        return {}
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }
"""

code_clean3 = """\
import re
from urllib.parse import urlparse

def extract_urls(text: str) -> list:
    pattern = r'https?://[^\s<>"\'{}|\\^`\\[\\]]+'
    return re.findall(pattern, text)

def is_safe_url(url: str, allowed_domains: list) -> bool:
    parsed = urlparse(url)
    return any(parsed.netloc.endswith(d) for d in allowed_domains)
"""

skills_clean = [
    make_skill(
        "shell-executor", "node_f7d2c8a0e1b5", "2024-11-20T14:30:00Z",
        code_clean1,
        "Safely executes shell commands with timeout support, returning structured output including stdout, stderr, and return codes.",
        description="Sandboxed shell command runner for agent automation",
        emoji="🖥️"
    ),
    make_skill(
        "metrics-aggregator", "node_a3e6b9f2d4c1", "2024-11-25T10:15:00Z",
        code_clean2,
        "Aggregates numeric metrics from record collections, computing statistical summaries including mean, median, and standard deviation.",
        description="Statistical aggregation utility for monitoring pipelines",
        emoji="📊"
    ),
    make_skill(
        "url-extractor", "node_9b1d4e7c2a5f", "2024-12-01T16:45:00Z",
        code_clean3,
        "Extracts and validates URLs from unstructured text, with domain allowlist enforcement for security-conscious agent workflows.",
        description="URL extraction and validation for content processing",
        emoji="🔗"
    ),
]

# ── 2 SUSPECT skills (same publisher, batch timing, but not quite FARMING) ────
code_suspect1 = """\
def parse_csv_row(row: str, delimiter: str = ',') -> list:
    return [field.strip() for field in row.split(delimiter)]

def normalize_headers(headers: list) -> list:
    return [h.lower().replace(' ', '_') for h in headers]
"""

code_suspect2 = """\
def parse_csv_line(line: str, sep: str = ',') -> list:
    # Split CSV line
    return [col.strip() for col in line.split(sep)]

def normalize_column_names(cols: list) -> list:
    return [c.lower().replace(' ', '_') for c in cols]
"""

skills_suspect = [
    make_skill(
        "csv-row-parser", "node_c4f9a1b2e3d0", "2024-12-07T14:00:00Z",
        code_suspect1,
        "Parses CSV rows and normalizes column headers for downstream data processing.",
        description="Lightweight CSV parsing utility",
        emoji="📋"
    ),
    make_skill(
        "csv-line-reader", "node_c4f9a1b2e3d0", "2024-12-07T14:03:00Z",
        code_suspect2,
        "Parses CSV rows and normalizes column headers for downstream data processing.",
        description="Lightweight CSV parsing utility",
        emoji="📋"
    ),
]

# ── Write all skills to submissions/ ──────────────────────────────────────────
all_skills = skills_cluster_a + skills_cluster_b + skills_clean + skills_suspect

for skill in all_skills:
    fname = workspace / "submissions" / f"{skill['name']}.json"
    with open(fname, "w") as f:
        json.dump(skill, f, indent=2)

# ── Write a manifest ─────────────────────────────────────────────────────────
manifest = {
    "batch_id": "AUDIT-2024-12-NB-007",
    "submitted_by": "trust_safety_team",
    "total_submissions": len(all_skills),
    "submission_window": "2024-11-20 to 2024-12-07",
    "skills": [s["name"] for s in all_skills],
}
with open(workspace / "submissions" / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

# ── Distractor files ──────────────────────────────────────────────────────────

# Publisher registry
for node_id in ["node_c4f9a1b2e3d0", "node_f7d2c8a0e1b5", "node_a3e6b9f2d4c1", "node_9b1d4e7c2a5f"]:
    pub_data = {
        "node_id": node_id,
        "joined": "2024-01-15",
        "verified": True,
        "total_published": random.randint(5, 50),
        "account_flags": [],
    }
    with open(workspace / "registry/publishers" / f"{node_id}.json", "w") as f:
        json.dump(pub_data, f, indent=2)

# Audit log (historical — distracting)
audit_log = [
    {"date": "2024-10-01", "action": "bulk_review", "flagged": 3, "cleared": 12},
    {"date": "2024-11-01", "action": "automated_scan", "flagged": 1, "cleared": 28},
    {"date": "2024-11-15", "action": "manual_review", "flagged": 0, "cleared": 5},
]
with open(workspace / "registry/audit_logs" / "historical_audits.json", "w") as f:
    json.dump(audit_log, f, indent=2)

# Dependency graph snapshot (distractor)
dep_graph = {"edges": [], "nodes": [s["skill_id"] for s in all_skills]}
with open(workspace / "registry/dependency_graph" / "snapshot.json", "w") as f:
    json.dump(dep_graph, f, indent=2)

# Schema file (distractor)
skill_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["skill_id", "name", "publisher", "capsule", "gene"],
    "properties": {
        "skill_id": {"type": "string"},
        "name": {"type": "string"},
        "capsule": {"type": "object"},
        "gene": {"type": "object"},
    }
}
with open(workspace / "submissions/schemas" / "skill_schema.json", "w") as f:
    json.dump(skill_schema, f, indent=2)

# Publisher metadata template (distractor)
pub_template = {
    "template_version": "2.1",
    "required_fields": ["node_id", "alias", "joined", "verified"],
    "optional_fields": ["bio", "website", "social"],
}
with open(workspace / "submissions/metadata" / "publisher_template.json", "w") as f:
    json.dump(pub_template, f, indent=2)

# Trust score history (distractor)
for node_id in ["node_c4f9a1b2e3d0", "node_f7d2c8a0e1b5"]:
    scores = [{"month": f"2024-{i:02d}", "score": round(random.uniform(3.5, 5.0), 2)} for i in range(1, 13)]
    with open(workspace / "internal/trust_scores" / f"{node_id}_history.json", "w") as f:
        json.dump(scores, f, indent=2)

# Old reports archive (distractor, incomplete)
old_report = {
    "report_id": "AUDIT-2024-10-NB-003",
    "status": "archived",
    "findings": "No significant clone activity detected in October batch.",
}
with open(workspace / "internal/reports_archive" / "AUDIT-2024-10-NB-003.json", "w") as f:
    json.dump(old_report, f, indent=2)

# Flagged history (distractor)
flagged = [
    {"skill_name": "old-csv-helper", "flagged_date": "2024-09-10", "reason": "duplicate content", "status": "removed"},
]
with open(workspace / "internal/flagged_history" / "flagged_skills.json", "w") as f:
    json.dump(flagged, f, indent=2)

# Tools placeholder (distractor)
with open(workspace / "tools" / "similarity_notes.txt", "w") as f:
    f.write("Internal notes: Levenshtein distance alone is insufficient for detecting whitespace-injected clones.\n")
    f.write("Normalize source before hashing. Strip comments and blank lines for functional comparison.\n")
    f.write("Cross-citation rings require graph traversal — linear scan misses indirect cycles.\n")

# A stale config (distractor)
stale_cfg = {
    "detector_version": "0.9.1",
    "thresholds": {"similarity_warn": 0.75, "similarity_flag": 0.90},
    "deprecated": True,
    "note": "This config is outdated. Do not use for production scans."
}
with open(workspace / "tools" / "detector_config_DEPRECATED.json", "w") as f:
    json.dump(stale_cfg, f, indent=2)

print("Workspace generated successfully.")
print(f"Total skills: {len(all_skills)}")
print(f"Cluster A (FARMING): {len(skills_cluster_a)} skills")
print(f"Cluster B (FARMING with cross-citation): {len(skills_cluster_b)} skills")
print(f"Clean: {len(skills_clean)} skills")
print(f"Suspect: {len(skills_suspect)} skills")