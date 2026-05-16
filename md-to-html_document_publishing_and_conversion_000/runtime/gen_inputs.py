import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create the md-to-html skill directory structure ---
skill_root = workspace / "md-to-html"
scripts_dir = skill_root / "scripts"
lib_dir = skill_root / "lib"

for d in [scripts_dir, lib_dir]:
    d.mkdir(parents=True, exist_ok=True)

# Create a realistic md2html.py script
md2html_script = r'''#!/usr/bin/env python3
"""
Markdown to HTML converter with fixed left-side TOC.
"""
import argparse
import os
import re
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    print("Error: 'markdown' package not installed. Run: pip install markdown")
    sys.exit(1)

LIB_DIR = Path(__file__).parent.parent / "lib"

def load_lib(filename):
    p = LIB_DIR / filename
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""

def extract_headings(md_text, max_level=4):
    headings = []
    for line in md_text.split("\n"):
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            if level <= max_level:
                text = m.group(2).strip()
                anchor = re.sub(r'[^\w\u4e00-\u9fff\- ]', '', text)
                anchor = re.sub(r'\s+', '-', anchor).strip('-').lower()
                headings.append((level, text, anchor))
    return headings

def build_toc(headings):
    if not headings:
        return "<p style='color:#999;font-size:12px;'>No headings found.</p>"
    toc_items = []
    for level, text, anchor in headings:
        indent = (level - 1) * 14
        toc_items.append(
            f'<div class="toc-item toc-level-{level}" style="padding-left:{indent}px">'
            f'<a href="#{anchor}" class="toc-link">{text}</a></div>'
        )
    return "\n".join(toc_items)

def add_heading_ids(html_content, headings):
    used = {}
    result = html_content
    for level, text, anchor in headings:
        key = anchor
        if key in used:
            used[key] += 1
            key = f"{anchor}-{used[key]}"
        else:
            used[anchor] = 0
        pattern = re.compile(
            r'(<h' + str(level) + r')(>|\s[^>]*>)(.*?</h' + str(level) + r'>)',
            re.IGNORECASE | re.DOTALL
        )
        def replacer(m, _anchor=key):
            return f'<h{level} id="{_anchor}">{m.group(3)}'
        result, n = pattern.subn(replacer, result, count=1)
    return result

def convert(input_path, output_path=None, title=None, level=4):
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    md_text = input_path.read_text(encoding="utf-8")

    if output_path is None:
        output_path = input_path.with_suffix(".html")
    else:
        output_path = Path(output_path).resolve()

    if title is None:
        title = input_path.stem

    output_path.parent.mkdir(parents=True, exist_ok=True)

    headings = extract_headings(md_text, max_level=level)
    toc_html = build_toc(headings)

    md_obj = markdown.Markdown(extensions=["tables", "fenced_code", "codehilite", "toc"])
    body_html = md_obj.convert(md_text)
    body_html = add_heading_ids(body_html, headings)

    prism_css = load_lib("prism-tomorrow.min.css")
    prism_js = load_lib("prism.min.js")
    katex_css = load_lib("katex.embedded.css")
    katex_js = load_lib("katex.min.js")
    autorender_js = load_lib("auto-render.min.js")

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{prism_css}
{katex_css}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ display: flex; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; color: #333; }}
#sidebar {{ width: 260px; min-width: 180px; max-width: 400px; height: 100vh; position: fixed; top: 0; left: 0; background: #fff; border-right: 1px solid #e0e0e0; overflow-y: auto; padding: 16px 0; z-index: 100; }}
#sidebar-header {{ padding: 12px 16px 8px; font-weight: 700; font-size: 15px; color: #222; border-bottom: 1px solid #f0f0f0; margin-bottom: 8px; }}
.toc-item {{ padding: 4px 16px; }}
.toc-link {{ text-decoration: none; color: #555; font-size: 13px; display: block; padding: 3px 4px; border-radius: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.toc-link:hover {{ background: #f0f0f0; color: #1a73e8; }}
.toc-link.active {{ background: #e8f0fe; color: #1a73e8; font-weight: 600; }}
#content {{ margin-left: 260px; padding: 40px 48px; max-width: 960px; width: 100%; min-height: 100vh; background: #fff; }}
h1,h2,h3,h4,h5,h6 {{ margin-top: 1.5em; margin-bottom: 0.6em; line-height: 1.3; }}
h1 {{ font-size: 2em; border-bottom: 2px solid #e0e0e0; padding-bottom: 0.3em; }}
h2 {{ font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }}
p {{ line-height: 1.7; margin-bottom: 1em; }}
code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-size: 0.9em; }}
pre {{ background: #2d2d2d; border-radius: 6px; padding: 16px; overflow-x: auto; margin-bottom: 1em; }}
pre code {{ background: none; color: #ccc; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 1em; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; }}
th {{ background: #f4f4f4; }}
blockquote {{ border-left: 4px solid #1a73e8; background: #f8f9ff; padding: 10px 16px; margin-bottom: 1em; color: #555; }}
#back-to-top {{ position: fixed; bottom: 24px; right: 24px; background: #1a73e8; color: #fff; border: none; border-radius: 50%; width: 44px; height: 44px; font-size: 20px; cursor: pointer; display: none; z-index: 200; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
</style>
</head>
<body>
<div id="sidebar">
  <div id="sidebar-header">📋 目录</div>
  <div id="toc">
{toc_html}
  </div>
</div>
<div id="content">
{body_html}
</div>
<button id="back-to-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>
<script>
{prism_js}
{katex_js}
{autorender_js}
</script>
<script>
// TOC active highlight
const tocLinks = document.querySelectorAll('.toc-link');
const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6')).filter(h=>h.id);
window.addEventListener('scroll', () => {{
  let current = '';
  for (const h of headings) {{
    if (h.getBoundingClientRect().top <= 80) current = h.id;
  }}
  tocLinks.forEach(a => {{
    a.classList.toggle('active', a.getAttribute('href') === '#'+current);
  }});
  document.getElementById('back-to-top').style.display = window.scrollY > 200 ? 'block' : 'none';
}});
// KaTeX
if (typeof renderMathInElement !== 'undefined') {{
  renderMathInElement(document.getElementById('content'), {{
    delimiters: [
      {{left:'$$',right:'$$',display:true}},
      {{left:'$',right:'$',display:false}}
    ]
  }});
}}
</script>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"✅ HTML generated: {output_path}")
    return str(output_path)

def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to HTML with TOC")
    parser.add_argument('-i', '--input', required=True, help='Input Markdown file')
    parser.add_argument('-o', '--output', default=None, help='Output HTML file')
    parser.add_argument('-t', '--title', default=None, help='HTML page title')
    parser.add_argument('-l', '--level', type=int, default=4, choices=range(1,7),
                        help='Max heading level in TOC (1-6, default 4)')
    args = parser.parse_args()
    convert(args.input, args.output, args.title, args.level)

if __name__ == '__main__':
    main()
'''

(scripts_dir / "md2html.py").write_text(md2html_script, encoding="utf-8")

# Create stub lib files (minimal content for offline use)
lib_files = {
    "prism-tomorrow.min.css": "/* prism tomorrow theme stub */",
    "prism.min.js": "/* prism core stub */",
    "prism-python.min.js": "/* prism python stub */",
    "prism-bash.min.js": "/* prism bash stub */",
    "prism-javascript.min.js": "/* prism js stub */",
    "prism-json.min.js": "/* prism json stub */",
    "mermaid.min.js": "/* mermaid stub */",
    "katex.min.js": "/* katex stub */",
    "katex.embedded.css": "/* katex css stub */",
    "auto-render.min.js": "/* auto-render stub */",
}
for fname, content in lib_files.items():
    (lib_dir / fname).write_text(content, encoding="utf-8")

# --- Create the target Markdown file ---
protocol_md = """# CRISPR Gene Editing Protocol v3.2

## Overview

This document describes the standard operating procedure for CRISPR-Cas9 gene editing in mammalian cell lines used at BioSpark Research Institute.

## Safety Requirements

All procedures must be carried out in a BSL-2 certified laboratory. Personal protective equipment (PPE) including gloves, lab coat, and eye protection is mandatory.

### Chemical Hazards

- Ethidium bromide is a known mutagen; handle with care.
- Liquid nitrogen requires cryogenic gloves.

### Biological Hazards

Work with lentiviral vectors requires prior approval from the biosafety committee.

## Materials and Equipment

### Reagents

The following reagents are required for this protocol:

- Cas9 protein (10 µg/µL stock)
- sgRNA (100 µM stock)
- Electroporation buffer
- Cell culture media (DMEM + 10% FBS)
- Puromycin (1 mg/mL stock)

### Equipment List

- Nucleofector device (Lonza)
- Biosafety cabinet (Class II)
- CO2 incubator (37°C, 5% CO2)
- Fluorescence microscope
- Flow cytometer

## Procedure

### Step 1: sgRNA Design and Validation

Design sgRNA sequences using the Benchling or CRISPOR online tool targeting the gene of interest. Validate off-target prediction scores.

#### Criteria for sgRNA Selection

- On-target score > 0.6 (Doench 2016)
- Fewest predicted off-target sites in coding regions
- Avoid sequences with poly-T stretches (>4T)

#### Synthesis and Annealing

Synthesize forward and reverse oligos with appropriate overhangs. Anneal at 95°C for 5 min, ramp down 5°C/min to 25°C.

### Step 2: RNP Complex Assembly

Combine Cas9 protein and sgRNA at a molar ratio of 1:2.5. Incubate at room temperature for 10 minutes.

#### Quality Check

Verify RNP assembly by native PAGE gel shift assay before proceeding.

### Step 3: Cell Preparation

Culture target cells to 70-80% confluency. Harvest using 0.25% Trypsin-EDTA. Count cells and resuspend at 2×10⁶ cells/mL in electroporation buffer.

#### Viability Assessment

Cell viability must be >85% (Trypan Blue exclusion) before proceeding.

### Step 4: Electroporation

Transfer 100 µL of cell suspension (2×10⁵ cells) to nucleofection cuvette. Add RNP complex. Run program CM-130 on the Nucleofector device.

### Step 5: Recovery and Selection

Transfer cells to pre-warmed media immediately after electroporation. Incubate 48 hours before adding puromycin for selection.

#### Selection Timeline

| Day | Action |
|-----|--------|
| 0   | Electroporation |
| 2   | Add puromycin (2 µg/mL) |
| 5   | Replace media + puromycin |
| 10  | Screen surviving colonies |

## Analysis and Verification

### PCR Screening

Design primers flanking the target site (150-300 bp amplicon). Run PCR on genomic DNA extracted from single clones.

### Sanger Sequencing

Submit PCR products for Sanger sequencing. Analyze with TIDE or ICE software to assess editing efficiency.

### Western Blot Confirmation

Confirm protein knockout by Western blot using appropriate primary antibody.

## Troubleshooting

### Low Editing Efficiency

- Check sgRNA quality by running on bioanalyzer
- Ensure Cas9 protein is active (test with in vitro cleavage assay)
- Optimize electroporation parameters

### High Cell Death

- Reduce RNP concentration
- Check cell viability before electroporation
- Use nucleofection buffer appropriate for cell type

## Data Recording

All experiments must be recorded in the electronic lab notebook (ELN) system within 24 hours of completion. Include lot numbers for all reagents, instrument calibration dates, and raw data files.

## References

1. Ran, F.A. et al. (2013). Genome engineering using the CRISPR-Cas9 system. *Nature Protocols*, 8(11), 2281-2308.
2. Doench, J.G. et al. (2016). Optimized sgRNA design to maximize activity and minimize off-target effects. *Nature Biotechnology*, 34, 184-191.
3. Komor, A.C. et al. (2017). CRISPR-based technologies for the manipulation of eukaryotic genomes. *Cell*, 169(4), 559-574.
"""

# Place the protocol markdown in the workspace root (not inside skill directory)
(workspace / "crispr_protocol_v3.md").write_text(protocol_md, encoding="utf-8")

# --- Create distractor files to simulate a realistic lab workspace ---
distractor_dirs = [
    workspace / "experiments" / "2024-Q1",
    workspace / "experiments" / "2024-Q2",
    workspace / "data" / "sequencing" / "batch_07",
    workspace / "data" / "flow_cytometry",
    workspace / "reports" / "internal",
    workspace / "reports" / "external",
    workspace / "scripts" / "analysis",
    workspace / "references",
    workspace / "protocols" / "archive",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    workspace / "experiments" / "2024-Q1" / "exp001_results.csv": "sample,efficiency\nHEK293T,0.72\nK562,0.58",
    workspace / "experiments" / "2024-Q1" / "exp002_notes.txt": "Repeat with lower RNP concentration.",
    workspace / "experiments" / "2024-Q2" / "exp010_viability.csv": "day,viability\n0,0.92\n2,0.85\n5,0.78",
    workspace / "data" / "sequencing" / "batch_07" / "sample01.fastq.gz.md5": "d41d8cd98f00b204e9800998ecf8427e",
    workspace / "data" / "sequencing" / "batch_07" / "alignment_report.txt": "Total reads: 12,450,000\nAligned: 98.3%",
    workspace / "data" / "flow_cytometry" / "gating_strategy.txt": "Gate on FSC/SSC, then live/dead, then GFP+",
    workspace / "reports" / "internal" / "monthly_summary_jan2024.docx.stub": "[binary stub]",
    workspace / "reports" / "external" / "grant_progress_report.txt": "Milestone 2 achieved ahead of schedule.",
    workspace / "scripts" / "analysis" / "tide_analysis.py": "# TIDE analysis script\n# Usage: python tide_analysis.py <ab1_file>",
    workspace / "scripts" / "analysis" / "ice_parser.py": "# ICE output parser\n# Parses JSON output from Synthego ICE",
    workspace / "references" / "key_papers.bib": "@article{Ran2013, title={Genome engineering...}, year={2013}}",
    workspace / "protocols" / "archive" / "crispr_protocol_v1.md": "# CRISPR Protocol v1.0\n## Old version - superseded",
    workspace / "protocols" / "archive" / "crispr_protocol_v2.md": "# CRISPR Protocol v2.1\n## Deprecated - use v3.2",
}

for fpath, content in distractor_files.items():
    fpath.write_text(content, encoding="utf-8")

# Create a README-like file that does NOT hint at the solution
(workspace / "LAB_INVENTORY.txt").write_text(
    "Lab Workspace Inventory\n"
    "=======================\n"
    "This directory contains experimental data, analysis scripts, and protocols.\n"
    "Contact: biospark-it@example.com\n",
    encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Target MD file: {workspace / 'crispr_protocol_v3.md'}")