import os
import json
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "skills/changelog-curator/scripts",
    "skills/changelog-curator/resources",
    "skills/changelog-curator/examples",
    "skills/changelog-curator/tests",
    "project/src/api",
    "project/src/auth",
    "project/src/db",
    "project/docs",
    "project/infra",
    "project/.github/workflows",
    "scratch/old_releases",
    "scratch/drafts",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "project/src/api/routes.py": "# API routes\ndef get_users(): pass\ndef create_token(): pass\n",
    "project/src/auth/oauth.py": "# OAuth module\nclass OAuthHandler:\n    pass\n",
    "project/src/db/migrations.py": "# DB migrations\nMIGRATIONS = ['0001_initial', '0002_add_index']\n",
    "project/docs/architecture.md": "# Architecture\n\nThis document is a placeholder.\n",
    "project/infra/terraform.tf": 'resource "aws_s3_bucket" "main" { bucket = "example" }\n',
    "project/.github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n",
    "scratch/old_releases/v2.3.0.md": "# v2.3.0\n- Fixed login bug\n- Performance improvements\n",
    "scratch/drafts/rough_notes.txt": "TODO: remember to mention rate limit changes\nmaybe mention the new dashboard?\n",
    "project/src/api/serializers.py": "# Serializers\nclass UserSerializer:\n    fields = ['id', 'email', 'created_at']\n",
    "project/src/db/schema.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT UNIQUE);\n",
    "project/docs/api_reference.html": "<html><body><h1>API Reference</h1><p>Placeholder</p></body></html>\n",
    "scratch/drafts/marketing_copy.txt": "Version 2.4 brings exciting new capabilities for developers...\n",
}
for path, content in distractors.items():
    with open(os.path.join(BASE, path), "w") as f:
        f.write(content)

# ── spec.json ────────────────────────────────────────────────────────────────
spec = {
    "version_schema": "semver",
    "sections": [
        "版本摘要",
        "用户可感知变化",
        "内部改进",
        "兼容性注意",
        "升级建议",
        "已知限制"
    ],
    "commit_classification": {
        "user_facing": ["feat", "fix", "perf", "deprecate", "security"],
        "internal": ["chore", "refactor", "test", "ci", "build", "style", "docs-internal"],
        "ambiguous_requires_confirmation": ["revert", "merge", "bump"]
    },
    "rules": {
        "missing_scope_action": "list_under_pending_confirmation",
        "max_user_facing_bullets": 10,
        "max_internal_bullets": 8,
        "version_header_format": "## [{version}] - {date}",
        "pending_section_label": "待确认项",
        "require_known_limitations": True,
        "empty_section_placeholder": "_无_"
    },
    "output_format": "markdown",
    "language": "zh-CN"
}
with open(os.path.join(BASE, "skills/changelog-curator/resources/spec.json"), "w", encoding="utf-8") as f:
    json.dump(spec, f, ensure_ascii=False, indent=2)

# ── template.md ──────────────────────────────────────────────────────────────
template_md = textwrap.dedent("""\
## [{version}] - {date}

### 版本摘要
{summary}

### 用户可感知变化
{user_facing}

### 内部改进
{internal}

### 兼容性注意
{compatibility}

### 升级建议
{upgrade_guide}

### 已知限制
{known_limitations}

### 待确认项
{pending}
""")
with open(os.path.join(BASE, "skills/changelog-curator/resources/template.md"), "w", encoding="utf-8") as f:
    f.write(template_md)

# ── run.py ───────────────────────────────────────────────────────────────────
run_py = textwrap.dedent('''\
#!/usr/bin/env python3
"""
changelog-curator run.py
Usage: python3 run.py --input <input_file> --output <output_file>

Reads a JSON input file with keys:
  version   : str  (e.g. "2.4.0")
  date      : str  (ISO date, e.g. "2025-01-15")
  commits   : list of {hash, type, scope, message}
  known_limitations : list of str (may be empty)

Writes a Markdown changelog to <output_file> following spec.json rules.
"""
import argparse, json, sys, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(SCRIPT_DIR, "..", "resources")

def load_spec():
    with open(os.path.join(RESOURCE_DIR, "spec.json"), encoding="utf-8") as f:
        return json.load(f)

def load_template():
    with open(os.path.join(RESOURCE_DIR, "template.md"), encoding="utf-8") as f:
        return f.read()

def classify_commits(commits, spec):
    user_facing, internal, pending = [], [], []
    uf_types  = set(spec["commit_classification"]["user_facing"])
    int_types = set(spec["commit_classification"]["internal"])
    amb_types = set(spec["commit_classification"]["ambiguous_requires_confirmation"])
    missing_scope_action = spec["rules"]["missing_scope_action"]

    for c in commits:
        ctype  = (c.get("type") or "").strip().lower()
        scope  = (c.get("scope") or "").strip()
        msg    = c.get("message", "")
        bullet = f"- [{ctype}] {msg}" if not scope else f"- [{ctype}({scope})] {msg}"

        if ctype in amb_types:
            pending.append(bullet)
        elif not scope and missing_scope_action == "list_under_pending_confirmation":
            pending.append(bullet + " _(缺少 scope，待确认)_")
        elif ctype in uf_types:
            user_facing.append(bullet)
        elif ctype in int_types:
            internal.append(bullet)
        else:
            pending.append(bullet + " _(未知类型，待确认)_")

    return user_facing, internal, pending

def render_section(items, placeholder="_无_"):
    if not items:
        return placeholder
    return "\\n".join(items)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    spec     = load_spec()
    template = load_template()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    version  = data.get("version", "0.0.0")
    date     = data.get("date", "TBD")
    commits  = data.get("commits", [])
    kl_raw   = data.get("known_limitations", [])
    summary  = data.get("summary", "")
    compat   = data.get("compatibility", "")
    upgrade  = data.get("upgrade_guide", "")

    user_facing, internal, pending = classify_commits(commits, spec)

    header_fmt = spec["rules"]["version_header_format"]
    header = header_fmt.format(version=version, date=date)
    # replace the template header line
    placeholder_header = "## [{version}] - {date}"

    output = template.replace(placeholder_header, header)
    output = output.replace("{version}", version)
    output = output.replace("{date}", date)
    output = output.replace("{summary}", summary or "_无_")
    output = output.replace("{user_facing}", render_section(user_facing))
    output = output.replace("{internal}", render_section(internal))
    output = output.replace("{compatibility}", compat or "_无_")
    output = output.replace("{upgrade_guide}", upgrade or "_无_")
    output = output.replace("{known_limitations}", render_section(kl_raw) if kl_raw else "_无_")
    output = output.replace("{pending}", render_section(pending) if pending else "_无_")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"[run.py] Changelog written to: {args.output}")

if __name__ == "__main__":
    main()
''')
with open(os.path.join(BASE, "skills/changelog-curator/scripts/run.py"), "w", encoding="utf-8") as f:
    f.write(run_py)

# ── examples ─────────────────────────────────────────────────────────────────
example_input = {
    "version": "2.3.0",
    "date": "2025-01-01",
    "summary": "小幅功能增强与缺陷修复版本。",
    "commits": [
        {"hash": "aaa1111", "type": "feat",     "scope": "auth",    "message": "支持 SSO 登录"},
        {"hash": "bbb2222", "type": "fix",      "scope": "api",     "message": "修复分页参数溢出问题"},
        {"hash": "ccc3333", "type": "chore",    "scope": "ci",      "message": "升级 GitHub Actions runner"},
    ],
    "known_limitations": ["SSO 暂不支持 SAML 2.0"],
    "compatibility": "无破坏性变更。",
    "upgrade_guide": "直接升级，无需迁移。"
}
with open(os.path.join(BASE, "skills/changelog-curator/examples/input_v2.3.0.json"), "w", encoding="utf-8") as f:
    json.dump(example_input, f, ensure_ascii=False, indent=2)

# Example output (reference only)
example_output = textwrap.dedent("""\
## [2.3.0] - 2025-01-01

### 版本摘要
小幅功能增强与缺陷修复版本。

### 用户可感知变化
- [feat(auth)] 支持 SSO 登录
- [fix(api)] 修复分页参数溢出问题

### 内部改进
- [chore(ci)] 升级 GitHub Actions runner

### 兼容性注意
无破坏性变更。

### 升级建议
直接升级，无需迁移。

### 已知限制
- SSO 暂不支持 SAML 2.0

### 待确认项
_无_
""")
with open(os.path.join(BASE, "skills/changelog-curator/examples/output_v2.3.0.md"), "w", encoding="utf-8") as f:
    f.write(example_output)

# ── smoke-test.md ─────────────────────────────────────────────────────────────
smoke_test = textwrap.dedent("""\
# Smoke Test

Run:
  python3 scripts/run.py --input examples/input_v2.3.0.json --output /tmp/smoke_out.md

Then verify /tmp/smoke_out.md contains the six required sections.
""")
with open(os.path.join(BASE, "skills/changelog-curator/tests/smoke-test.md"), "w", encoding="utf-8") as f:
    f.write(smoke_test)

# ── THE PROBLEM INPUT: messy raw commit dump for v2.4.0 ──────────────────────
# This is the messy input the agent must process
raw_commits_v240 = textwrap.dedent("""\
version: 2.4.0
release-date: 2025-07-18
team: Platform Engineering

--- RAW COMMIT DUMP (from git log, unfiltered) ---

hash=f1a2b3c  type=feat     scope=webhooks   message=新增 Webhook 事件订阅 API，支持最多 50 个端点
hash=9d8e7f6  type=fix      scope=ratelimit  message=修复并发请求时速率限制计数器重置异常
hash=4c3d2e1  type=perf     scope=search     message=全文搜索响应时间降低 40%（引入向量索引）
hash=b5a6c7d  type=refactor scope=           message=重构认证中间件以提升可维护性
hash=e8f9a0b  type=chore    scope=deps       message=升级 pydantic 至 2.7.0
hash=1b2c3d4  type=security scope=tokens     message=修复 JWT 令牌泄漏漏洞（CVE-2025-1337）
hash=5e6f7a8  type=feat     scope=dashboard  message=新增 API 使用量折线图与导出功能
hash=2d3e4f5  type=docs-internal scope=arch  message=更新内部架构决策记录 ADR-0042
hash=c9d0e1f  type=test     scope=webhooks   message=为 Webhook 模块补充集成测试
hash=7a8b9c0  type=revert   scope=billing    message=回滚 billing 模块 v2.4.0-rc1 中的实验性改动
hash=3f4a5b6  type=deprecate scope=v1-api    message=标记 /v1/users 端点为废弃，将在 v3.0 移除
hash=8c9d0e1  type=feat     scope=           message=支持通过环境变量覆盖全局超时配置
hash=d2e3f4a  type=build    scope=docker     message=优化 Docker 镜像层以减少构建时间
hash=6b7c8d9  type=fix      scope=auth       message=修复 OAuth2 PKCE 流程中 code_verifier 校验失败
hash=0e1f2a3  type=merge    scope=main       message=Merge branch release/2.4.0 into main
hash=9f0a1b2  type=bump     scope=version    message=Bump version to 2.4.0
hash=4d5e6f7  type=ci       scope=pipeline   message=新增 SAST 静态安全扫描步骤
hash=1a2b3c4  type=perf     scope=db         message=为高频查询添加复合索引，读取性能提升 25%
hash=5f6a7b8  type=style    scope=formatter  message=统一代码格式化规则（black + isort）
hash=e3d4c5b  type=unknown  scope=misc       message=临时禁用夜间批处理任务（原因不明，待排查）

--- 已知限制（团队提供）---
- Webhook 端点数量上限当前硬编码为 50，后续版本将支持动态配置
- v1 API 废弃期至少维持两个大版本（v3.0 前均可用）

--- 兼容性说明 ---
本版本包含一处破坏性变更：移除了 /v1/legacy-export 端点（该端点在 v2.2.0 中已被标记废弃）。
依赖该端点的客户端须迁移至 /v2/export。

--- 升级建议 ---
1. 检查是否使用 /v1/legacy-export，如有，迁移至 /v2/export
2. 如使用 JWT 认证，建议立即升级（安全补丁）
3. 无数据库迁移脚本需执行
""")
with open(os.path.join(BASE, "project/docs/raw_v2.4.0_commits.txt"), "w", encoding="utf-8") as f:
    f.write(raw_commits_v240)

# Also create a partial/wrong previous attempt to mislead the agent
wrong_draft = textwrap.dedent("""\
# Release Notes v2.4.0 (DRAFT - DO NOT USE)

## What's New
- Webhooks!
- Better search
- Security fix

## Bug Fixes  
- Rate limiting
- OAuth fix

(This draft was auto-generated and is incomplete / incorrectly formatted)
""")
with open(os.path.join(BASE, "scratch/drafts/v2.4.0_wrong_draft.md"), "w", encoding="utf-8") as f:
    f.write(wrong_draft)

print("Workspace generated successfully.")
print("Key paths:")
print("  Skill root:  /workspace/skills/changelog-curator/")
print("  Raw input:   /workspace/project/docs/raw_v2.4.0_commits.txt")
print("  Distractor drafts: /workspace/scratch/drafts/")