import os
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "skills/botlearn-certify/flows",
    "skills/botlearn-certify/knowledge",
    "skills/botlearn-certify/strategies",
    "skills/botlearn-certify/assets",
    "skills/botlearn-certify/scripts",
    "skills/botlearn-certify/results",
    "skills/botlearn-assessment/reports",
    "skills/botlearn-assessment/history",
    "skills/botlearn-assessment/tmp",
    "config",
    "logs",
    "data/raw",
    "data/processed",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "config/platform.yaml": "platform: openclaw\nenv: production\nversion: 3.2.1\n",
    "config/agents.json": '{"agents": [{"id": "agent-007", "name": "Zeta"}, {"id": "agent-042", "name": "Omega"}]}\n',
    "logs/system.log": "2024-01-10 08:00:00 INFO  Platform started\n2024-01-10 08:01:00 INFO  Assessment module loaded\n",
    "logs/error.log": "2024-01-09 22:15:00 ERROR Connection timeout on port 9090\n",
    "data/raw/exam_dump_2023.csv": "agent_id,score,date\nagent-007,72,2023-11-01\nagent-042,88,2023-12-15\n",
    "data/processed/summary_2023.json": '{"total_exams": 210, "avg_score": 79.4}\n',
    "skills/botlearn-assessment/tmp/scratch.txt": "temp file — do not use\n",
    "skills/botlearn-assessment/history/archive_2023.tar.gz.placeholder": "binary placeholder\n",
    "skills/botlearn-certify/flows/DEPRECATED_flow0.md": "# Deprecated — do not use\nThis flow was replaced in v0.1.3.\n",
    "skills/botlearn-certify/scripts/check-assessment.sh": "#!/bin/bash\necho 'botlearn-assessment OK'\n",
}
for rel, content in distractor_files.items():
    p = WORKSPACE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── botlearn-certify SKILL.md ────────────────────────────────────────────────
skill_md = textwrap.dedent("""\
    ---
    name: botlearn-certify
    version: 0.1.5
    ---

    # botlearn-certify — OpenClaw Agent Education Certification System

    ## Key Principles
    1. **Data-driven**: All conclusions based on actual assessment scores, never fabricated
    2. **Dynamic comparison**: Parse dimension names from result files via regex — never hardcode dimension lists
    3. **Emotional value**: Certificates should be celebratory and encouraging
    4. **Dual format**: Always generate both HTML and MD certificates

    ## Output Location
    All certificates are saved to:
    ```
    results/certificate-{YYYYMMDD}-{HHmm}.html
    results/certificate-{YYYYMMDD}-{HHmm}.md
    ```

    ## Reference Materials
    - `knowledge/comparison-methodology.md`
    - `strategies/classification.md`
    - `assets/certificate-html-template.md`
    - `assets/certificate-md-template.md`
    """)
(WORKSPACE / "skills/botlearn-certify/SKILL.md").write_text(skill_md)

# ── flow1-historical.md ──────────────────────────────────────────────────────
flow1 = textwrap.dedent("""\
    # Flow 1 — Historical Assessment Retrieval

    1. Verify botlearn-assessment is installed (run `bash scripts/check-assessment.sh`).
    2. Read `../botlearn-assessment/INDEX.md` to find the most recent FULL exam entry.
       - Full exam entries are marked with tag `[FULL]` in the INDEX.
       - Each entry has format: `| DATE | REPORT_PATH | TAG |`
    3. Parse the identified report file for dimension scores.
       - Use regex to extract lines matching pattern: `^- ([^:]+):\s+([0-9]+(?:\.[0-9]+)?)/100$`
       - Extract ALL dimensions dynamically — never hardcode dimension names.
    4. Record the `overall_score` from the report (line: `Overall Score: XX/100`).
    """)
(WORKSPACE / "skills/botlearn-certify/flows/flow1-historical.md").write_text(flow1)

# ── flow2-fresh-exam.md ──────────────────────────────────────────────────────
flow2 = textwrap.dedent("""\
    # Flow 2 — Fresh Assessment Execution

    In this sandbox context, the fresh exam has already been completed and saved.
    Read the fresh exam report from `../botlearn-assessment/reports/latest.md`.
    Parse dimension scores with the same regex as Flow 1.
    Record the `overall_score`.
    """)
(WORKSPACE / "skills/botlearn-certify/flows/flow2-fresh-exam.md").write_text(flow2)

# ── flow3-certificate.md ─────────────────────────────────────────────────────
flow3 = textwrap.dedent("""\
    # Flow 3 — Certificate Generation

    1. Load comparison methodology from `knowledge/comparison-methodology.md`.
    2. Load classification rules from `strategies/classification.md`.
    3. Compare historical baseline vs fresh scores:
       - Per-dimension delta = fresh_score - historical_score
       - Overall improvement = fresh_overall - historical_overall
    4. Classify the professional profile using `strategies/classification.md`.
    5. Load `assets/certificate-html-template.md` and fill in ALL placeholders.
    6. Load `assets/certificate-md-template.md` and fill in ALL placeholders.
    7. Save both files to `results/` with naming:
       `certificate-{YYYYMMDD}-{HHmm}.html`
       `certificate-{YYYYMMDD}-{HHmm}.md`
       where the timestamp is the current wall-clock time at generation.
    8. Both files MUST contain the agent name, overall scores (historical + fresh),
       per-dimension comparison table, improvement value, and professional profile label.
    """)
(WORKSPACE / "skills/botlearn-certify/flows/flow3-certificate.md").write_text(flow3)

# ── comparison-methodology.md ────────────────────────────────────────────────
comparison_md = textwrap.dedent("""\
    # Comparison Methodology

    ## Score Improvement Calculation
    ```
    overall_improvement = fresh_overall_score - historical_overall_score
    ```

    ## Per-Dimension Delta
    ```
    dimension_delta[d] = fresh_score[d] - historical_score[d]
    ```
    A positive delta means improvement; negative means regression.

    ## Improvement Classification
    | Improvement Range | Label         |
    |-------------------|---------------|
    | >= 15             | Exceptional   |
    | >= 8              | Significant   |
    | >= 1              | Modest        |
    | 0                 | Steady        |
    | < 0               | Needs Review  |

    ## Required certificate fields
    - `{{HISTORICAL_OVERALL}}` — historical overall score (integer)
    - `{{FRESH_OVERALL}}`      — fresh overall score (integer)
    - `{{IMPROVEMENT}}`        — overall_improvement value (with sign, e.g. +7 or -2)
    - `{{IMPROVEMENT_LABEL}}`  — label from table above
    - `{{DIMENSION_TABLE}}`    — table of all dimensions with historical, fresh, delta
    """)
(WORKSPACE / "skills/botlearn-certify/knowledge/comparison-methodology.md").write_text(comparison_md)

# ── classification.md ────────────────────────────────────────────────────────
classification_md = textwrap.dedent("""\
    # Professional Profile Classification

    Classification is based on the FRESH overall score only.

    | Score Range  | Profile Label            | Badge Color |
    |--------------|--------------------------|-------------|
    | 90 – 100     | Elite Practitioner       | gold        |
    | 75 – 89      | Advanced Specialist      | silver      |
    | 60 – 74      | Competent Professional   | bronze      |
    | 45 – 59      | Developing Learner       | blue        |
    | 0  – 44      | Foundation Builder       | green       |

    The certificate MUST include:
    - `{{PROFILE_LABEL}}`  — text label from table above
    - `{{BADGE_COLOR}}`    — color from table above
    """)
(WORKSPACE / "skills/botlearn-certify/strategies/classification.md").write_text(classification_md)

# ── HTML template ────────────────────────────────────────────────────────────
html_template = textwrap.dedent("""\
    # HTML Certificate Template

    Use the following HTML structure. Replace ALL `{{PLACEHOLDERS}}` with real values.

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>OpenClaw Capability Certificate</title>
      <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; }
        .badge { display: inline-block; padding: 6px 16px; border-radius: 12px;
                 background: {{BADGE_COLOR}}; color: white; font-weight: bold; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px 12px; text-align: left; }
        th { background: #f0f0f0; }
      </style>
    </head>
    <body>
      <h1>🎓 OpenClaw Agent Capability Certificate</h1>
      <p><strong>Agent:</strong> {{AGENT_NAME}}</p>
      <p><strong>Profile:</strong> <span class="badge">{{PROFILE_LABEL}}</span></p>
      <h2>Score Summary</h2>
      <p>Historical Overall: {{HISTORICAL_OVERALL}}/100</p>
      <p>Fresh Overall: {{FRESH_OVERALL}}/100</p>
      <p>Improvement: {{IMPROVEMENT}} ({{IMPROVEMENT_LABEL}})</p>
      <h2>Dimension Breakdown</h2>
      {{DIMENSION_TABLE}}
      <p style="margin-top:40px;color:#888;">Generated by botlearn-certify v0.1.5</p>
    </body>
    </html>
    ```
    """)
(WORKSPACE / "skills/botlearn-certify/assets/certificate-html-template.md").write_text(html_template)

# ── MD template ──────────────────────────────────────────────────────────────
md_template = textwrap.dedent("""\
    # MD Certificate Template

    Use the following Markdown structure. Replace ALL `{{PLACEHOLDERS}}` with real values.

    ```markdown
    # 🎓 OpenClaw Agent Capability Certificate

    **Agent:** {{AGENT_NAME}}
    **Profile:** {{PROFILE_LABEL}} ({{BADGE_COLOR}})

    ## Score Summary

    | Metric | Score |
    |--------|-------|
    | Historical Overall | {{HISTORICAL_OVERALL}}/100 |
    | Fresh Overall | {{FRESH_OVERALL}}/100 |
    | Improvement | {{IMPROVEMENT}} ({{IMPROVEMENT_LABEL}}) |

    ## Dimension Breakdown

    {{DIMENSION_TABLE}}

    ---
    *Generated by botlearn-certify v0.1.5*
    ```
    """)
(WORKSPACE / "skills/botlearn-certify/assets/certificate-md-template.md").write_text(md_template)

# ── botlearn-assessment INDEX.md ─────────────────────────────────────────────
index_md = textwrap.dedent("""\
    # botlearn-assessment Exam Index

    | DATE       | REPORT_PATH                        | TAG    |
    |------------|------------------------------------|--------|
    | 2024-03-05 | history/report-20240305-1420.md    | [MINI] |
    | 2024-05-18 | history/report-20240518-0930.md    | [FULL] |
    | 2024-07-22 | history/report-20240722-1105.md    | [MINI] |
    | 2024-09-30 | history/report-20240930-1600.md    | [FULL] |
    | 2024-11-14 | history/report-20241114-0845.md    | [MINI] |
    """)
(WORKSPACE / "skills/botlearn-assessment/INDEX.md").write_text(index_md)

# ── Historical MINI reports (distractors) ───────────────────────────────────
mini1 = textwrap.dedent("""\
    # Assessment Report — 2024-03-05
    Type: MINI
    Agent: Zeta-7

    ## Scores
    - Reasoning: 61/100
    - Language Comprehension: 58/100

    Overall Score: 59/100
    """)
(WORKSPACE / "skills/botlearn-assessment/history/report-20240305-1420.md").write_text(mini1)

mini2 = textwrap.dedent("""\
    # Assessment Report — 2024-07-22
    Type: MINI
    Agent: Zeta-7

    ## Scores
    - Reasoning: 70/100
    - Language Comprehension: 68/100

    Overall Score: 69/100
    """)
(WORKSPACE / "skills/botlearn-assessment/history/report-20240722-1105.md").write_text(mini2)

mini3 = textwrap.dedent("""\
    # Assessment Report — 2024-11-14
    Type: MINI
    Agent: Zeta-7

    ## Scores
    - Reasoning: 74/100

    Overall Score: 74/100
    """)
(WORKSPACE / "skills/botlearn-assessment/history/report-20241114-0845.md").write_text(mini3)

# ── Historical FULL reports ──────────────────────────────────────────────────
full1 = textwrap.dedent("""\
    # Assessment Report — 2024-05-18
    Type: FULL
    Agent: Zeta-7

    ## Scores
    - Reasoning: 62/100
    - Language Comprehension: 59/100
    - Tool Usage: 55/100
    - Problem Solving: 64/100
    - Knowledge Retrieval: 60/100

    Overall Score: 60/100
    """)
(WORKSPACE / "skills/botlearn-assessment/history/report-20240518-0930.md").write_text(full1)

# ← The MOST RECENT full exam — agent must pick this one (2024-09-30)
full2 = textwrap.dedent("""\
    # Assessment Report — 2024-09-30
    Type: FULL
    Agent: Zeta-7

    ## Scores
    - Reasoning: 71/100
    - Language Comprehension: 74/100
    - Tool Usage: 68/100
    - Problem Solving: 76/100
    - Knowledge Retrieval: 73/100

    Overall Score: 72/100
    """)
(WORKSPACE / "skills/botlearn-assessment/history/report-20240930-1600.md").write_text(full2)

# ── Fresh exam report ────────────────────────────────────────────────────────
fresh_report = textwrap.dedent("""\
    # Assessment Report — 2025-01-15
    Type: FULL
    Agent: Zeta-7

    ## Scores
    - Reasoning: 80/100
    - Language Comprehension: 82/100
    - Tool Usage: 77/100
    - Problem Solving: 85/100
    - Knowledge Retrieval: 79/100

    Overall Score: 81/100
    """)
(WORKSPACE / "skills/botlearn-assessment/reports/latest.md").write_text(fresh_report)

print("Workspace generated successfully.")