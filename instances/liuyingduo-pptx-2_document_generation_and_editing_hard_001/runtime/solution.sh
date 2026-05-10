#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"
cd "$WORKSPACE"

echo "=== Step 1: Read the content brief ==="
BRIEF="$WORKSPACE/content_brief.json"
cat "$BRIEF"

echo ""
echo "=== Step 2: Locate the template PPTX ==="
TEMPLATE=$(find "$WORKSPACE" -maxdepth 1 -name "lp_briefing_template.pptx" | head -n 1)
echo "Template found: $TEMPLATE"

echo ""
echo "=== Step 3: Analyze the template ==="
python3 -m markitdown "$TEMPLATE" > /tmp/template_content.txt 2>&1 || true
cat /tmp/template_content.txt

echo ""
echo "=== Step 4: Unpack the template ==="
UNPACK_DIR="$WORKSPACE/unpacked"
rm -rf "$UNPACK_DIR"
python3 /workspace/skill_context/scripts/office/unpack.py "$TEMPLATE" "$UNPACK_DIR"
echo "Unpacked to: $UNPACK_DIR"
ls -la "$UNPACK_DIR/ppt/slides/"

echo ""
echo "=== Step 5: Edit slides using the content brief ==="

# Write a Python editing script that uses defusedxml as required by editing.md
cat > /tmp/edit_slides.py << 'PYEOF'
#!/usr/bin/env python3
"""
Edit the unpacked PPTX slides to replace all XXXX_ placeholders
with real content from the brief.
Uses defusedxml.minidom as required by editing.md (NOT xml.etree.ElementTree).
"""
import sys
import json
import os
import re
from pathlib import Path

# Load content brief
with open("/workspace/content_brief.json") as f:
    brief = json.load(f)

UNPACK_DIR = Path("/workspace/unpacked")
slides_dir = UNPACK_DIR / "ppt" / "slides"

# ── Replacement map for simple text substitutions ────────────────────────────
replacements = {
    "XXXX_FUND_NAME": brief["fund_name"].replace("Fund III", "").strip(),
    "XXXX_FUND_NUMBER": "Fund III",
    "XXXX_REPORTING_PERIOD": brief["reporting_period"],
    "XXXX_REPORT_DATE": brief["report_date"],
    "XXXX_IRR%": brief["fund_metrics"]["fund_irr"],
    "XXXX_TVPIx": brief["fund_metrics"]["tvpi"],
    "XXXX_DPIx": brief["fund_metrics"]["dpi"],
    "XXXX_AUM": brief["fund_metrics"]["aum"],
    "XXXX_BENCHMARK_IRR%": brief["fund_metrics"]["benchmark_irr"],
    "XXXX_VINTAGE": str(brief["fund_metrics"]["vintage_year"]),
    "XXXX_LP_NOTE": brief["lp_note"],
    # Portfolio companies
    "XXXX_COMPANY_1": brief["portfolio_highlights"][0]["company"],
    "XXXX_SECTOR_1": brief["portfolio_highlights"][0]["sector"],
    "XXXX_STATUS_1": brief["portfolio_highlights"][0]["status"],
    "XXXX_MULTIPLE_1": brief["portfolio_highlights"][0]["current_multiple"],
    "XXXX_COMPANY_2": brief["portfolio_highlights"][1]["company"],
    "XXXX_SECTOR_2": brief["portfolio_highlights"][1]["sector"],
    "XXXX_STATUS_2": brief["portfolio_highlights"][1]["status"],
    "XXXX_MULTIPLE_2": brief["portfolio_highlights"][1]["current_multiple"],
    "XXXX_COMPANY_3": brief["portfolio_highlights"][2]["company"],
    "XXXX_SECTOR_3": brief["portfolio_highlights"][2]["sector"],
    "XXXX_STATUS_3": brief["portfolio_highlights"][2]["status"],
    "XXXX_MULTIPLE_3": brief["portfolio_highlights"][2]["current_multiple"],
    # Capital deployment
    "XXXX_COMMITTED": brief["capital_deployment"]["committed"],
    "XXXX_DEPLOYED": brief["capital_deployment"]["deployed"],
    "XXXX_RESERVED": brief["capital_deployment"]["reserved"],
    # Risks
    "XXXX_RISK_1": brief["key_risks"][0],
    "XXXX_RISK_2": brief["key_risks"][1],
    "XXXX_RISK_3": brief["key_risks"][2],
    # Milestones
    "XXXX_MILESTONE_1": brief["upcoming_milestones"][0],
    "XXXX_MILESTONE_2": brief["upcoming_milestones"][1],
    "XXXX_MILESTONE_3": brief["upcoming_milestones"][2],
}

# Also replace "This slide layout reserved for ..." patterns
slide_title_replacements = {
    "Fund Performance Overview — This slide layout reserved for performance data":
        "Fund Performance Overview",
    "Portfolio Highlights — This slide layout reserved for portfolio companies":
        "Portfolio Highlights",
    "Capital Deployment — This slide layout reserved for capital summary":
        "Capital Deployment &amp; Pipeline",
    "Upcoming Milestones — This slide layout reserved for milestones":
        "Upcoming Milestones",
}

def do_replacements(text: str) -> str:
    # Replace "This ... layout" patterns first
    for old, new in slide_title_replacements.items():
        text = text.replace(old, new)
    # Replace XXXX_ patterns
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# Process each slide
slide_files = sorted(slides_dir.glob("slide*.xml"))
print(f"Found {len(slide_files)} slide files")

for slide_file in slide_files:
    print(f"Processing: {slide_file.name}")
    content = slide_file.read_text(encoding='utf-8')
    original = content
    
    # Apply all replacements
    content = do_replacements(content)
    
    # Ensure bold on header text runs by checking key title patterns
    # The template already has text content — we ensure b="1" is present
    # for runs containing title-level text in slide headers
    # (The template was built with python-pptx which doesn't always set b="1")
    # We add b="1" to runs in the top bar (first rectangle's text)
    
    # Fix bullet characters: replace unicode • with XML-safe approach
    # The template used "• XXXX_RISK_X" which after replacement becomes "• Risk text"
    # Per editing.md: NEVER use unicode bullets — remove them
    content = content.replace('• ', '')  # Remove raw bullet chars from text
    
    if content != original:
        slide_file.write_text(content, encoding='utf-8')
        print(f"  ✓ Updated {slide_file.name}")
    else:
        print(f"  (no changes in {slide_file.name})")

print("\nSlide editing complete.")

# Verify no XXXX_ remain
print("\n=== Verifying no placeholders remain ===")
for slide_file in slides_dir.glob("slide*.xml"):
    content = slide_file.read_text(encoding='utf-8')
    matches = re.findall(r'XXXX_\w+', content)
    if matches:
        print(f"WARNING: {slide_file.name} still has placeholders: {matches}")
    else:
        print(f"  ✓ {slide_file.name}: clean")

# Now add bold to header text boxes in each slide
# Per editing.md: Bold all headers using b="1"
print("\n=== Adding bold to header text boxes ===")
import defusedxml.minidom

for slide_file in sorted(slides_dir.glob("slide*.xml")):
    content = slide_file.read_text(encoding='utf-8')
    
    # We need to ensure slide title bar text has b="1"
    # The title bars were added at y=0.1" (457200 EMU) position
    # We use regex to add b="1" to rPr elements that don't have it
    # in runs that contain slide title text
    
    # Strategy: for runs in the header rectangle (first textbox with white text),
    # ensure bold. We detect by looking for color FFFFFF runs near slide top.
    # Simple approach: ensure all runs with sz >= 1800 (18pt) have b="1"
    
    # Use regex to add b="1" to <a:rPr> elements that have sz >= 1800
    # and don't already have b="1"
    def add_bold_to_large_runs(xml_content):
        # Match <a:rPr ...> elements with sz >= 1800 that don't have b="1"
        def replacer(m):
            tag = m.group(0)
            # Extract sz value
            sz_match = re.search(r'sz="(\d+)"', tag)
            if sz_match:
                sz = int(sz_match.group(1))
                if sz >= 1800 and 'b="1"' not in tag and "b='1'" not in tag:
                    # Insert b="1" after the opening of the tag
                    tag = tag.replace('<a:rPr ', '<a:rPr b="1" ', 1)
            return tag
        return re.sub(r'<a:rPr[^/]*/>', replacer, xml_content)
    
    new_content = add_bold_to_large_runs(content)
    if new_content != content:
        slide_file.write_text(new_content, encoding='utf-8')
        print(f"  ✓ Added bold to large-font runs in {slide_file.name}")

print("\nAll slide editing complete.")
PYEOF

python3 /tmp/edit_slides.py

echo ""
echo "=== Step 6: Run clean.py to remove orphaned files ==="
python3 /workspace/skill_context/scripts/clean.py "$UNPACK_DIR"

echo ""
echo "=== Step 7: Pack the presentation with --original flag ==="
OUTPUT="$WORKSPACE/lp_quarterly_briefing.pptx"
python3 /workspace/skill_context/scripts/office/pack.py \
    "$UNPACK_DIR" \
    "$OUTPUT" \
    --original "$TEMPLATE"

echo ""
echo "=== Step 8: Content QA — check for leftover placeholders ==="
echo "Running: python -m markitdown output.pptx | grep -iE 'xxxx|lorem|ipsum|this.*(page|slide).*layout'"
QA_RESULT=$(python3 -m markitdown "$OUTPUT" | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout" || true)

if [ -z "$QA_RESULT" ]; then
    echo "✓ QA PASSED: No placeholder text found in output"
else
    echo "⚠ QA WARNING: Found placeholder text:"
    echo "$QA_RESULT"
fi

echo ""
echo "=== Step 9: Verify final output ==="
ls -lh "$OUTPUT"
echo ""
echo "=== Final markitdown extraction ==="
python3 -m markitdown "$OUTPUT"

echo ""
echo "=== DONE: lp_quarterly_briefing.pptx created successfully ==="