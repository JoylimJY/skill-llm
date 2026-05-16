#!/usr/bin/env python3
"""
Generates a realistic, messy sandbox workspace for the Chinese copywriting evaluation task.
The agent must rewrite a flawed Markdown release-notes file and produce a corrected output.
"""

import os
import random
import pathlib

random.seed(42)

WORKSPACE = pathlib.Path("/workspace")

# ─── Distractor directory structure ───────────────────────────────────────────
dirs = [
    "app/android/src",
    "app/ios/src",
    "app/shared/utils",
    "docs/design",
    "docs/legal",
    "marketing/campaigns/q3",
    "marketing/campaigns/q4",
    "backend/api/v2",
    "backend/db/migrations",
    "infra/docker",
    "infra/ci",
    "tests/unit",
    "tests/e2e",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files (realistic but irrelevant) ──────────────────────────────
distractor_files = {
    "app/android/src/MainActivity.java": "// Android main activity placeholder\npublic class MainActivity {}",
    "app/ios/src/AppDelegate.swift": "// iOS AppDelegate\nimport UIKit",
    "app/shared/utils/constants.ts": 'export const API_BASE = "https://api.example.com";',
    "docs/design/wireframe-notes.txt": "Wireframe iteration 3: add bottom nav bar.",
    "docs/legal/privacy-policy-draft.txt": "用户隐私政策草稿，待法务审核。",
    "marketing/campaigns/q3/brief.md": "# Q3 Campaign Brief\n\n目标受众：18-35岁城市用户。",
    "marketing/campaigns/q4/kpis.csv": "metric,target\nDAU,50000\nRetention,0.4",
    "backend/api/v2/openapi.yaml": "openapi: 3.0.0\ninfo:\n  title: App API\n  version: '2.0'",
    "backend/db/migrations/001_init.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY);",
    "infra/docker/Dockerfile.prod": "FROM python:3.11-slim\nRUN pip install gunicorn",
    "infra/ci/pipeline.yml": "stages:\n  - build\n  - test\n  - deploy",
    "tests/unit/test_auth.py": "def test_login(): assert True",
    "tests/e2e/test_onboarding.py": "def test_first_launch(): assert True",
    "app/shared/utils/formatter.py": "def format_date(d): return d.strftime('%Y-%m-%d')",
}
for rel_path, content in distractor_files.items():
    p = WORKSPACE / rel_path
    p.write_text(content, encoding="utf-8")

# ─── The actual task file: a MESSY release-notes Markdown with many violations ─
# Violations injected (all from the upstream Chinese copywriting guidelines):
#
# SPACING VIOLATIONS:
#   - Missing space between Chinese and English: "发布了iOS版本" → should be "发布了 iOS 版本"
#   - Missing space between Chinese and number: "版本3.2" → should be "版本 3.2"
#   - Missing space between number and Chinese unit: "500MB内存" → "500 MB 内存" (English unit)
#   - Missing space between English and Chinese: "GitHub仓库" → "GitHub 仓库"
#   - Missing space between number and English: "200ms延迟" → "200 ms 延迟"
#
# PUNCTUATION VIOLATIONS:
#   - Using halfwidth comma in Chinese sentence: "修复了bug,提升了性能" → should use fullwidth "，"
#   - Using halfwidth period at end of Chinese sentence: "感谢您的支持." → should be "感谢您的支持。"
#   - Using halfwidth parentheses in Chinese context: "(仅限付费用户)" → "（仅限付费用户）"
#   - Using Western ellipsis "..." instead of Chinese "……": "加载中..." → "加载中……"
#   - Duplicate punctuation: "！！" or "??" should be single
#
# FULLWIDTH / HALFWIDTH FORM VIOLATIONS:
#   - Full-width digits in code context: "版本号为３．２．１" → should be halfwidth "3.2.1"
#   - Mixing fullwidth and halfwidth in same sentence inappropriately
#
# PROPER NOUN / CASING VIOLATIONS:
#   - "github" should be "GitHub"
#   - "IOS" or "ios" should be "iOS"
#   - "wifi" should be "WiFi"
#   - "app store" should be "App Store"
#   - "javascript" should be "JavaScript"

messy_release_notes = """\
# 版本更新日志

## v3.2.1 发布说明

我们很高兴地宣布，本次更新发布了ios版本和Android版本的全面升级。

### 新功能

- 新增了离线模式，用户现在可以在没有wifi的情况下继续使用核心功能(仅限付费用户)
- 支持通过github登录，方便开发者快速接入
- 在app store上线了全新的订阅方案，价格更实惠
- 新增javascript插件支持，让第三方开发者能够扩展功能

### 性能优化

- 将启动时间从原来的800ms缩短至200ms,提升了用户体验
- 内存占用降低了约500MB,应用更加流畅
- 修复了在IOS设备上的崩溃问题
- 数据库查询速度提升了30%,界面响应更迅速

### Bug修复

- 修复了用户登录后无法加载数据的问题(影响版本3.0至3.1.5)
- 修复了在部分Android设备上显示乱码的问题
- 解决了与第三方支付SDK集成时出现的兼容性问题
- 加载中...请等待数据同步完成

### 重要提示

感谢所有用户的反馈和支持.我们会持续改进产品，为您提供更好的体验!!

如有问题，请访问我们的github仓库提交issue，或通过官方渠道联系客服。

更新方法：请前往app store搜索我们的应用，点击更新即可。
"""

task_file = WORKSPACE / "docs" / "release-notes-draft.md"
task_file.write_text(messy_release_notes, encoding="utf-8")

print("[gen_inputs] Workspace generated successfully.")
print(f"[gen_inputs] Task file: {task_file}")
print(f"[gen_inputs] Distractor files: {len(distractor_files)}")