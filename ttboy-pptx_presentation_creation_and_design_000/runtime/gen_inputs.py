import os
import json
import random
from pathlib import Path

random.seed(42)

BASE = "/workspace"

# Create realistic nested directory structure with distractor files
dirs = [
    "scripts/office",
    "scripts",
    "assets/images",
    "assets/data",
    "assets/fonts",
    "docs/internal",
    "docs/external",
    "archive/2023",
    "archive/2024",
    "templates",
    "output",
    "reports/q1",
    "reports/q2",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# Distractor files that look plausible but are irrelevant
distractors = {
    "docs/internal/meeting_notes_march.txt": "Discussed Series A timeline. Target raise: $8M. Lead investor TBD.",
    "docs/internal/branding_guidelines.txt": "Primary brand color: #2C5F2D. Secondary: #97BC62. Do not use Comic Sans.",
    "docs/external/press_release_draft.txt": "GreenWave Energy announces breakthrough in solar panel efficiency.",
    "archive/2023/old_deck_notes.txt": "Deck from 2023 seed round. Outdated numbers. Do not use.",
    "archive/2024/investor_feedback.txt": "Investors liked the market slide. Revenue chart was confusing. Fix for Series A.",
    "assets/data/raw_financials.csv": "Quarter,Revenue,Costs\nQ1 2023,120000,98000\nQ2 2023,145000,102000\nQ3 2023,178000,115000\nQ4 2023,210000,125000\nQ1 2024,265000,138000\nQ2 2024,310000,150000",
    "assets/data/market_research.json": json.dumps({
        "global_solar_market_size_2024_usd_billion": 234,
        "cagr_percent": 8.9,
        "target_segment": "Commercial rooftop installations",
        "tam_usd_billion": 87,
        "sam_usd_billion": 12,
        "som_usd_billion": 0.9,
        "key_competitors": ["SolarEdge", "Enphase", "SunPower"],
        "differentiator": "AI-driven yield optimization software layer"
    }),
    "assets/data/team_bios.json": json.dumps([
        {"name": "Dr. Aisha Mensah", "title": "CEO & Co-Founder", "background": "PhD MIT Energy Systems, ex-Tesla Powerwall lead"},
        {"name": "Rajiv Nair", "title": "CTO & Co-Founder", "background": "MSc Stanford CS, ex-Google DeepMind climate team"},
        {"name": "Sofia Andersson", "title": "CFO", "background": "MBA Wharton, ex-Goldman Sachs Clean Energy IB"},
        {"name": "Marcus Webb", "title": "VP Sales", "background": "15 years enterprise solar sales, closed $200M+ deals"}
    ]),
    "assets/data/traction_metrics.json": json.dumps({
        "pilots_active": 14,
        "avg_yield_improvement_percent": 22,
        "letters_of_intent": 6,
        "total_pipeline_usd": 4200000,
        "monthly_recurring_revenue_usd": 38000,
        "year_founded": 2022
    }),
    "reports/q1/q1_summary.txt": "Q1 2024 revenue $265K, ahead of plan. Key win: Munich RE pilot signed.",
    "reports/q2/q2_summary.txt": "Q2 2024 revenue $310K. 4 new pilots onboarded. MRR hit $38K milestone.",
    "templates/placeholder_note.txt": "No approved template exists for this deck. Create from scratch.",
    "assets/fonts/font_options.txt": "Approved header fonts: Georgia, Trebuchet MS, Calibri\nApproved body fonts: Calibri, Calibri Light",
}

for path, content in distractors.items():
    full_path = os.path.join(BASE, path)
    with open(full_path, "w") as f:
        f.write(content)

# Create the skill scripts that "already exist in workspace" per the rules
# These are mock/stub versions that behave correctly

# scripts/office/unpack.py
unpack_script = '''#!/usr/bin/env python3
"""Unpack a PPTX file into a directory, pretty-printing XML."""
import sys
import zipfile
import os
import shutil
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("Usage: unpack.py input.pptx output_dir/")
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2]
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst, exist_ok=True)
    with zipfile.ZipFile(src, 'r') as z:
        z.extractall(dst)
    # Pretty-print XML files
    import xml.dom.minidom
    for root, dirs, files in os.walk(dst):
        for fname in files:
            if fname.endswith('.xml') or fname.endswith('.rels'):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    dom = xml.dom.minidom.parseString(content.encode('utf-8'))
                    pretty = dom.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')
                    # Remove extra XML declaration if present
                    lines = pretty.split('\\n')
                    if lines[0].startswith('<?xml'):
                        lines[0] = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write('\\n'.join(lines))
                except Exception:
                    pass
    print(f"Unpacked {src} -> {dst}")

if __name__ == '__main__':
    main()
'''

# scripts/office/pack.py
pack_script = '''#!/usr/bin/env python3
"""Repack an unpacked PPTX directory back into a .pptx file."""
import sys
import zipfile
import os

def main():
    if len(sys.argv) < 3:
        print("Usage: pack.py unpacked_dir/ output.pptx [--original original.pptx]")
        sys.exit(1)
    src_dir = sys.argv[1]
    dst = sys.argv[2]
    if os.path.exists(dst):
        os.remove(dst)
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(src_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                arcname = os.path.relpath(fpath, src_dir)
                z.write(fpath, arcname)
    print(f"Packed {src_dir} -> {dst}")

if __name__ == '__main__':
    main()
'''

# scripts/office/soffice.py
soffice_script = '''#!/usr/bin/env python3
"""Wrapper for LibreOffice soffice command."""
import sys
import subprocess
import os

def main():
    args = ["soffice"] + sys.argv[1:]
    result = subprocess.run(args, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
'''

# scripts/add_slide.py
add_slide_script = '''#!/usr/bin/env python3
"""Duplicate a slide or create from layout in an unpacked PPTX."""
import sys
import os
import shutil
import re
import random
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("Usage: add_slide.py unpacked_dir/ slideN.xml")
        sys.exit(1)
    unpacked = sys.argv[1]
    slide_ref = sys.argv[2]
    slides_dir = os.path.join(unpacked, 'ppt', 'slides')
    existing = sorted([f for f in os.listdir(slides_dir) if re.match(r'slide\\d+\\.xml$', f)],
                      key=lambda x: int(re.search(r'\\d+', x).group()))
    next_num = int(re.search(r'\\d+', existing[-1]).group()) + 1 if existing else 1
    new_slide = f'slide{next_num}.xml'
    src = os.path.join(slides_dir, slide_ref)
    dst = os.path.join(slides_dir, new_slide)
    shutil.copy(src, dst)
    # Copy rels
    rels_dir = os.path.join(slides_dir, '_rels')
    src_rels = os.path.join(rels_dir, slide_ref + '.rels')
    if os.path.exists(src_rels):
        shutil.copy(src_rels, os.path.join(rels_dir, new_slide + '.rels'))
    rid = random.randint(300, 999)
    print(f'<p:sldId id="{rid}" r:id="rId{next_num}"/>')
    print(f"New slide: {new_slide}")

if __name__ == '__main__':
    main()
'''

# scripts/clean.py
clean_script = '''#!/usr/bin/env python3
"""Remove orphaned slides and media from an unpacked PPTX."""
import sys
import os
import re

def main():
    if len(sys.argv) < 2:
        print("Usage: clean.py unpacked_dir/")
        sys.exit(1)
    unpacked = sys.argv[1]
    pres_xml = os.path.join(unpacked, 'ppt', 'presentation.xml')
    with open(pres_xml, 'r', encoding='utf-8') as f:
        content = f.read()
    referenced = set(re.findall(r'slide(\\d+)\\.xml', content))
    slides_dir = os.path.join(unpacked, 'ppt', 'slides')
    removed = 0
    for fname in os.listdir(slides_dir):
        m = re.match(r'slide(\\d+)\\.xml$', fname)
        if m and m.group(1) not in referenced:
            os.remove(os.path.join(slides_dir, fname))
            removed += 1
    print(f"Cleaned {removed} orphaned slide(s).")

if __name__ == '__main__':
    main()
'''

# scripts/thumbnail.py
thumbnail_script = '''#!/usr/bin/env python3
"""Create a thumbnail grid from a PPTX file."""
import sys
print("thumbnail.py: For visual QA use soffice + pdftoppm. For template analysis, this creates thumbnails.jpg")
print("Note: This stub outputs a placeholder. In production, uses LibreOffice to render slides.")
'''

scripts = {
    "scripts/office/unpack.py": unpack_script,
    "scripts/office/pack.py": pack_script,
    "scripts/office/soffice.py": soffice_script,
    "scripts/add_slide.py": add_slide_script,
    "scripts/clean.py": clean_script,
    "scripts/thumbnail.py": thumbnail_script,
}

for path, content in scripts.items():
    full_path = os.path.join(BASE, path)
    with open(full_path, "w") as f:
        f.write(content)

# Create SKILL.md and referenced docs at workspace root
skill_md_note = """# Skills available
See editing.md and pptxgenjs.md for pptx creation workflows.
"""

with open(os.path.join(BASE, "README_SKILLS.txt"), "w") as f:
    f.write(skill_md_note)

# Create the actual task brief for the agent
task_brief = """TASK BRIEF: GreenWave Energy — Series A Investor Pitch Deck

Please create a 5-slide investor pitch deck for GreenWave Energy, our climate tech startup.
Save it as: greenwave_pitch.pptx

The deck should cover:
1. Title slide — Company name "GreenWave Energy", tagline "AI-Powered Solar Yield Optimization", and founding year
2. Market Opportunity — TAM ($87B), SAM ($12B), SOM ($0.9B) with the global solar market size ($234B) and CAGR (8.9%)
3. Traction — Key metrics: 14 active pilots, 22% avg yield improvement, 6 LOIs, $4.2M pipeline, $38K MRR
4. Team — All 4 team members with their titles and backgrounds
5. Revenue chart slide — Show quarterly revenue from Q1 2023 through Q2 2024 using a bar chart

Design requirements:
- Use the Forest & Moss color palette (it fits the climate theme)
- Each slide must have at least one visual element (shape, chart, or icon)
- Card-style layouts for the team slide (one card per person)
- The traction slide should use large stat callouts
- Two or more slides should have drop shadows on card/shape elements

The data files are in assets/data/.
"""

with open(os.path.join(BASE, "task_brief.txt"), "w") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in Path(BASE).rglob('*') if _.is_file())}")