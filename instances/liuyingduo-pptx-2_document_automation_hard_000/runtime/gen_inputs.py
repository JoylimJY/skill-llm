#!/usr/bin/env python3
"""
Generates the sandbox workspace for the PPTX editing task.
Creates a realistic biotech investor relations template PPTX with placeholder text,
plus distractor files to test contextual awareness.
"""
import os
import random
import zipfile
import io
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure (distractors) ──────────────────────────────────────
dirs = [
    "archive/q1_2024",
    "archive/q2_2024",
    "data/pipeline",
    "data/financials",
    "comms/investor_letters",
    "comms/press_releases",
    "design/brand_assets",
    "design/templates_old",
    "reports/internal",
    "reports/external",
    "scripts_backup",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ────────────────────────────────────────────────────────
distractor_files = {
    "archive/q1_2024/Q1_summary.txt": "Q1 2024 pipeline summary. Phase 1 trial initiated for BIO-101.",
    "archive/q2_2024/Q2_summary.txt": "Q2 2024 results: BIO-101 Phase 1 complete, BIO-202 IND filed.",
    "archive/q2_2024/Q2_financials.csv": "item,amount\nR&D spend,4200000\nCash runway,18 months",
    "data/pipeline/pipeline_db.json": '{"assets": [{"id": "BIO-101", "phase": 3}, {"id": "BIO-202", "phase": 2}, {"id": "BIO-303", "phase": 1}]}',
    "data/pipeline/trial_sites.csv": "site,country,enrolled\nBoston,USA,45\nLondon,UK,38\nBerlin,Germany,29",
    "data/financials/q3_cash.txt": "Cash position as of Q3: $142.5M. Runway: 24 months.",
    "comms/investor_letters/oct_letter.txt": "Dear Investor, Q3 has been transformative for NovaBio Therapeutics...",
    "comms/press_releases/bio101_ph3.txt": "PRESS RELEASE: NovaBio announces BIO-101 Phase 3 enrollment complete.",
    "design/brand_assets/color_palette.txt": "Primary: #1A3A5C\nAccent: #E8A020\nBackground: #F4F6F8",
    "design/templates_old/old_template_notes.txt": "DEPRECATED: Use pipeline_update_template.pptx for Q3 and beyond.",
    "reports/internal/cmo_update.txt": "CMO Q3 Update: BIO-101 primary endpoint met. BIO-202 dose escalation ongoing.",
    "reports/external/analyst_coverage.txt": "Coverage initiated by Biotech Capital Partners. Target: $28/share.",
    "scripts_backup/old_gen.py": "# Deprecated script for generating old format slides\nprint('deprecated')",
}
for fpath, content in distractor_files.items():
    (WORKSPACE / fpath).write_text(content)

# ── Q3 pipeline content (what the agent must populate into the deck) ────────
q3_content = """NOVABIO THERAPEUTICS — Q3 2024 PIPELINE UPDATE

COMPANY OVERVIEW:
NovaBio Therapeutics is a clinical-stage biopharmaceutical company focused on next-generation oncology treatments. Founded in 2018, headquartered in Boston, MA. 62 employees.

PIPELINE ASSETS:
1. BIO-101 (Lead Asset)
   Indication: Non-Small Cell Lung Cancer (NSCLC)
   Phase: Phase 3
   Status: Enrollment complete (152 patients). Topline data expected Q1 2025.
   Key milestone: Primary endpoint is progression-free survival at 12 months.

2. BIO-202
   Indication: Triple-Negative Breast Cancer (TNBC)
   Phase: Phase 2
   Status: Dose escalation ongoing. 3 of 5 cohorts enrolled.
   Key milestone: Dose expansion decision expected Q4 2024.

3. BIO-303
   Indication: Colorectal Cancer (CRC)
   Phase: Phase 1
   Status: IND cleared. Site activation in progress (4 of 6 sites open).
   Key milestone: First patient dosed expected Q4 2024.

FINANCIALS:
Cash position: $142.5 million (as of September 30, 2024)
Cash runway: Through Q3 2026 (24 months)
Q3 R&D spend: $8.3 million
YTD R&D spend: $23.1 million
Shares outstanding: 48.2 million

KEY Q3 MILESTONES ACHIEVED:
- BIO-101 Phase 3 enrollment completed ahead of schedule
- BIO-202 received FDA Fast Track Designation
- Entered into collaboration agreement with GlobalPharma Inc. (milestone payments up to $180M)
- Appointed Dr. Sarah Chen as Chief Medical Officer

UPCOMING CATALYSTS (Q4 2024 - Q1 2025):
- BIO-101 topline data readout (Q1 2025)
- BIO-202 dose expansion decision (Q4 2024)
- BIO-303 first patient dosed (Q4 2024)

MANAGEMENT TEAM:
CEO: James Hartwell — 20+ years in oncology drug development
CMO: Dr. Sarah Chen — Former VP Clinical Development at Roche
CFO: Maria Santos — Ex-Goldman Sachs biotech investment banking
CSO: Dr. Raj Patel — 15 patents, pioneer in targeted kinase inhibitors
"""

(WORKSPACE / "data/q3_pipeline_content.txt").write_text(q3_content)

# ── Build the PPTX template with placeholder text ──────────────────────────
# We create a valid PPTX from scratch using raw XML/zip construction
# This is a real minimal PPTX with 6 slides and placeholder text

SLIDE_WIDTH  = 9144000   # EMU for 10 inches (16:9)
SLIDE_HEIGHT = 5143500   # EMU for 5.625 inches

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide3.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide4.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide5.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide6.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''

RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''

PRESENTATION_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                saveSubsetFonts="1">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
    <p:sldId id="256" r:id="rId2"/>
    <p:sldId id="257" r:id="rId3"/>
    <p:sldId id="258" r:id="rId4"/>
    <p:sldId id="259" r:id="rId5"/>
    <p:sldId id="260" r:id="rId6"/>
    <p:sldId id="261" r:id="rId7"/>
  </p:sldIdLst>
  <p:sldSz cx="9144000" cy="5143500"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>'''

PRESENTATION_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide2.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide3.xml"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide4.xml"/>
  <Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide5.xml"/>
  <Relationship Id="rId7" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide6.xml"/>
</Relationships>'''

SLIDE_MASTER = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld>
    <p:bg>
      <p:bgRef idx="1001" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
        <a:srgbClr val="FFFFFF"/>
      </p:bgRef>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:txStyles>
    <p:titleStyle>
      <a:lvl1pPr algn="ctr"><a:defRPr b="1" sz="3600"><a:solidFill><a:srgbClr val="1A3A5C"/></a:solidFill></a:defRPr></a:lvl1pPr>
    </p:titleStyle>
    <p:bodyStyle>
      <a:lvl1pPr><a:defRPr sz="1800"><a:solidFill><a:srgbClr val="333333"/></a:solidFill></a:defRPr></a:lvl1pPr>
    </p:bodyStyle>
    <p:otherStyle>
      <a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr>
    </p:otherStyle>
  </p:txStyles>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
    <p:sldLayoutId id="2147483650" r:id="rId2"/>
  </p:sldLayoutIdLst>
</p:sldMaster>'''

SLIDE_MASTER_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout2.xml"/>
</Relationships>'''

SLIDE_LAYOUT1 = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             type="title">
  <p:cSld name="Title Slide">
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>'''

SLIDE_LAYOUT2 = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             type="obj">
  <p:cSld name="Content">
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>'''

LAYOUT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>'''

CORE_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:title>Pipeline Update Template</dc:title>
  <dc:creator>NovaBio IR Team</dc:creator>
</cp:coreProperties>'''

APP_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>Microsoft Office PowerPoint</Application>
  <Slides>6</Slides>
</Properties>'''

def make_slide(slide_id: int, title: str, body_paragraphs: list[tuple[str, bool]]) -> str:
    """
    body_paragraphs: list of (text, is_bold) tuples
    """
    body_xml = ""
    for text, bold in body_paragraphs:
        b_attr = ' b="1"' if bold else ''
        body_xml += f'''      <a:p>
        <a:pPr algn="l"><a:lnSpc><a:spcPts val="2000"/></a:lnSpc></a:pPr>
        <a:r><a:rPr lang="en-US" sz="1800"{b_attr} dirty="0"/><a:t>{text}</a:t></a:r>
      </a:p>
'''

    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_WIDTH}" cy="{SLIDE_HEIGHT}"/><a:chOff x="0" y="0"/><a:chExt cx="{SLIDE_WIDTH}" cy="{SLIDE_HEIGHT}"/></a:xfrm></p:grpSpPr>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Title {slide_id}"/>
          <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
          <p:nvPr><p:ph type="title"/></p:nvPr>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="457200" y="274638"/><a:ext cx="8229600" cy="1143000"/></a:xfrm>
        </p:spPr>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p><a:r><a:rPr lang="en-US" sz="3600" b="1" dirty="0"/><a:t>{title}</a:t></a:r></a:p>
        </p:txBody>
      </p:sp>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="3" name="Body {slide_id}"/>
          <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
          <p:nvPr><p:ph idx="1"/></p:nvPr>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="457200" y="1600200"/><a:ext cx="8229600" cy="3200400"/></a:xfrm>
        </p:spPr>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
{body_xml}        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''

def make_slide_rels(slide_num: int) -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout2.xml"/>
</Relationships>'''

# Define 6 template slides with placeholder "XXXX" content
slides_data = [
    # Slide 1: Title slide
    (1, "XXXX Company Name — XXXX Quarter XXXX Pipeline Update", [
        ("XXXX Date | Investor Presentation", False),
        ("Confidential — Not for Distribution", False),
    ]),
    # Slide 2: Company overview (KEEP — populate)
    (2, "Company Overview", [
        ("XXXX Company Name is a clinical-stage biopharmaceutical company focused on XXXX.", False),
        ("Founded: XXXX | HQ: XXXX | Employees: XXXX", False),
        ("Mission: XXXX lorem ipsum mission statement goes here.", False),
    ]),
    # Slide 3: Pipeline summary (KEEP — populate)
    (3, "Pipeline Overview", [
        ("Asset", True),
        ("XXXX Asset 1 — Indication XXXX — Phase XXXX — Status: XXXX", False),
        ("XXXX Asset 2 — Indication XXXX — Phase XXXX — Status: XXXX", False),
        ("XXXX Asset 3 — Indication XXXX — Phase XXXX — Status: XXXX", False),
    ]),
    # Slide 4: Financials (KEEP — populate)
    (4, "Financial Highlights", [
        ("Cash Position: $XXXX million", False),
        ("Cash Runway: XXXX months through XXXX", False),
        ("Q3 R&D Spend: $XXXX million", False),
        ("Shares Outstanding: XXXX million", False),
    ]),
    # Slide 5: This is a LOREM IPSUM placeholder slide that should be DELETED
    (5, "This slide layout — Lorem ipsum filler", [
        ("Lorem ipsum dolor sit amet, consectetur adipiscing elit.", False),
        ("This page layout is reserved for optional appendix content.", False),
        ("XXXX optional content XXXX", False),
    ]),
    # Slide 6: Management team (KEEP — populate)
    (6, "Management Team", [
        ("XXXX CEO Name — XXXX background", False),
        ("XXXX CMO Name — XXXX background", False),
        ("XXXX CFO Name — XXXX background", False),
        ("XXXX CSO Name — XXXX background", False),
    ]),
]

# Build PPTX zip
pptx_buffer = io.BytesIO()
with zipfile.ZipFile(pptx_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("[Content_Types].xml", CONTENT_TYPES)
    zf.writestr("_rels/.rels", RELS)
    zf.writestr("ppt/presentation.xml", PRESENTATION_XML)
    zf.writestr("ppt/_rels/presentation.xml.rels", PRESENTATION_RELS)
    zf.writestr("ppt/slideMasters/slideMaster1.xml", SLIDE_MASTER)
    zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", SLIDE_MASTER_RELS)
    zf.writestr("ppt/slideLayouts/slideLayout1.xml", SLIDE_LAYOUT1)
    zf.writestr("ppt/slideLayouts/slideLayout2.xml", SLIDE_LAYOUT2)
    zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", LAYOUT_RELS)
    zf.writestr("ppt/slideLayouts/_rels/slideLayout2.xml.rels", LAYOUT_RELS)
    zf.writestr("docProps/core.xml", CORE_XML)
    zf.writestr("docProps/app.xml", APP_XML)

    for slide_num, title, body in slides_data:
        slide_xml = make_slide(slide_num, title, body)
        zf.writestr(f"ppt/slides/slide{slide_num}.xml", slide_xml)
        zf.writestr(f"ppt/slides/_rels/slide{slide_num}.xml.rels", make_slide_rels(slide_num))

pptx_bytes = pptx_buffer.getvalue()
(WORKSPACE / "pipeline_update_template.pptx").write_bytes(pptx_bytes)

print("✓ Generated pipeline_update_template.pptx")
print(f"✓ Created {len(distractor_files)} distractor files across {len(dirs)} directories")
print(f"✓ Q3 content brief available at data/q3_pipeline_content.txt")
print("Workspace ready.")