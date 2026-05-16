#!/usr/bin/env bash
set -euo pipefail

# ── install the skill if not already present ──────────────────────────────────
SKILL_DIR="/workspace/skills/github-actions-workflow-hardening-audit"
SCRIPT_PATH="$SKILL_DIR/scripts/workflow-hardening-audit.sh"

# Clone the skill from the public OpenClaw registry mirror or github
if [ ! -f "$SCRIPT_PATH" ]; then
  echo "[setup] Fetching skill from GitHub..."
  TMP=$(mktemp -d)
  git clone --depth=1 https://github.com/openclaw/skills.git "$TMP/skills" 2>/dev/null || true

  if [ -d "$TMP/skills/github-actions-workflow-hardening-audit" ]; then
    cp -r "$TMP/skills/github-actions-workflow-hardening-audit/." "$SKILL_DIR/"
    echo "[setup] Skill installed from git clone."
  else
    echo "[setup] Git clone did not contain the expected skill directory. Generating minimal working script..."
    mkdir -p "$SKILL_DIR/scripts"

    cat > "$SCRIPT_PATH" << 'SKILLEOF'
#!/usr/bin/env bash
# workflow-hardening-audit.sh — minimal faithful implementation of the SKILL.md contract

set -euo pipefail

WORKFLOW_GLOB="${WORKFLOW_GLOB:-.github/workflows/*.y*ml}"
TOP_N="${TOP_N:-20}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-text}"
WARN_SCORE="${WARN_SCORE:-3}"
CRITICAL_SCORE="${CRITICAL_SCORE:-7}"
REQUIRE_TIMEOUT="${REQUIRE_TIMEOUT:-1}"
REQUIRE_PERMISSIONS="${REQUIRE_PERMISSIONS:-1}"
REQUIRE_CONCURRENCY="${REQUIRE_CONCURRENCY:-0}"
FLAG_FLOATING_REFS="${FLAG_FLOATING_REFS:-1}"
ALLOW_REF_REGEX="${ALLOW_REF_REGEX:-}"
WORKFLOW_FILE_MATCH="${WORKFLOW_FILE_MATCH:-}"
WORKFLOW_FILE_EXCLUDE="${WORKFLOW_FILE_EXCLUDE:-}"
EVENT_MATCH="${EVENT_MATCH:-}"
EVENT_EXCLUDE="${EVENT_EXCLUDE:-}"
FAIL_ON_CRITICAL="${FAIL_ON_CRITICAL:-0}"

python3 - "$WORKFLOW_GLOB" "$TOP_N" "$OUTPUT_FORMAT" "$WARN_SCORE" "$CRITICAL_SCORE" \
          "$REQUIRE_TIMEOUT" "$REQUIRE_PERMISSIONS" "$REQUIRE_CONCURRENCY" \
          "$FLAG_FLOATING_REFS" "$ALLOW_REF_REGEX" \
          "$WORKFLOW_FILE_MATCH" "$WORKFLOW_FILE_EXCLUDE" \
          "$EVENT_MATCH" "$EVENT_EXCLUDE" \
          "$FAIL_ON_CRITICAL" << 'PYEOF'
import sys, glob, json, re, os
import yaml

(workflow_glob, top_n, output_format, warn_score, critical_score,
 require_timeout, require_permissions, require_concurrency,
 flag_floating_refs, allow_ref_regex,
 wf_file_match, wf_file_exclude,
 event_match, event_exclude,
 fail_on_critical) = sys.argv[1:]

top_n = int(top_n)
warn_score = int(warn_score)
critical_score = int(critical_score)
require_timeout = require_timeout == "1"
require_permissions = require_permissions == "1"
require_concurrency = require_concurrency == "1"
flag_floating_refs = flag_floating_refs == "1"
fail_on_critical = fail_on_critical == "1"

FLOATING_PATTERNS = [
    r'@main$', r'@master$', r'@latest$',
    r'@v\d+$',  # major-only tag
]

def is_floating(ref):
    """Return True if the ref after '@' looks floating."""
    if allow_ref_regex:
        if re.search(allow_ref_regex, ref):
            return False
    for pat in FLOATING_PATTERNS:
        if re.search(pat, ref):
            return True
    return False

def extract_events(on_val):
    if isinstance(on_val, str):
        return [on_val]
    if isinstance(on_val, list):
        return on_val
    if isinstance(on_val, dict):
        return list(on_val.keys())
    return []

def audit_workflow(path):
    with open(path) as f:
        try:
            doc = yaml.safe_load(f)
        except Exception as e:
            return {"file": path, "score": 0, "severity": "ok", "issues": [f"parse-error: {e}"], "events": []}

    if not isinstance(doc, dict):
        return {"file": path, "score": 0, "severity": "ok", "issues": [], "events": []}

    events = extract_events(doc.get("on", doc.get(True, {})))
    issues = []
    score = 0

    jobs = doc.get("jobs", {}) or {}
    has_workflow_perms = "permissions" in doc
    has_workflow_concurrency = "concurrency" in doc

    # --- timeout check ---
    if require_timeout:
        for jname, jbody in jobs.items():
            if not isinstance(jbody, dict):
                continue
            if "timeout-minutes" not in jbody:
                issues.append(f"job '{jname}': missing timeout-minutes")
                score += 1

    # --- permissions check ---
    if require_permissions:
        if not has_workflow_perms:
            # check if ALL jobs have permissions
            all_jobs_have_perms = all(
                isinstance(jbody, dict) and "permissions" in jbody
                for jbody in jobs.values()
            ) if jobs else False
            if not all_jobs_have_perms:
                issues.append("missing permissions declaration")
                score += 1

    # --- concurrency check ---
    if require_concurrency:
        if not has_workflow_concurrency:
            all_jobs_have_concurrency = all(
                isinstance(jbody, dict) and "concurrency" in jbody
                for jbody in jobs.values()
            ) if jobs else False
            if not all_jobs_have_concurrency:
                issues.append("missing concurrency declaration")
                score += 1

    # --- floating refs check ---
    if flag_floating_refs:
        for jname, jbody in jobs.items():
            if not isinstance(jbody, dict):
                continue
            for step in (jbody.get("steps") or []):
                if not isinstance(step, dict):
                    continue
                uses = step.get("uses", "")
                if not uses:
                    continue
                if "@" in uses:
                    ref_part = uses.split("@", 1)[1]
                    if is_floating("@" + ref_part):
                        issues.append(f"job '{jname}' step uses floating ref: {uses}")
                        score += 1

    if score >= critical_score:
        severity = "critical"
    elif score >= warn_score:
        severity = "warn"
    else:
        severity = "ok"

    return {"file": path, "score": score, "severity": severity, "issues": issues, "events": events}

# gather files
all_files = sorted(glob.glob(workflow_glob, recursive=True))

# file-path filtering
if wf_file_match:
    all_files = [f for f in all_files if re.search(wf_file_match, f)]
if wf_file_exclude:
    all_files = [f for f in all_files if not re.search(wf_file_exclude, f)]

results = []
for fp in all_files:
    r = audit_workflow(fp)
    # event filtering
    ev_str = ",".join(r["events"])
    if event_match and not re.search(event_match, ev_str):
        continue
    if event_exclude and re.search(event_exclude, ev_str):
        continue
    results.append(r)

results.sort(key=lambda x: -x["score"])
top_results = results[:top_n]

total = len(results)
critical_count = sum(1 for r in results if r["severity"] == "critical")
warn_count = sum(1 for r in results if r["severity"] == "warn")
ok_count = sum(1 for r in results if r["severity"] == "ok")
critical_files = [r for r in results if r["severity"] == "critical"]

if output_format == "json":
    out = {
        "summary": {
            "total": total,
            "critical": critical_count,
            "warn": warn_count,
            "ok": ok_count
        },
        "workflows": top_results,
        "critical_workflows": critical_files
    }
    print(json.dumps(out, indent=2))
else:
    print(f"=== GitHub Actions Hardening Audit ===")
    print(f"Total scanned: {total}  critical={critical_count}  warn={warn_count}  ok={ok_count}")
    print()
    for r in top_results:
        print(f"[{r['severity'].upper():8}] score={r['score']}  {r['file']}")
        for iss in r["issues"]:
            print(f"           - {iss}")
    print()

if fail_on_critical and critical_count > 0:
    sys.exit(1)
sys.exit(0)
PYEOF
SKILLEOF

    chmod +x "$SCRIPT_PATH"
    echo "[setup] Minimal skill script written."
  fi
  rm -rf "$TMP"
fi

chmod +x "$SCRIPT_PATH"

# ensure python3-yaml is available
python3 -c "import yaml" 2>/dev/null || pip3 install pyyaml -q -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "[setup] Environment ready."
echo "[setup] Skill path: $SCRIPT_PATH"
ls -la "$SKILL_DIR/scripts/"