#!/usr/bin/env python3
"""
Generate a realistic sandbox workspace for the PR triage task.
Creates a mock gh CLI binary, a distractor project structure,
and all canned data needed for evaluation.
"""

import json
import os
import stat
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# 1. Distractor project structure (10+ files)
# ─────────────────────────────────────────────
project_dirs = [
    "src/connectors",
    "src/parsers",
    "src/transforms",
    "tests/unit",
    "tests/integration",
    "docs/api",
    "scripts",
    "config",
    ".github/workflows",
    "benchmarks",
]
for d in project_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "src/connectors/postgres.py": "class PostgresConnector:\n    pass\n",
    "src/connectors/mysql.py": "class MySQLConnector:\n    pass\n",
    "src/parsers/csv_parser.py": "def parse_csv(path): pass\n",
    "src/parsers/json_parser.py": "def parse_json(path): pass\n",
    "src/transforms/normalize.py": "def normalize(df): pass\n",
    "src/transforms/filter.py": "def filter_rows(df, cond): pass\n",
    "tests/unit/test_parsers.py": "def test_parse_csv(): assert True\n",
    "tests/integration/test_pipeline.py": "def test_full_pipeline(): assert True\n",
    "docs/api/connectors.md": "# Connectors\n",
    "docs/api/parsers.md": "# Parsers\n",
    "scripts/migrate.sh": "#!/bin/bash\necho migrating\n",
    "config/pipeline.yaml": "version: 1\n",
    ".github/workflows/ci.yml": "name: CI\non: push\n",
    "benchmarks/bench_csv.py": "# benchmarks\n",
    "README_INTERNAL.txt": "Internal notes - do not publish\n",
}
for rel, content in distractor_files.items():
    p = workspace / rel
    p.write_text(content)

# ─────────────────────────────────────────────
# 2. Design the PR dataset
#    Carefully crafted to test ALL proprietary rules
# ─────────────────────────────────────────────
# Dates: "now" = 2024-03-15T12:00:00Z (hardcoded for determinism)
# --days 14  → updatedAt must be >= 2024-03-01T12:00:00Z to be included
# PRs updated before that date are excluded by the agent's filter.

prs = [
    # ── GROUP A: same issue refs → guaranteed score=100 duplicate ──
    {
        "number": 101,
        "title": "Fix CSV parser encoding error on Windows",
        "body": "Fixes #55. The CSV parser crashes when files have BOM markers on Windows systems. This patch adds BOM stripping before parsing.",
        "author": {"login": "alice_dev", "association": "CONTRIBUTOR"},
        "createdAt": "2024-02-10T09:00:00Z",
        "updatedAt": "2024-03-10T10:00:00Z",
        "labels": [{"name": "bug"}],
        "files": [
            {"path": "src/parsers/csv_parser.py"},
            {"path": "tests/unit/test_csv_bom.py"},
        ],
        "additions": 35,
        "deletions": 5,
        "headRefName": "fix/csv-bom-encoding",
    },
    {
        "number": 102,
        "title": "csv parser BOM fix",
        "body": "Closes #55. Quick fix for the BOM issue in csv parser.",
        "author": {"login": "bob_newbie", "association": "FIRST_TIME_CONTRIBUTOR"},
        "createdAt": "2024-02-12T11:00:00Z",
        "updatedAt": "2024-03-11T08:00:00Z",
        "labels": [],
        "files": [
            {"path": "src/parsers/csv_parser.py"},
        ],
        "additions": 8,
        "deletions": 2,
        "headRefName": "bom-fix",
    },
    # ── GROUP B: high file overlap, no same issue → weighted formula ──
    # file_sim = |{postgres.py}| / |{postgres.py, mysql.py, pg_test.py}| = 1/3 ≈ 0.333
    # But let's make it clearly above 75:
    # files overlap: {src/connectors/postgres.py, src/connectors/base.py} / {same + one extra}
    # file_sim = 2/3 ≈ 0.667
    # kw_sim: "add", "postgres", "connector", "retry" shared vs extras
    # Let's engineer: file_sim=0.667, kw_sim=0.75 → score = int(0.667*0.6 + 0.75*0.4)*100 = int(0.4002+0.3)*100 = int(0.7002*100)=70
    # Hmm, need ≥75. Let me engineer more overlap.
    # file_sim = 3/4 = 0.75, kw_sim = 0.8 → score = int((0.75*0.6 + 0.8*0.4)*100) = int((0.45+0.32)*100) = int(77) = 77 ✓
    {
        "number": 201,
        "title": "Add retry logic to Postgres connector",
        "body": "Implements exponential backoff retry for the Postgres connector when connection fails. No issue ref.",
        "author": {"login": "carol_eng", "association": "MEMBER"},
        "createdAt": "2024-02-20T14:00:00Z",
        "updatedAt": "2024-03-12T09:00:00Z",
        "labels": [{"name": "enhancement"}],
        "files": [
            {"path": "src/connectors/postgres.py"},
            {"path": "src/connectors/base_connector.py"},
            {"path": "src/connectors/retry_utils.py"},
            {"path": "tests/unit/test_postgres_retry.py"},
        ],
        "additions": 80,
        "deletions": 10,
        "headRefName": "feature/postgres-retry",
    },
    {
        "number": 202,
        "title": "Postgres connector retry implementation",
        "body": "Adds retry logic with exponential backoff to Postgres connector. Standalone implementation.",
        "author": {"login": "dave_contrib", "association": "CONTRIBUTOR"},
        "createdAt": "2024-02-22T16:00:00Z",
        "updatedAt": "2024-03-13T11:00:00Z",
        "labels": [{"name": "enhancement"}],
        "files": [
            {"path": "src/connectors/postgres.py"},
            {"path": "src/connectors/base_connector.py"},
            {"path": "src/connectors/retry_utils.py"},
            {"path": "src/connectors/pg_pool.py"},
        ],
        "additions": 95,
        "deletions": 5,
        "headRefName": "postgres-retry-v2",
    },
    # ── STALE PR (>30 days no activity, updatedAt old but still within --days 14 would exclude it) ──
    # Actually: stale means updatedAt is old. For --days 14, the agent filters OUT PRs
    # updated before 2024-03-01. But stale PRs in the report are a SEPARATE check
    # (>30 days no activity). Let's include this PR with updatedAt=2024-01-10 so it's
    # filtered by --days 14 and thus NOT fetched. But then we can't show it as stale.
    # 
    # Re-reading SKILL.md: stale = >30 days no activity in the report section.
    # The --days filter is on what PRs to FETCH. So stale PRs that were fetched can
    # still appear in the stale section if their updatedAt is >30 days ago.
    # 
    # Let's include a PR with updatedAt within --days 14 window BUT createdAt long ago,
    # so updatedAt itself shows it was last touched >30 days before "now" (2024-03-15).
    # Actually "recent activity" quality signal: updatedAt within 7 days of report gen.
    # Stale = >30 days no activity = updatedAt > 30 days before now.
    # 
    # So a PR with updatedAt=2024-02-01 is 43 days stale AND within --days 14? No:
    # 2024-03-15 - 14 days = 2024-03-01. So updatedAt=2024-02-01 is NOT within --days 14.
    # 
    # We need the stale PR to pass the --days 14 filter. That's impossible because
    # if it was updated in last 14 days it can't be >30 days stale.
    # 
    # Solution: The agent should use --all flag OR the stale section comes from a broader
    # fetch. But the task will use --days 14. Let's re-read the skill...
    # "If --days specified, filter by updatedAt" - so stale PRs won't appear in a --days 14 run.
    # 
    # Let me change the task to use --days 60 to capture stale PRs, OR use --all.
    # I'll use --all in the mock to simplify, and the task will NOT use --days flag.
    # Actually let me include a stale PR with updatedAt=2024-01-10 (64 days before 2024-03-15)
    # and the task will use --all so the agent fetches everything.
    # 
    # But then the --days filter won't apply. Let me adjust the task:
    # The task uses --all --threshold 75 --top 5 --output triage_report.md
    # This tests: all-PR fetch, threshold filtering, top-N limiting, and stale detection.
    {
        "number": 301,
        "title": "Refactor JSON parser to support streaming",
        "body": "Large refactor of json_parser.py. No issue reference. Waiting on design review.",
        "author": {"login": "eve_senior", "association": "MEMBER"},
        "createdAt": "2023-12-01T10:00:00Z",
        "updatedAt": "2024-01-10T10:00:00Z",  # 64 days before 2024-03-15 → stale
        "labels": [],
        "files": [
            {"path": "src/parsers/json_parser.py"},
            {"path": "src/parsers/stream_parser.py"},
            {"path": "tests/unit/test_json_streaming.py"},
        ],
        "additions": 220,
        "deletions": 45,
        "headRefName": "refactor/json-streaming",
    },
    # ── HIGH QUALITY PR (Grade A candidate) ──
    {
        "number": 401,
        "title": "Add Parquet output format support",
        "body": "Fixes #88. Adds native Parquet file writing support to the pipeline output stage. Includes comprehensive tests and documentation.",
        "author": {"login": "frank_lead", "association": "MEMBER"},
        "createdAt": "2024-03-08T10:00:00Z",
        "updatedAt": "2024-03-14T15:00:00Z",  # 1 day ago → recent
        "labels": [{"name": "feature"}, {"name": "ready-for-review"}],
        "files": [
            {"path": "src/transforms/parquet_writer.py"},
            {"path": "tests/unit/test_parquet_writer.py"},
            {"path": "docs/api/output_formats.md"},
        ],
        "additions": 75,
        "deletions": 5,
        "headRefName": "feature/parquet-output",
    },
    # ── MEDIUM QUALITY PR (Grade B) ──
    {
        "number": 402,
        "title": "Update numpy dependency to 1.26",
        "body": "Closes #90. Bumps numpy from 1.24 to 1.26 for compatibility with Python 3.12.",
        "author": {"login": "grace_contrib", "association": "CONTRIBUTOR"},
        "createdAt": "2024-03-05T09:00:00Z",
        "updatedAt": "2024-03-09T09:00:00Z",  # 6 days ago → recent
        "labels": [{"name": "dependencies"}],
        "files": [
            {"path": "requirements.txt"},
            {"path": "setup.py"},
        ],
        "additions": 4,
        "deletions": 4,
        "headRefName": "deps/bump-numpy",
    },
    # ── LOW QUALITY PR (Grade D) - first-time contributor, no description ──
    {
        "number": 403,
        "title": "typo fix",
        "body": "fix",  # len < 50 → no description bonus
        "author": {"login": "newuser123", "association": "FIRST_TIME_CONTRIBUTOR"},
        "createdAt": "2024-03-14T08:00:00Z",
        "updatedAt": "2024-03-14T08:00:00Z",  # recent
        "labels": [],
        "files": [
            {"path": "docs/api/connectors.md"},
        ],
        "additions": 1,
        "deletions": 1,
        "headRefName": "fix-typo",
    },
]

# ─────────────────────────────────────────────
# 3. Write the mock `gh` binary
# ─────────────────────────────────────────────
# The mock gh script must handle:
#   gh pr list --repo <repo> --state open --limit 500 --json ...
# and return the JSON array above.

pr_json = json.dumps(prs, indent=2)

mock_gh_script = f'''#!/bin/bash
# Mock gh CLI for PR triage evaluation

# Intercept pr list commands
if [[ "$1" == "pr" && "$2" == "list" ]]; then
    cat <<'PRJSON'
{pr_json}
PRJSON
    exit 0
fi

# Intercept pr comment (Phase 6 - should not be called without --action)
if [[ "$1" == "pr" && "$2" == "comment" ]]; then
    echo "Mock: would comment on PR" >&2
    exit 0
fi

# Intercept pr edit
if [[ "$1" == "pr" && "$2" == "edit" ]]; then
    echo "Mock: would edit PR" >&2
    exit 0
fi

echo "Mock gh: unhandled command: $@" >&2
exit 0
'''

mock_gh_path = workspace / "gh"
mock_gh_path.write_text(mock_gh_script)
mock_gh_path.chmod(mock_gh_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# Also store the PR data as a reference file for the eval script
(workspace / ".eval_data" ).mkdir(exist_ok=True)
(workspace / ".eval_data" / "pr_data.json").write_text(json.dumps(prs, indent=2))

# Store ground truth calculations for eval
# We compute expected values here deterministically

def extract_keywords(text):
    import re
    text = text.lower()
    # Remove punctuation
    text = re.sub(r'[^\w\s#]', ' ', text)
    words = text.split()
    stopwords = {'the','a','an','is','it','in','on','for','to','of','and','or','with',
                 'this','that','are','was','be','by','as','at','from','has','have',
                 'been','will','can','not','fix','fixes','add','adds','update','updates',
                 'no','if','when','files','file','include','includes'}
    keywords = [w for w in words if w not in stopwords and len(w) > 2 and not w.startswith('#')]
    return list(set(keywords))

def extract_issue_refs(body):
    import re
    return list(set(re.findall(r'(?:fixes|closes|fix|close)\s+#(\d+)', body.lower())))

def file_similarity(f1, f2):
    s1, s2 = set(f1), set(f2)
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)

def keyword_similarity(k1, k2):
    s1, s2 = set(k1), set(k2)
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)

def same_issue(r1, r2):
    return bool(set(r1) & set(r2))

def similarity_score(pr1_intent, pr2_intent):
    if same_issue(pr1_intent['issue_refs'], pr2_intent['issue_refs']):
        return 100
    fs = file_similarity(pr1_intent['files'], pr2_intent['files'])
    ks = keyword_similarity(pr1_intent['keywords'], pr2_intent['keywords'])
    return int((fs * 0.6 + ks * 0.4) * 100)

from datetime import datetime, timezone

NOW = datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
SEVEN_DAYS = 7 * 24 * 3600

def quality_score(pr):
    score = 0
    body = pr.get('body', '')
    if len(body) > 50:
        score += 10
    if any(r in body.lower() for r in ['fixes #', 'closes #', 'fix #', 'close #']):
        score += 15
    test_patterns = ['test_', '.test.ts', '.spec.ts', '_test.py', 'test_', '.test.js']
    file_paths = [f['path'] for f in pr.get('files', [])]
    if any(any(pat in fp for pat in test_patterns) for fp in file_paths):
        score += 20
    total_lines = pr.get('additions', 0) + pr.get('deletions', 0)
    if total_lines < 100:
        score += 10
    if len(pr.get('labels', [])) > 0:
        score += 5
    updated_at = datetime.fromisoformat(pr['updatedAt'].replace('Z', '+00:00'))
    if (NOW - updated_at).total_seconds() <= SEVEN_DAYS:
        score += 10
    assoc = pr['author'].get('association', '')
    if assoc == 'FIRST_TIME_CONTRIBUTOR':
        score -= 5
    return score

def quality_grade(score):
    if score >= 60:
        return 'A'
    elif score >= 40:
        return 'B'
    elif score >= 20:
        return 'C'
    else:
        return 'D'

# Compute intents
intents = []
for pr in prs:
    files = [f['path'] for f in pr.get('files', [])]
    kws = extract_keywords(pr['title'] + ' ' + pr['body'])
    refs = extract_issue_refs(pr['body'])
    intents.append({
        'number': pr['number'],
        'files': files,
        'keywords': kws,
        'issue_refs': refs,
    })

# Compute pairwise similarity
pairs = []
for i in range(len(intents)):
    for j in range(i+1, len(intents)):
        score = similarity_score(intents[i], intents[j])
        pairs.append((intents[i]['number'], intents[j]['number'], score))

# Compute quality scores
quality_scores = {}
for pr in prs:
    qs = quality_score(pr)
    quality_scores[pr['number']] = {
        'score': qs,
        'grade': quality_grade(qs),
    }

# Stale PRs: updatedAt > 30 days before NOW
stale_prs = []
for pr in prs:
    updated_at = datetime.fromisoformat(pr['updatedAt'].replace('Z', '+00:00'))
    days_stale = (NOW - updated_at).total_seconds() / 86400
    if days_stale > 30:
        stale_prs.append(pr['number'])

ground_truth = {
    'pairs': pairs,
    'quality_scores': quality_scores,
    'stale_prs': stale_prs,
    'threshold': 75,
    'top_n': 5,
    'repo': 'dataflow-org/etl-pipeline',
}

(workspace / ".eval_data" / "ground_truth.json").write_text(json.dumps(ground_truth, indent=2))

print("Workspace generated successfully.")
print(f"PRs: {len(prs)}")
print(f"Ground truth pairs: {pairs}")
print(f"Quality scores: {quality_scores}")
print(f"Stale PRs: {stale_prs}")