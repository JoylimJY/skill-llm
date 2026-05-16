import os
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ── Skill installation (simulate {baseDir}) ──────────────────────────────────
skill_base = WORKSPACE / "skills" / "md-to-pdf"
scripts_dir = skill_base / "scripts"
styles_dir = skill_base / "styles"
references_dir = skill_base / "references"
for d in [scripts_dir, styles_dir, references_dir]:
    d.mkdir(parents=True, exist_ok=True)

# md2pdf.sh script (realistic implementation)
md2pdf_sh = scripts_dir / "md2pdf.sh"
md2pdf_sh.write_text(textwrap.dedent(r"""
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
STYLES_DIR="$BASE_DIR/styles"

INPUT_MD=""
OUTPUT_PDF=""
STYLE="clean"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --style)
            STYLE="$2"
            shift 2
            ;;
        *.md)
            INPUT_MD="$1"
            shift
            ;;
        *.pdf)
            OUTPUT_PDF="$1"
            shift
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

if [[ -z "$INPUT_MD" ]]; then
    echo "Error: No input .md file specified." >&2
    exit 1
fi

if [[ -z "$OUTPUT_PDF" ]]; then
    OUTPUT_PDF="${INPUT_MD%.md}.pdf"
fi

# Resolve CSS
if [[ -f "$STYLE" ]]; then
    CSS_FILE="$STYLE"
elif [[ -f "$STYLES_DIR/${STYLE}.css" ]]; then
    CSS_FILE="$STYLES_DIR/${STYLE}.css"
else
    echo "Error: Style '$STYLE' not found." >&2
    exit 1
fi

echo "Converting: $INPUT_MD -> $OUTPUT_PDF (style: $STYLE)"

TMP_HTML=$(mktemp /tmp/md2pdf_XXXXXX.html)
trap "rm -f '$TMP_HTML'" EXIT

pandoc "$INPUT_MD" \
    --standalone \
    --css="$CSS_FILE" \
    --metadata title="$(basename "${INPUT_MD%.md}")" \
    -o "$TMP_HTML"

wkhtmltopdf \
    --enable-local-file-access \
    --quiet \
    "$TMP_HTML" \
    "$OUTPUT_PDF"

echo "Done: $OUTPUT_PDF"
""").lstrip())
md2pdf_sh.chmod(0o755)

# Built-in CSS styles
(styles_dir / "clean.css").write_text(textwrap.dedent("""
body { font-family: Arial, sans-serif; font-size: 12pt; color: #222; margin: 40px; }
h1 { border-bottom: 2px solid #444; padding-bottom: 6px; }
h2 { color: #444; }
code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
pre { background: #f4f4f4; padding: 12px; border-radius: 4px; }
""").lstrip())

(styles_dir / "modern.css").write_text(textwrap.dedent("""
body { font-family: 'Helvetica Neue', Helvetica, sans-serif; font-size: 13pt; color: #1a1a2e; margin: 48px; }
h1 { color: #0057b8; border-bottom: 3px solid #0057b8; padding-bottom: 8px; font-size: 2em; }
h2 { color: #0057b8; font-size: 1.4em; margin-top: 32px; }
h3 { color: #333; }
code { background: #eef4ff; color: #003d7a; padding: 2px 5px; border-radius: 3px; }
pre { background: #eef4ff; padding: 14px; border-radius: 5px; }
blockquote { border-left: 4px solid #0057b8; padding-left: 16px; color: #555; }
""").lstrip())

(styles_dir / "paper.css").write_text(textwrap.dedent("""
body { font-family: 'Georgia', serif; font-size: 12pt; color: #111; margin: 60px; line-height: 1.8; }
h1 { font-size: 1.8em; text-align: center; margin-bottom: 4px; }
h2 { font-size: 1.3em; margin-top: 28px; border-bottom: 1px solid #999; }
code { font-family: monospace; font-size: 0.9em; }
pre { background: #f9f9f9; padding: 10px; border: 1px solid #ddd; }
""").lstrip())

# references/usage.md
(references_dir / "usage.md").write_text(textwrap.dedent("""
# md-to-pdf Usage Reference

## Basic Conversion
    bash scripts/md2pdf.sh /abs/path/doc.md

## Style Options
Named styles: clean, modern, paper

## Custom CSS
Pass absolute path to --style:
    bash scripts/md2pdf.sh /abs/path/doc.md /abs/path/out.pdf --style /abs/path/custom.css

## Metadata
Add YAML frontmatter to suppress title warnings:
    ---
    title: "My Document"
    ---

## Local File Access
wkhtmltopdf is invoked with --enable-local-file-access automatically.
""").lstrip())

# ── Distractor directory structure ───────────────────────────────────────────
distractors = [
    ("institute/archive/2022/q1_report_draft.md", "# Q1 2022 Draft\nOld draft, not for publication."),
    ("institute/archive/2022/q2_notes.txt", "Meeting notes from Q2 2022."),
    ("institute/archive/2023/annual_summary.md", "# Annual Summary 2023\nPlaceholder."),
    ("institute/assets/logo.png.b64", "iVBORw0KGgoAAAANSUhEUgAAAAUA"),  # fake base64
    ("institute/assets/fonts/README.txt", "Custom fonts go here."),
    ("institute/templates/old_template.html", "<html><body>Legacy template</body></html>"),
    ("institute/templates/cover_page.tex", r"\begin{document}\maketitle\end{document}"),
    ("institute/scripts/legacy_convert.py", "# Old conversion script - deprecated\nimport subprocess\n"),
    ("institute/config/build.yaml", "output_dir: dist/\nformat: pdf\n"),
    ("institute/config/pandoc_old.json", '{"standalone": true, "toc": false}'),
    ("institute/dist/.gitkeep", ""),
    ("institute/docs/internal/style_guide.txt", "Use Arial 12pt for all documents."),
]

for rel_path, content in distractors:
    fp = WORKSPACE / rel_path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)

# ── Task inputs ──────────────────────────────────────────────────────────────
reports_dir = WORKSPACE / "institute" / "reports" / "q3_2024"
reports_dir.mkdir(parents=True, exist_ok=True)

# Report 1: stakeholder_summary.md — to be converted with "modern" style
# INTENTIONALLY missing YAML frontmatter title (agent must add it)
(reports_dir / "stakeholder_summary.md").write_text(textwrap.dedent("""
## Q3 2024 Research Highlights

The institute achieved significant milestones this quarter, including three peer-reviewed
publications and two successful grant renewals totalling **€1.2M**.

### Key Achievements

- Publication in *Nature Communications* on quantum error correction
- Partnership established with TechVentures GmbH
- Expanded computing cluster to **512 nodes**

### Financial Overview

| Category        | Budget (€) | Spent (€) | Variance |
|-----------------|-----------|-----------|----------|
| Personnel       | 400,000   | 388,500   | +11,500  |
| Equipment       | 150,000   | 147,200   | +2,800   |
| Travel          | 30,000    | 28,750    | +1,250   |
| Overhead        | 120,000   | 120,000   | 0        |

### Outlook

Q4 will focus on finalising the EU Horizon 2025 proposal and onboarding
two postdoctoral researchers in the AI & Materials division.
""").lstrip())

# Report 2: technical_report.md — to be converted with CUSTOM CSS
# Also intentionally missing YAML frontmatter title
(reports_dir / "technical_report.md").write_text(textwrap.dedent("""
## Cluster Performance Analysis — Q3 2024

This report documents the computational performance metrics for the institute's HPC cluster
following the August 2024 hardware upgrade.

### Methodology

Performance was measured using the **LINPACK HPL** benchmark suite across all 512 nodes.
Each node runs dual Intel Xeon Platinum 8480+ CPUs with 512 GB DDR5 RAM.

### Results

```
HPL Score:   4.82 PFlops (peak theoretical: 6.14 PFlops)
Efficiency:  78.5%
MPI tasks:   32,768
Runtime:     14m 22s
```

### Bottlenecks Identified

1. **InfiniBand fabric saturation** at >90% load — recommend upgrading to NDR400
2. **Storage I/O** limited by aging Lustre configuration — tuning in progress
3. **Job scheduler** (SLURM 23.02) upgrade pending to resolve reservation conflicts

### Recommendations

Deploy NDR400 InfiniBand by Q1 2025. Allocate €85,000 from the equipment reserve fund.
""").lstrip())

# Custom CSS for the technical report (branded)
branded_css = WORKSPACE / "institute" / "assets" / "branded.css"
branded_css.write_text(textwrap.dedent("""
body {
    font-family: 'Courier New', monospace;
    font-size: 11pt;
    color: #0a0a0a;
    margin: 50px;
    background-color: #fafafa;
}
h1, h2 {
    color: #8b0000;
    border-bottom: 2px solid #8b0000;
}
h3 { color: #333; font-size: 1.1em; }
code, pre {
    background: #fff3f3;
    color: #8b0000;
    padding: 3px 6px;
    border-radius: 2px;
    font-size: 0.95em;
}
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 6px 10px; }
th { background: #8b0000; color: white; }
""").lstrip())

print("Workspace generated successfully.")
print(f"Skill base: {skill_base}")
print(f"Reports: {reports_dir}")
print(f"Branded CSS: {branded_css}")