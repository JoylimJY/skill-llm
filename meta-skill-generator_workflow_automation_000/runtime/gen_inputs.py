#!/usr/bin/env python3
"""
Generate the workspace: a realistic meta-skill-generator project with
existing scripts, messy databases, and multiple skills to audit.
"""
import json
import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# Create directory structure
os.makedirs(f"{WORKSPACE}/meta-skill-generator/scripts", exist_ok=True)
os.makedirs(f"{WORKSPACE}/meta-skill-generator/generated", exist_ok=True)

# --- Create SKILL.md ---
skill_md = """---
name: meta-skill-generator
description: |
  AI 技能自动生成框架。用于自动扫描、注册、检索、生成、评估、测试、优化技能。
  
  触发场景：
  1. 用户要求创建"技能工厂"
  2. 需要检索/生成/评估技能
  3. 需要测试/优化技能代码
  
  状态：核心功能已完成

  ⚠️ 注意：首次使用需运行 `python scripts/embed_skill.py` 重建向量搜索库
metadata: {"openclaw":{"emoji":"🛠️"}}
---

# Meta-Skill Generator

> AI 技能自动生成框架 - 完整版

## 已实现功能

| 功能 | 脚本 | 状态 |
|------|------|------|
| 扫描 | scan_skills.py | ✅ 24个技能 |
| 存储 | simple_db.py | ✅ JSON |
| 搜索 | scan_skills.py | ✅ 关键词 |
| 生成 | generate_skill.py | ✅ SKILL.md |
| 评分 | evaluator.py | ✅ 5维度 |
| 测试 | sandbox.py | ✅ 沙盒 |
| 优化 | optimizer.py | ✅ 自动 |

## 流程图

```
用户需求 → 扫描现有 → 匹配/生成 → 测试 → 评分 → 优化 → 完成
              ↓
         如果已有相似技能，直接复用
```

## 评分公式

```
Score = 0.4×SR + 0.2×Sp + 0.2×R + 0.2×Q
```

- SR: 测试成功率
- Sp: 速度
- R: 鲁棒性
- Q: 代码质量

## 优化策略

| 策略 | 说明 |
|------|------|
| rewrite | 保留逻辑，添加异常处理 |
| compress | 简化代码，移除冗余 |

## 优化建议

- 添加异常处理
- 添加输入验证
- 拆分过长的函数
- 添加类型提示
- 添加文档字符串

## 当前评分

| 技能 | 评分 |
|------|------|
| truthfulness | 0.65 |
| skill-manager | 0.64 |

## 文件结构

```
meta-skill-generator/
├── SKILL.md
├── skills_db.json
├── scores_db.json
├── optimize_db.json
├── scripts/
│   ├── scan_skills.py
│   ├── simple_db.py
│   ├── generate_skill.py
│   ├── evaluator.py
│   ├── sandbox.py
│   └── optimizer.py
└── generated/
```

---

**框架已完成！** 🦞
"""

with open(f"{WORKSPACE}/meta-skill-generator/SKILL.md", "w") as f:
    f.write(skill_md)

# --- Create scripts/scan_skills.py ---
scan_skills_py = '''#!/usr/bin/env python3
"""
scan_skills.py - Scan directories for SKILL.md files and register them.
Usage: python scan_skills.py <scan_dir> [--db <db_path>]
"""
import os
import sys
import json
import re
import argparse

def parse_skill_md(filepath):
    """Parse a SKILL.md file and extract metadata."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract frontmatter
    fm_match = re.search(r'^---\\n(.*?)\\n---', content, re.DOTALL)
    meta = {}
    if fm_match:
        fm = fm_match.group(1)
        name_match = re.search(r'name:\\s*(.+)', fm)
        desc_match = re.search(r'description:\\s*\\|?\\n?\\s*(.+)', fm)
        if name_match:
            meta['name'] = name_match.group(1).strip()
        if desc_match:
            meta['description'] = desc_match.group(1).strip()
    
    meta['path'] = filepath
    meta['status'] = 'scanned'
    return meta

def scan_directory(scan_dir):
    """Recursively scan for SKILL.md files."""
    skills = []
    for root, dirs, files in os.walk(scan_dir):
        for f in files:
            if f == 'SKILL.md':
                full = os.path.join(root, f)
                try:
                    skill = parse_skill_md(full)
                    skills.append(skill)
                except Exception as e:
                    print(f"[WARN] Failed to parse {full}: {e}", file=sys.stderr)
    return skills

def search_skills(skills, keyword):
    """Search skills by keyword in name or description."""
    results = []
    kw = keyword.lower()
    for s in skills:
        if kw in s.get('name', '').lower() or kw in s.get('description', '').lower():
            results.append(s)
    return results

def main():
    parser = argparse.ArgumentParser(description='Scan skills')
    parser.add_argument('scan_dir', help='Directory to scan')
    parser.add_argument('--db', default='skills_db.json', help='Database file path')
    parser.add_argument('--search', default=None, help='Search keyword')
    args = parser.parse_args()
    
    skills = scan_directory(args.scan_dir)
    
    if args.search:
        skills = search_skills(skills, args.search)
        print(json.dumps(skills, indent=2, ensure_ascii=False))
        return
    
    # Save to db
    db_path = args.db
    existing = []
    if os.path.exists(db_path):
        with open(db_path, 'r') as f:
            existing = json.load(f)
    
    # Merge: update existing by name, add new
    name_map = {s['name']: s for s in existing if 'name' in s}
    for s in skills:
        if 'name' in s:
            name_map[s['name']] = s
    
    merged = list(name_map.values())
    with open(db_path, 'w') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Scanned {len(skills)} skills, DB has {len(merged)} total.")

if __name__ == '__main__':
    main()
'''

with open(f"{WORKSPACE}/meta-skill-generator/scripts/scan_skills.py", "w") as f:
    f.write(scan_skills_py)

# --- Create scripts/simple_db.py ---
simple_db_py = '''#!/usr/bin/env python3
"""
simple_db.py - Simple JSON database operations.
Usage: python simple_db.py <action> <db_path> [--key <key>] [--value <json_value>]
Actions: list, get, set, delete
"""
import json
import sys
import argparse

def load_db(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_db(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description='Simple DB')
    parser.add_argument('action', choices=['list', 'get', 'set', 'delete'])
    parser.add_argument('db_path', help='Path to JSON db file')
    parser.add_argument('--key', default=None)
    parser.add_argument('--value', default=None)
    args = parser.parse_args()
    
    data = load_db(args.db_path)
    
    if args.action == 'list':
        if isinstance(data, list):
            for i, item in enumerate(data):
                print(f"[{i}] {json.dumps(item, ensure_ascii=False)}")
        elif isinstance(data, dict):
            for k, v in data.items():
                print(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    elif args.action == 'get':
        if args.key and isinstance(data, dict):
            print(json.dumps(data.get(args.key), indent=2, ensure_ascii=False))
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))
    elif args.action == 'set':
        if args.key and args.value:
            if isinstance(data, dict):
                data[args.key] = json.loads(args.value)
            elif isinstance(data, list):
                data.append(json.loads(args.value))
            save_db(args.db_path, data)
            print(f"[OK] Set {args.key}")
    elif args.action == 'delete':
        if args.key and isinstance(data, dict):
            data.pop(args.key, None)
            save_db(args.db_path, data)
            print(f"[OK] Deleted {args.key}")
    
if __name__ == '__main__':
    main()
'''

with open(f"{WORKSPACE}/meta-skill-generator/scripts/simple_db.py", "w") as f:
    f.write(simple_db_py)

# --- Create scripts/generate_skill.py ---
generate_skill_py = '''#!/usr/bin/env python3
"""
generate_skill.py - Generate a new SKILL.md from a name and description.
Usage: python generate_skill.py <name> <description> [--output <dir>]
"""
import os
import sys
import argparse

TEMPLATE = """---
name: {name}
description: |
  {description}
metadata: {{"openclaw": {{"emoji": "🔧"}}}}
---

# {title}

> {description}

## 功能

- 核心功能已实现

## 文件结构

```
{name}/
├── SKILL.md
└── scripts/
```
"""

def generate(name, description, output_dir='generated'):
    os.makedirs(output_dir, exist_ok=True)
    skill_dir = os.path.join(output_dir, name)
    os.makedirs(skill_dir, exist_ok=True)
    
    title = name.replace('-', ' ').title()
    content = TEMPLATE.format(name=name, description=description, title=title)
    
    path = os.path.join(skill_dir, 'SKILL.md')
    with open(path, 'w') as f:
        f.write(content)
    
    print(f"[OK] Generated {path}")
    return path

def main():
    parser = argparse.ArgumentParser(description='Generate skill')
    parser.add_argument('name', help='Skill name')
    parser.add_argument('description', help='Skill description')
    parser.add_argument('--output', default='generated', help='Output directory')
    args = parser.parse_args()
    
    generate(args.name, args.description, args.output)

if __name__ == '__main__':
    main()
'''

with open(f"{WORKSPACE}/meta-skill-generator/scripts/generate_skill.py", "w") as f:
    f.write(generate_skill_py)

# --- Create scripts/evaluator.py ---
evaluator_py = '''#!/usr/bin/env python3
"""
evaluator.py - Evaluate a skill on 5 dimensions and compute weighted score.
Usage: python evaluator.py <skill_name> [--sr <float>] [--sp <float>] [--r <float>] [--q <float>] [--db <path>]

Score = 0.4*SR + 0.2*Sp + 0.2*R + 0.2*Q

Dimensions:
  SR: 测试成功率 (test success rate) 0.0-1.0
  Sp: 速度 (speed) 0.0-1.0
  R:  鲁棒性 (robustness) 0.0-1.0
  Q:  代码质量 (code quality) 0.0-1.0
"""
import json
import sys
import argparse
import os

def compute_score(sr, sp, r, q):
    """Compute weighted score using the official formula."""
    return round(0.4 * sr + 0.2 * sp + 0.2 * r + 0.2 * q, 4)

def evaluate(skill_name, sr, sp, r, q, db_path='scores_db.json'):
    score = compute_score(sr, sp, r, q)
    
    record = {
        'name': skill_name,
        'dimensions': {
            'SR': sr,
            'Sp': sp,
            'R': r,
            'Q': q
        },
        'score': score,
        'formula': '0.4*SR + 0.2*Sp + 0.2*R + 0.2*Q'
    }
    
    # Load existing
    db = {}
    if os.path.exists(db_path):
        with open(db_path, 'r') as f:
            db = json.load(f)
    
    db[skill_name] = record
    
    with open(db_path, 'w') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    
    print(f"[EVAL] {skill_name}: SR={sr}, Sp={sp}, R={r}, Q={q} => Score={score}")
    return record

def main():
    parser = argparse.ArgumentParser(description='Evaluate skill')
    parser.add_argument('skill_name', help='Name of skill')
    parser.add_argument('--sr', type=float, required=True, help='Test success rate')
    parser.add_argument('--sp', type=float, required=True, help='Speed')
    parser.add_argument('--r', type=float, required=True, help='Robustness')
    parser.add_argument('--q', type=float, required=True, help='Code quality')
    parser.add_argument('--db', default='scores_db.json', help='Scores DB path')
    args = parser.parse_args()
    
    evaluate(args.skill_name, args.sr, args.sp, args.r, args.q, args.db)

if __name__ == '__main__':
    main()
'''

with open(f"{WORKSPACE}/meta-skill-generator/scripts/evaluator.py", "w") as f:
    f.write(evaluator_py)

# --- Create scripts/sandbox.py ---
sandbox_py = '''#!/usr/bin/env python3
"""
sandbox.py - Run skill tests in a sandboxed environment.
Usage: python sandbox.py <skill_name> [--skills-db <path>]

Returns test results as JSON to stdout.
"""
import json
import sys
import os
import argparse
import subprocess
import random

random.seed(12345)

def run_tests(skill_name, skills_db_path='skills_db.json'):
    """Simulate running tests for a skill."""
    # Load skills db to verify skill exists
    skills = []
    if os.path.exists(skills_db_path):
        with open(skills_db_path, 'r') as f:
            skills = json.load(f)
    
    found = None
    for s in skills:
        if s.get('name') == skill_name:
            found = s
            break
    
    if not found:
        print(json.dumps({'error': f'Skill {skill_name} not found in DB'}))
        sys.exit(1)
    
    # Simulate test results based on skill properties
    # Use deterministic "random" based on skill name hash
    h = hash(skill_name) % 1000
    sr = round(min(1.0, max(0.0, (h % 100) / 100.0)), 2)
    sp = round(min(1.0, max(0.0, ((h * 7) % 100) / 100.0)), 2)
    r = round(min(1.0, max(0.0, ((h * 13) % 100) / 100.0)), 2)
    q = round(min(1.0, max(0.0, ((h * 19) % 100) / 100.0)), 2)
    
    result = {
        'skill': skill_name,
        'tests_run': 10,
        'tests_passed': int(sr * 10),
        'metrics': {
            'SR': sr,
            'Sp': sp,
            'R': r,
            'Q': q
        },
        'status': 'completed'
    }
    
    print(json.dumps(result, indent=2))
    return result

def main():
    parser = argparse.ArgumentParser(description='Sandbox test runner')
    parser.add_argument('skill_name', help='Skill to test')
    parser.add_argument('--skills-db', default='skills_db.json', help='Skills DB path')
    args = parser.parse_args()
    
    run_tests(args.skill_name, args.skills_db)

if __name__ == '__main__':
    main()
'''

with open(f"{WORKSPACE}/meta-skill-generator/scripts/sandbox.py", "w") as f:
    f.write(sandbox_py)

# --- Create scripts/optimizer.py ---
optimizer_py = '''#!/usr/bin/env python3
"""
optimizer.py - Optimize skills based on evaluation scores.
Usage: python optimizer.py <skill_name> --strategy <rewrite|compress> [--scores-db <path>] [--optimize-db <path>]

Strategies:
  rewrite  - Preserve logic, add exception handling, input validation, docstrings
  compress - Simplify code, remove redundancy, add type hints

A skill should be optimized if its score < 0.7
After optimization, the optimizer records the action and suggests re-evaluation.
"""
import json
import sys
import os
import argparse

OPTIMIZATION_TIPS = {
    'rewrite': [
        '添加异常处理 (try/except)',
        '添加输入验证',
        '添加文档字符串',
        '拆分过长的函数'
    ],
    'compress': [
        '简化代码',
        '移除冗余导入',
        '添加类型提示',
        '合并重复逻辑'
    ]
}

def optimize(skill_name, strategy, scores_db_path='scores_db.json', optimize_db_path='optimize_db.json'):
    if strategy not in ('rewrite', 'compress'):
        print(f"[ERROR] Unknown strategy: {strategy}. Use 'rewrite' or 'compress'.")
        sys.exit(1)
    
    # Load scores
    scores = {}
    if os.path.exists(scores_db_path):
        with open(scores_db_path, 'r') as f:
            scores = json.load(f)
    
    skill_score = scores.get(skill_name, {})
    current_score = skill_score.get('score', 0.0)
    
    if current_score >= 0.7:
        print(f"[SKIP] {skill_name} score={current_score} >= 0.7, no optimization needed.")
        return None
    
    # Record optimization
    tips = OPTIMIZATION_TIPS.get(strategy, [])
    
    # Simulate score improvement
    improved_dims = skill_score.get('dimensions', {'SR': 0.5, 'Sp': 0.5, 'R': 0.5, 'Q': 0.5})
    if strategy == 'rewrite':
        improved_dims['R'] = min(1.0, round(improved_dims.get('R', 0.5) + 0.15, 2))
        improved_dims['Q'] = min(1.0, round(improved_dims.get('Q', 0.5) + 0.10, 2))
    elif strategy == 'compress':
        improved_dims['Sp'] = min(1.0, round(improved_dims.get('Sp', 0.5) + 0.15, 2))
        improved_dims['Q'] = min(1.0, round(improved_dims.get('Q', 0.5) + 0.10, 2))
    
    new_score = round(0.4 * improved_dims['SR'] + 0.2 * improved_dims['Sp'] + 0.2 * improved_dims['R'] + 0.2 * improved_dims['Q'], 4)
    
    record = {
        'skill': skill_name,
        'strategy': strategy,
        'original_score': current_score,
        'optimized_score': new_score,
        'improved_dimensions': improved_dims,
        'tips_applied': tips,
        'status': 'optimized'
    }
    
    # Save to optimize db
    opt_db = {}
    if os.path.exists(optimize_db_path):
        with open(optimize_db_path, 'r') as f:
            opt_db = json.load(f)
    
    opt_db[skill_name] = record
    
    with open(optimize_db_path, 'w') as f:
        json.dump(opt_db, f, indent=2, ensure_ascii=False)
    
    print(f"[OPT] {skill_name}: {strategy} applied. Score: {current_score} -> {new_score}")
    print(f"[OPT] Tips: {tips}")
    return record

def main():
    parser = argparse.ArgumentParser(description='Optimize skill')
    parser.add_argument('skill_name', help='Skill to optimize')
    parser.add_argument('--strategy', required=True, choices=['rewrite', 'compress'])
    parser.add_argument('--scores-db', default='scores_db.json')
    parser.add_argument('--optimize-db', default='optimize_db.json')
    args = parser.parse_args()
    
    optimize(args.skill_name, args.strategy, args.scores_db, args.optimize_db)

if __name__ == '__main__':
    main()
'''

with open(f"{WORKSPACE}/meta-skill-generator/scripts/optimizer.py", "w") as f:
    f.write(optimizer_py)

# --- Create existing messy/incomplete databases ---

# A partially populated skills_db.json with stale entries
stale_skills_db = [
    {"name": "old-deprecated-skill", "path": "/nonexistent/path/SKILL.md", "status": "scanned"},
    {"name": "truthfulness", "path": "/old/truthfulness/SKILL.md", "status": "scanned", "description": "Outdated entry"}
]
with open(f"{WORKSPACE}/meta-skill-generator/skills_db.json", "w") as f:
    json.dump(stale_skills_db, f, indent=2)

# An outdated scores_db.json with partial entries
old_scores = {
    "truthfulness": {
        "name": "truthfulness",
        "dimensions": {"SR": 0.7, "Sp": 0.5, "R": 0.6, "Q": 0.7},
        "score": 0.65,
        "formula": "0.4*SR + 0.2*Sp + 0.2*R + 0.2*Q"
    },
    "skill-manager": {
        "name": "skill-manager",
        "dimensions": {"SR": 0.6, "Sp": 0.7, "R": 0.5, "Q": 0.8},
        "score": 0.64,
        "formula": "0.4*SR + 0.2*Sp + 0.2*R + 0.2*Q"
    }
}
with open(f"{WORKSPACE}/meta-skill-generator/scores_db.json", "w") as f:
    json.dump(old_scores, f, indent=2)

# Empty optimize_db.json
with open(f"{WORKSPACE}/meta-skill-generator/optimize_db.json", "w") as f:
    json.dump({}, f)

# --- Create a set of skill directories to be scanned (simulating real repo) ---
# These are scattered around to test the scan functionality

skills_to_create = [
    {
        "dir": "skills-library/data-validator",
        "name": "data-validator",
        "desc": "Validates incoming data against schemas and business rules."
    },
    {
        "dir": "skills-library/code-reviewer",
        "name": "code-reviewer", 
        "desc": "Automated code review and quality assessment tool."
    },
    {
        "dir": "skills-library/report-builder",
        "name": "report-builder",
        "desc": "Generates formatted reports from structured data sources."
    },
    {
        "dir": "skills-library/log-analyzer",
        "name": "log-analyzer",
        "desc": "Analyzes application logs to detect anomalies and patterns."
    },
    {
        "dir": "skills-library/api-tester",
        "name": "api-tester",
        "desc": "Tests REST API endpoints for correctness and performance."
    },
]

for skill in skills_to_create:
    dirpath = f"{WORKSPACE}/meta-skill-generator/{skill['dir']}"
    os.makedirs(dirpath, exist_ok=True)
    content = f"""---
name: {skill['name']}
description: |
  {skill['desc']}
metadata: {{"openclaw": {{"emoji": "🔧"}}}}
---

# {skill['name'].replace('-', ' ').title()}

> {skill['desc']}
"""
    with open(f"{dirpath}/SKILL.md", "w") as f:
        f.write(content)

# --- Create distractor files ---
distractors = [
    "meta-skill-generator/notes/meeting_2024_01.txt",
    "meta-skill-generator/notes/architecture_draft.md",
    "meta-skill-generator/backups/old_skills_db.json.bak",
    "meta-skill-generator/backups/config_v1.yaml",
    "meta-skill-generator/tmp/debug_output.log",
    "meta-skill-generator/tmp/test_results_old.json",
    "meta-skill-generator/docs/api_reference.md",
    "meta-skill-generator/docs/deployment_guide.txt",
    "meta-skill-generator/ci/pipeline.yml",
    "meta-skill-generator/ci/test_runner.sh",
    "meta-skill-generator/.env.example",
    "meta-skill-generator/requirements.txt",
]

for d in distractors:
    full = f"{WORKSPACE}/{d}"
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        if d.endswith(".json.bak"):
            json.dump({"old": "backup", "stale": True}, f)
        elif d.endswith(".yaml") or d.endswith(".yml"):
            f.write("# placeholder config\nversion: 1\n")
        elif d.endswith(".txt") or d.endswith(".md"):
            f.write(f"# {os.path.basename(d)}\nThis is a distractor file.\n")
        elif d.endswith(".log"):
            f.write("[2024-01-01] DEBUG: old debug output\n" * 5)
        elif d.endswith(".sh"):
            f.write("#!/bin/bash\necho 'test'\n")
        elif d.endswith(".example"):
            f.write("API_KEY=placeholder\nDB_URL=localhost\n")
        else:
            f.write("placeholder\n")

# requirements.txt
with open(f"{WORKSPACE}/meta-skill-generator/requirements.txt", "w") as f:
    f.write("# no external deps needed\n")

print("[gen_inputs] Workspace generated successfully.")