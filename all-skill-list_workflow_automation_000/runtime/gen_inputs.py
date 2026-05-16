import os
import pickle
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

# ─── Root paths ───────────────────────────────────────────────────────────────
HOME = Path("/root")
SKILLS_ROOT = HOME / ".openclaw" / "workspace" / "skills"
ALL_SKILL_LIST_DIR = SKILLS_ROOT / "all-skill-list"
SCRIPTS_DIR = ALL_SKILL_LIST_DIR / "scripts"

# ─── Create directory skeleton ────────────────────────────────────────────────
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Define the CURRENT set of skills (what SHOULD exist after agent acts) ───
CURRENT_SKILLS = [
    "web-crawler",
    "pdf-extractor",
    "db-connector",
    "email-sender",
    "image-resizer",
    "code-reviewer",
    "log-analyzer",
]

# ─── Define the STALE set (what the old cache "remembers") ────────────────────
# Compared to CURRENT: "image-resizer" is NEW, "old-skill-alpha" was REMOVED,
# "dead-skill-beta" was also REMOVED.
STALE_SKILLS = [
    "web-crawler",
    "pdf-extractor",
    "db-connector",
    "email-sender",
    "old-skill-alpha",   # will NOT exist on disk
    "dead-skill-beta",   # will NOT exist on disk
    "code-reviewer",
    "log-analyzer",
]

# ─── Create SKILL.md for each CURRENT skill ───────────────────────────────────
SKILL_DESCRIPTIONS = {
    "web-crawler": textwrap.dedent("""\
        ---
        name: web-crawler
        description: 高性能网页爬取技能，支持深度抓取、JS渲染、自动去重和断点续传
        metadata: {"clawbot":{"emoji":"🕷","requires":{}}}
        ---
        # Web Crawler Skill
        Fetches and parses web pages recursively. Supports rate limiting and proxy rotation.
        """),
    "pdf-extractor": textwrap.dedent("""\
        ---
        name: pdf-extractor
        description: PDF内容提取技能，支持文本、表格、图片、元数据的结构化抽取
        metadata: {"clawbot":{"emoji":"📄","requires":{}}}
        ---
        # PDF Extractor Skill
        Extracts structured content from PDF documents including text, tables and images.
        """),
    "db-connector": textwrap.dedent("""\
        ---
        name: db-connector
        description: 多数据库连接器，支持 MySQL、PostgreSQL、MongoDB、Redis 的统一访问接口
        metadata: {"clawbot":{"emoji":"🗄","requires":{}}}
        ---
        # DB Connector Skill
        Provides a unified interface to multiple database backends with connection pooling.
        """),
    "email-sender": textwrap.dedent("""\
        ---
        name: email-sender
        description: 自动化邮件发送技能，支持 HTML 模板、附件、批量发送和退信处理
        metadata: {"clawbot":{"emoji":"📧","requires":{}}}
        ---
        # Email Sender Skill
        Sends HTML or plain-text emails with attachment support and bounce handling.
        """),
    "image-resizer": textwrap.dedent("""\
        ---
        name: image-resizer
        description: 图像批量缩放与格式转换技能，支持 JPEG/PNG/WebP，保留 EXIF 元数据
        metadata: {"clawbot":{"emoji":"🖼","requires":{}}}
        ---
        # Image Resizer Skill
        Batch resizes images and converts between JPEG, PNG and WebP while preserving EXIF data.
        """),
    "code-reviewer": textwrap.dedent("""\
        ---
        name: code-reviewer
        description: AI 辅助代码审查技能，支持多语言、安全扫描、风格检查和自动建议
        metadata: {"clawbot":{"emoji":"🔍","requires":{}}}
        ---
        # Code Reviewer Skill
        Performs AI-assisted code review with security scanning and style enforcement.
        """),
    "log-analyzer": textwrap.dedent("""\
        ---
        name: log-analyzer
        description: 日志分析与异常检测技能，支持正则规则、统计基线和实时告警
        metadata: {"clawbot":{"emoji":"📊","requires":{}}}
        ---
        # Log Analyzer Skill
        Analyzes log streams for anomalies using regex rules and statistical baselines.
        """),
}

for skill_name, content in SKILL_DESCRIPTIONS.items():
    skill_dir = SKILLS_ROOT / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    # Add some distractor files inside each skill dir
    (skill_dir / "config.yaml").write_text(f"skill: {skill_name}\nversion: 1.0\n")
    (skill_dir / "requirements.txt").write_text("requests>=2.28\n")
    scripts_sub = skill_dir / "scripts"
    scripts_sub.mkdir(exist_ok=True)
    (scripts_sub / "run.py").write_text(f"# Entry point for {skill_name}\nprint('running {skill_name}')\n")
    (scripts_sub / "utils.py").write_text(f"# Utilities for {skill_name}\n")

# ─── Create the all-skill-list SKILL.md ───────────────────────────────────────
(ALL_SKILL_LIST_DIR / "SKILL.md").write_text(textwrap.dedent("""\
    ---
    name: all-skill-list
    description: 本地扩展技能目录 - 聚合所有 OpenClaw 本地技能，支持列表查询、描述提取、缓存加速、差异对比、自动更新技能清单
    metadata: {"clawbot":{"emoji":"📚","requires":{},"install":[{"id":"local","kind":"dir","path":"/home/node/.openclaw/workspace/skills","label":"本地技能目录"}]}}
    ---
    # Skill-List - 本地扩展技能目录（智能缓存版）
    This skill aggregates all local OpenClaw skills.
    """), encoding="utf-8")

# ─── Create the main skill-list.py script ─────────────────────────────────────
SKILL_LIST_SCRIPT = r'''#!/usr/bin/env python3
"""
skill-list.py - OpenClaw Local Skills Directory Manager (Cache Edition)
Scans ~/.openclaw/workspace/skills and manages a Pickle cache.
"""
import argparse
import os
import pickle
import json
import sys
from pathlib import Path

# Resolve skill root dynamically from script location
SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPT_DIR.parent.parent  # .../skills
CACHE_FILE = SCRIPT_DIR / "skills_cache.pickle"
JSON_EXPORT = SCRIPT_DIR / "skills_export.json"
MD_EXPORT   = SCRIPT_DIR / "all_skills.md"

SELF_NAME = "all-skill-list"


def get_skill_dirs():
    """Return sorted list of skill directory names (excluding self)."""
    if not SKILLS_ROOT.is_dir():
        return []
    dirs = [
        d.name for d in sorted(SKILLS_ROOT.iterdir())
        if d.is_dir() and d.name != SELF_NAME
    ]
    return dirs


def parse_skill_md(skill_dir: Path):
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"name": skill_dir.name, "description": "", "has_skill_md": False, "path": str(skill_dir)}
    content = skill_md.read_text(encoding="utf-8", errors="replace")
    # Extract description from frontmatter
    description = ""
    in_frontmatter = False
    fm_count = 0
    for line in content.splitlines():
        if line.strip() == "---":
            fm_count += 1
            in_frontmatter = fm_count == 1
            if fm_count == 2:
                in_frontmatter = False
            continue
        if in_frontmatter and line.startswith("description:"):
            description = line[len("description:"):].strip()
    return {
        "name": skill_dir.name,
        "description": description,
        "full_content": content,
        "has_skill_md": True,
        "path": str(skill_dir),
    }


def scan_all_skills():
    skill_dirs = get_skill_dirs()
    skills = []
    for name in skill_dirs:
        skill_path = SKILLS_ROOT / name
        skills.append(parse_skill_md(skill_path))
    return skill_dirs, skills


def load_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None
    return None


def save_cache(skill_dirs, skills):
    data = {"skill_dirs": skill_dirs, "skills": skills}
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(data, f)


def get_skills(force=False):
    current_dirs = get_skill_dirs()
    if not force:
        cached = load_cache()
        if cached and cached.get("skill_dirs") == current_dirs:
            print("📦 使用缓存数据", file=sys.stderr)
            return cached["skills"]
    print("🔍 扫描OpenClaw技能...", file=sys.stderr)
    skill_dirs, skills = scan_all_skills()
    save_cache(skill_dirs, skills)
    return skills


def display_skills(skills, level="simple"):
    total = len(skills)
    has_md = sum(1 for s in skills if s.get("has_skill_md"))
    print(f"\n📊 OpenClaw技能列表 (共 {total} 个)")
    for i, skill in enumerate(skills, 1):
        icon = "✅" if skill.get("has_skill_md") else "❌"
        if level == "simple":
            print(f"  {i}. {icon} {skill['name']}")
        elif level == "half":
            desc = skill.get("description", "")[:200]
            print(f"  {i}. {icon} {skill['name']}")
            if desc:
                print(f"      📝 {desc}")
            print(f"      📁 {skill['path']}")
        elif level == "all":
            print(f"  {i}. {icon} {skill['name']}")
            content = skill.get("full_content") or skill.get("description", "")
            if content:
                print(f"      📝 完整内容:")
                for line in content.splitlines():
                    print(f"         {line}")
            print(f"      📁 {skill['path']}")
    print(f"\n📈 统计: {has_md}/{total} 个技能有SKILL.md文件")


def export_json(skills):
    data = []
    for s in skills:
        data.append({
            "name": s["name"],
            "description": s.get("description", ""),
            "has_skill_md": s.get("has_skill_md", False),
            "path": s["path"],
        })
    JSON_EXPORT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ JSON已导出: {JSON_EXPORT}", file=sys.stderr)


def export_md(skills):
    lines = ["# OpenClaw 技能总览\n"]
    for s in skills:
        lines.append(f"## {s['name']}\n")
        content = s.get("full_content") or s.get("description", "")
        if content:
            lines.append(content)
        lines.append(f"\n**路径**: `{s['path']}`\n")
        lines.append("---\n")
    MD_EXPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Markdown已导出: {MD_EXPORT}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Skills Directory")
    parser.add_argument("-f", "--force", action="store_true", help="强制重新扫描")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    parser.add_argument("-V", dest="level", choices=["all", "half", "simple"], default="simple", help="显示级别")
    parser.add_argument("--json", action="store_true", dest="export_json", help="导出为JSON格式")
    parser.add_argument("--md", action="store_true", dest="export_md", help="导出为Markdown格式")
    parser.add_argument("--no-repair", action="store_true", help="关闭自动修复功能")
    parser.add_argument("--debug", action="store_true", help="显示调试信息")
    args = parser.parse_args()

    if args.debug:
        print(f"[DEBUG] SKILLS_ROOT={SKILLS_ROOT}", file=sys.stderr)
        print(f"[DEBUG] CACHE_FILE={CACHE_FILE}", file=sys.stderr)

    skills = get_skills(force=args.force)
    display_skills(skills, level=args.level)

    if args.export_json:
        export_json(skills)
    if args.export_md:
        export_md(skills)


if __name__ == "__main__":
    main()
'''

(SCRIPTS_DIR / "skill-list.py").write_text(SKILL_LIST_SCRIPT, encoding="utf-8")
(SCRIPTS_DIR / "skill-list.py").chmod(0o755)

# ─── Helper: parse a SKILL.md in gen_inputs.py scope ─────────────────────────
def parse_skill_md(skill_dir: Path):
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"name": skill_dir.name, "description": "", "has_skill_md": False, "path": str(skill_dir)}
    content = skill_md.read_text(encoding="utf-8", errors="replace")
    description = ""
    in_frontmatter = False
    fm_count = 0
    for line in content.splitlines():
        if line.strip() == "---":
            fm_count += 1
            in_frontmatter = fm_count == 1
            if fm_count == 2:
                in_frontmatter = False
            continue
        if in_frontmatter and line.startswith("description:"):
            description = line[len("description:"):].strip()
    return {
        "name": skill_dir.name,
        "description": description,
        "full_content": content,
        "has_skill_md": True,
        "path": str(skill_dir),
    }

# ─── Seed a STALE cache ────────────────────────────────────────────────────────
# The stale cache remembers old skill dirs (including non-existent ones)
# and is missing "image-resizer".
stale_skills_data = []
for name in STALE_SKILLS:
    if name in ["old-skill-alpha", "dead-skill-beta"]:
        stale_skills_data.append({
            "name": name,
            "description": f"Legacy skill: {name}",
            "has_skill_md": True,
            "path": str(SKILLS_ROOT / name),
            "full_content": f"---\nname: {name}\ndescription: Legacy skill: {name}\n---\n",
        })
    else:
        skill_path = SKILLS_ROOT / name
        stale_skills_data.append(parse_skill_md(skill_path))

stale_cache = {
    "skill_dirs": STALE_SKILLS,
    "skills": stale_skills_data,
}
with open(SCRIPTS_DIR / "skills_cache.pickle", "wb") as f:
    pickle.dump(stale_cache, f)

print("✅ Workspace initialized:")
print(f"   Skills root:  {SKILLS_ROOT}")
print(f"   Skills created: {CURRENT_SKILLS}")
print(f"   Stale cache reflects: {STALE_SKILLS}")
print(f"   Cache file:   {SCRIPTS_DIR / 'skills_cache.pickle'}")
print(f"   Script:       {SCRIPTS_DIR / 'skill-list.py'}")

# ─── Extra distractor files in workspace root ─────────────────────────────────
WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(exist_ok=True)
(WORKSPACE / "notes.txt").write_text("Old meeting notes - not relevant\n")
(WORKSPACE / "todo.md").write_text("# TODO\n- Review skills\n- Update docs\n")
(WORKSPACE / "archive").mkdir(exist_ok=True)
(WORKSPACE / "archive" / "old_export.json").write_text('[{"name":"dead-skill-beta"}]')
(WORKSPACE / "archive" / "legacy_cache.pkl").write_bytes(b"PK\x03\x04fake")
(WORKSPACE / "tmp").mkdir(exist_ok=True)
(WORKSPACE / "tmp" / "scratch.py").write_text("# scratch\n")
(WORKSPACE / "tmp" / "debug.log").write_text("2026-01-01 ERROR: cache miss\n")