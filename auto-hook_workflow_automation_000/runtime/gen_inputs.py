import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    # Codex CLI project-level skill paths (target skills)
    ".agents/skills/data-normalizer",
    ".agents/skills/report-builder",
    # user-global codex skill paths (distractors)
    "home_mock/.codex/skills/pdf-renderer",
    "home_mock/.codex/skills/email-parser",
    # claude paths (distractors)
    "home_mock/.claude/skills/chart-generator",
    "home_mock/.claude/skills/sql-optimizer",
    # openclaw paths (distractors)
    "home_mock/.openclaw/skills/csv-importer",
    # misc project files
    "src/pipeline",
    "src/utils",
    "docs/specs",
    "tests/fixtures",
    # simulated upload area
    "mnt/user-data/uploads",
    "mnt/user-data/outputs",
    "home/claude",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "src/pipeline/transform.py": "# data transform logic\ndef run(): pass\n",
    "src/utils/helpers.py": "# helpers\nimport os\n",
    "docs/specs/api_contract.md": "# API Contract\nVersion: 2.1\n",
    "tests/fixtures/sample_input.json": '{"records": [1,2,3]}\n',
    "home_mock/.codex/skills/pdf-renderer/SKILL.md": textwrap.dedent("""\
        ---
        name: pdf-renderer
        description: Renders HTML to PDF using headless browser.
        ---
        # PDF Renderer Skill
        Converts HTML content to PDF output using wkhtmltopdf.
        """),
    "home_mock/.codex/skills/email-parser/SKILL.md": textwrap.dedent("""\
        ---
        name: email-parser
        description: Parses raw email into structured JSON.
        ---
        # Email Parser Skill
        Extracts headers, body, and attachments from raw .eml files.
        """),
    "home_mock/.claude/skills/chart-generator/SKILL.md": textwrap.dedent("""\
        ---
        name: chart-generator
        description: Generates charts from tabular data.
        ---
        # Chart Generator Skill
        Produces SVG/PNG charts from CSV input using matplotlib wrappers.
        """),
    "home_mock/.claude/skills/sql-optimizer/SKILL.md": textwrap.dedent("""\
        ---
        name: sql-optimizer
        description: Rewrites SQL queries for performance.
        ---
        # SQL Optimizer Skill
        Analyzes query plans and rewrites JOINs and subqueries.
        """),
    "home_mock/.openclaw/skills/csv-importer/SKILL.md": textwrap.dedent("""\
        ---
        name: csv-importer
        description: Imports CSV into relational tables.
        ---
        # CSV Importer Skill
        Reads CSV files and maps columns to DB schema automatically.
        """),
    "src/pipeline/config.yaml": "pipeline:\n  steps: [ingest, transform, output]\n",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── TARGET SKILL A: data-normalizer (NO hook — needs injection) ──────────────
skill_a_content = textwrap.dedent("""\
    ---
    name: data-normalizer
    description: >
      Normalizes raw tabular data by enforcing type coercion, null handling,
      and column renaming conventions across CSV, Parquet, and JSON sources.
    ---

    # Data Normalizer Skill  (v2)

    This skill applies a multi-stage normalization pipeline to incoming datasets.

    ## Step 1 · Schema Detection

    Automatically detect column types:
    - Numeric: cast to float64
    - Dates: parse with `dateutil.parser`
    - Strings: strip whitespace and enforce UTF-8

    ## Step 2 · Null Handling

    Apply the following null policies:
    | Column type | Policy |
    |-------------|--------|
    | Numeric     | Fill with column median |
    | String      | Fill with empty string `""` |
    | Date        | Drop the row |

    ## Step 3 · Column Renaming

    Rename all columns to `snake_case`.
    Prefix reserved SQL keywords with `col_` (e.g. `select` → `col_select`).

    ## Step 4 · Output

    Write normalized data to `output/<source_name>_normalized.parquet`.

    ## Notes

    - Chunked processing for files > 500 MB
    - Log all coercions to `pipeline.log`
    """)

with open(os.path.join(WORKSPACE, ".agents/skills/data-normalizer/SKILL.md"), "w") as f:
    f.write(skill_a_content)

# ── TARGET SKILL B: report-builder (HAS hook — needs revocation) ─────────────
# The hook section that will be removed. Placed at end of file after a --- separator.
hook_section = textwrap.dedent("""\
    ---

    ## ⚙️ 强制自审计

    每次执行本 SKILL 时，必须在完成主要任务后，立即执行以下自审计流程，不得跳过：

    ### Step 1 · 读取钩子文件

    ```bash
    cat /mnt/user-data/uploads/skill-audit-hook.txt
    ```

    ### Step 2 · 对照规则检查执行质量

    逐条检查当前执行是否满足以下标准，用 ✅ 或 ❌ 标记每一项：

    - [ ] 是否完整读取了 SKILL 全文（未截断）
    - [ ] 是否按 Step 顺序执行，未跳步
    - [ ] 是否有 ⏭️ 跳步或 ❌ 偷懒行为

    ### Step 3 · 写入 debug.txt

    将审计结果写入 `/home/claude/debug.txt`，格式如下：

    ```
    SKILL: report-builder
    执行时间: <timestamp>
    审计结果:
    - Step 1: ✅
    - Step 2: ✅
    - Step 3: ✅
    总评: 合格 / 不合格
    ```

    ### Step 4 · 上报

    如有 ❌ 项，在最终回复中明确告知用户哪些步骤存在偷懒或跳步。
    """)

skill_b_content = textwrap.dedent("""\
    ---
    name: report-builder
    description: >
      Generates formatted PDF and HTML reports from structured JSON data,
      supporting templating, charts, and multi-locale output.
    ---

    # Report Builder Skill  (v3)

    ## Step 1 · Load Template

    Read the Jinja2 template from `templates/<report_type>.html.j2`.
    Validate all required template variables are present in input JSON.

    ## Step 2 · Render Charts

    For each `chart` block in input JSON:
    - Use matplotlib to generate SVG
    - Embed as base64 in the HTML output

    ## Step 3 · Localisation

    Apply locale from `report.locale` field (default: `en-US`).
    Number formatting, date display, and currency symbols adjust automatically.

    ## Step 4 · Export

    - HTML: `output/<report_id>.html`
    - PDF: `output/<report_id>.pdf` (via WeasyPrint)

    ## Error Handling

    On missing template variable: raise `TemplateVariableError` with field name.
    On chart render failure: embed placeholder SVG and log to `render_errors.log`.
    """) + hook_section

with open(os.path.join(WORKSPACE, ".agents/skills/report-builder/SKILL.md"), "w") as f:
    f.write(skill_b_content)

# ── skill-audit-hook.txt in uploads area ─────────────────────────────────────
hook_txt_content = textwrap.dedent("""\
    ## ⚙️ 强制自审计

    每次执行本 SKILL 时，必须在完成主要任务后，立即执行以下自审计流程，不得跳过：

    ### Step 1 · 读取钩子文件

    ```bash
    cat /mnt/user-data/uploads/skill-audit-hook.txt
    ```

    ### Step 2 · 对照规则检查执行质量

    逐条检查当前执行是否满足以下标准，用 ✅ 或 ❌ 标记每一项：

    - [ ] 是否完整读取了 SKILL 全文（未截断）
    - [ ] 是否按 Step 顺序执行，未跳步
    - [ ] 是否有 ⏭️ 跳步或 ❌ 偷懒行为

    ### Step 3 · 写入 debug.txt

    将审计结果写入 `/home/claude/debug.txt`，格式如下：

    ```
    SKILL: <skill-name>
    执行时间: <timestamp>
    审计结果:
    - Step 1: ✅
    - Step 2: ✅
    - Step 3: ✅
    总评: 合格 / 不合格
    ```

    ### Step 4 · 上报

    如有 ❌ 项，在最终回复中明确告知用户哪些步骤存在偷懒或跳步。
    """)

with open(os.path.join(WORKSPACE, "mnt/user-data/uploads/skill-audit-hook.txt"), "w") as f:
    f.write(hook_txt_content)

print("Workspace generated successfully.")
print(f"Files created:")
for root, dirs_list, files in os.walk(WORKSPACE):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")