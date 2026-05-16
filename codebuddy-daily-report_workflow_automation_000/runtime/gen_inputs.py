import os
import json
import random
import stat
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Compute target date (前天 = day-before-yesterday) ──────────────────────
today = datetime.now().date()
target_date = today - timedelta(days=2)
target_date_str = target_date.strftime("%Y-%m-%d")

# ── 1. Create the skill directory structure ───────────────────────────────
skill_dir = Path.home() / ".codebuddy" / "skills" / "daily-report"
scripts_dir = skill_dir / "scripts"
references_dir = skill_dir / "references"
scripts_dir.mkdir(parents=True, exist_ok=True)
references_dir.mkdir(parents=True, exist_ok=True)

# ── 2. Write the mock collect.py ──────────────────────────────────────────
collect_script = scripts_dir / "collect.py"

mock_json_days_ago_2 = {
    "date": target_date_str,
    "system": "Linux",
    "git_author": "Li Wei",
    "repos": [
        {
            "path": "/home/liwei/projects/payment-gateway",
            "name": "payment-gateway",
            "commits": [
                {
                    "hash": "f3a9c12",
                    "message": "feat: implement idempotency key validation",
                    "branch": "feature/idempotency",
                    "time": f"{target_date_str} 09:15:00"
                },
                {
                    "hash": "b7d4e55",
                    "message": "fix: handle duplicate transaction edge case",
                    "branch": "feature/idempotency",
                    "time": f"{target_date_str} 11:42:00"
                },
                {
                    "hash": "c1f8a33",
                    "message": "test: add unit tests for idempotency service",
                    "branch": "feature/idempotency",
                    "time": f"{target_date_str} 14:07:00"
                }
            ],
            "diff_stats": "+287 -45 across 12 files"
        },
        {
            "path": "/home/liwei/projects/risk-engine",
            "name": "risk-engine",
            "commits": [
                {
                    "hash": "9e2b1d7",
                    "message": "refactor: extract fraud-detection rule engine",
                    "branch": "main",
                    "time": f"{target_date_str} 15:30:00"
                },
                {
                    "hash": "a4c7f02",
                    "message": "docs: update API contract for risk scoring endpoint",
                    "branch": "main",
                    "time": f"{target_date_str} 16:55:00"
                }
            ],
            "diff_stats": "+134 -78 across 7 files"
        }
    ],
    "agent_sessions": [
        {
            "session_id": "sess_7f3a9b",
            "overview_content": "Worked on implementing idempotency key validation for the payment gateway service. The agent helped design the Redis-based deduplication cache, reviewed transaction hashing strategies, and generated comprehensive unit tests covering race conditions and TTL expiry scenarios.",
            "modified_time": f"{target_date_str} 14:30:00"
        },
        {
            "session_id": "sess_2c8d1e",
            "overview_content": "Assisted with refactoring the fraud detection rule engine in risk-engine service. Discussed extracting business rules into a configurable DSL, reviewed the new scoring algorithm, and helped write the updated API contract documentation.",
            "modified_time": f"{target_date_str} 17:10:00"
        }
    ],
    "errors": []
}

mock_json_empty = {
    "date": today.strftime("%Y-%m-%d"),
    "system": "Linux",
    "git_author": "Li Wei",
    "repos": [],
    "agent_sessions": [],
    "errors": []
}

mock_json_yesterday = {
    "date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
    "system": "Linux",
    "git_author": "Li Wei",
    "repos": [],
    "agent_sessions": [],
    "errors": []
}

# Serialize JSON data to strings for embedding in the generated script
json_days_ago_2_str = json.dumps(mock_json_days_ago_2, ensure_ascii=False, indent=2)
json_yesterday_str = json.dumps(mock_json_yesterday, ensure_ascii=False, indent=2)
json_empty_str = json.dumps(mock_json_empty, ensure_ascii=False, indent=2)

collect_py_content = f'''#!/usr/bin/env python3
"""Mock collect.py for daily-report skill - deterministic test fixture."""
import json
import sys
import argparse
from datetime import datetime, timedelta

DATA_DAYS_AGO_2 = {repr(json_days_ago_2_str)}
DATA_YESTERDAY = {repr(json_yesterday_str)}
DATA_EMPTY = {repr(json_empty_str)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yesterday", action="store_true")
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--days-ago", type=int, default=0)
    args = parser.parse_args()

    if args.days_ago == 2 or args.date == "{target_date_str}":
        data = DATA_DAYS_AGO_2
    elif args.yesterday or args.days_ago == 1:
        data = DATA_YESTERDAY
    elif args.days_ago > 0:
        data = DATA_EMPTY
    else:
        data = DATA_EMPTY

    print(data)

if __name__ == "__main__":
    main()
'''

collect_script.write_text(collect_py_content, encoding="utf-8")
collect_script.chmod(collect_script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── 3. Write a references/config.yaml (present but not critical) ──────────
config_yaml = references_dir / "config.yaml"
config_yaml.write_text("""# Daily Report Config
extra_search_dirs:
  - ~/projects
  - ~/work
language: zh
""", encoding="utf-8")

# ── 4. Create distractor files in workspace ───────────────────────────────
old_date1 = (today - timedelta(days=10)).strftime("%Y-%m-%d")
old_date2 = (today - timedelta(days=5)).strftime("%Y-%m-%d")

reports_dir = workspace / "reports"
reports_dir.mkdir(exist_ok=True)

(reports_dir / f"daily-report-{old_date1}.md").write_text(f"""# 工作日报 - {old_date1}

## 📊 今日概览
- 活跃仓库: 1 个
- 总提交数: 2 次

## 🔧 项目详情
### legacy-app
**分支**: main

| 时间 | 提交说明 |
|------|---------|
| 10:00 | chore: update dependencies |

## 📝 今日总结
日常维护工作。
""", encoding="utf-8")

(reports_dir / f"daily-report-{old_date2}.md").write_text(f"""# 工作日报 - {old_date2}

## 📊 今日概览  
- 活跃仓库: 0 个
- 总提交数: 0 次

## 📝 今日总结
无提交记录。
""", encoding="utf-8")

projects_dir = workspace / "projects"
(projects_dir / "payment-gateway" / "src").mkdir(parents=True, exist_ok=True)
(projects_dir / "payment-gateway" / "src" / "idempotency.py").write_text(
    "# idempotency service placeholder\n", encoding="utf-8"
)
(projects_dir / "payment-gateway" / "src" / "transaction.py").write_text(
    "# transaction processor\n", encoding="utf-8"
)
(projects_dir / "payment-gateway" / "tests").mkdir(parents=True, exist_ok=True)
(projects_dir / "payment-gateway" / "tests" / "__init__.py").write_text("", encoding="utf-8")
(projects_dir / "payment-gateway" / "tests" / "test_idempotency.py").write_text(
    "# unit tests\n", encoding="utf-8"
)
(projects_dir / "risk-engine" / "src").mkdir(parents=True, exist_ok=True)
(projects_dir / "risk-engine" / "src" / "rules.py").write_text(
    "# rule engine\n", encoding="utf-8"
)
(projects_dir / "risk-engine" / "src" / "scoring.py").write_text(
    "# scoring algorithm\n", encoding="utf-8"
)

scripts_dir2 = workspace / "scripts"
scripts_dir2.mkdir(exist_ok=True)
(scripts_dir2 / "generate_report.sh").write_text(
    "#!/bin/bash\n# This is a stub script, not the real tool.\necho 'Not implemented'\n",
    encoding="utf-8"
)
(scripts_dir2 / "collect_data.py").write_text(
    "# Wrong script - this is not collect.py from the skill\nprint('{}')  \n",
    encoding="utf-8"
)

(workspace / "config.json").write_text(
    json.dumps({"project": "fintech-suite", "version": "2.1.0", "author": "Li Wei"}),
    encoding="utf-8"
)
(workspace / ".gitconfig").write_text(
    "[user]\n    name = Li Wei\n    email = dev@fintech-corp.com\n",
    encoding="utf-8"
)
(workspace / "notes.txt").write_text(
    "TODO: remember to generate the 前天 daily report for the sprint retrospective!\n"
    "The team standup is tomorrow morning.\n",
    encoding="utf-8"
)

(workspace / ".task_meta.json").write_text(
    json.dumps({"target_date": target_date_str, "skill_dir": str(skill_dir)}),
    encoding="utf-8"
)

print(f"[gen_inputs] Workspace initialized. Target date (前天): {target_date_str}")
print(f"[gen_inputs] Skill dir: {skill_dir}")
print(f"[gen_inputs] Mock collect.py written to: {collect_script}")