import sys
import os
import json
from docx import Document

def check_document(path):
    filepath = os.path.join(path, "MeetingMinutes.docx")
    if not os.path.exists(filepath):
        return False, "Output file MeetingMinutes.docx does not exist"
    
    try:
        doc = Document(filepath)
    except Exception as e:
        return False, f"Failed to open or parse the docx: {e}"

    # Check title Heading 1 with exact text
    if len(doc.paragraphs) < 2:
        return False, "Document does not have enough paragraphs"

    title_para = doc.paragraphs[0]
    title_text = title_para.text.strip()
    title_style = title_para.style.name

    if title_text != "Team Meeting - April 2024":
        return False, f"Title text mismatch: found '{title_text}'"
    if not (title_style == "Heading 1" or title_style.startswith("Heading")):
        return False, f"Title style is not Heading 1 (found '{title_style}')"

    # Check bullet list of exactly 3 items
    # docx does not directly expose numbering level easily - we check numbering by paragraph styles or numbering properties
    bullets = []
    for p in doc.paragraphs[1:]:
        text = p.text.strip()
        if text:
            bullets.append(text)

    expected_items = ["Project updates", "Budget review", "Next steps"]
    for item in expected_items:
        if item not in bullets:
            return False, f"Missing bullet item '{item}'"

    if len(bullets) != 3:
        return False, f"Bullet list should have 3 items, found {len(bullets)}"

    # Check font name and size of all runs (Arial, 12pt)
    # python-docx returns size in Pt units
    for p in doc.paragraphs:
        for run in p.runs:
            font = run.font
            if font.name and font.name.lower() != "arial":
                return False, f"Font not Arial in run: '{run.text}'"
            if font.size and font.size.pt != 12:
                return False, f"Font size not 12pt in run: '{run.text}'"

    # Check footer has page numbers centered
    # python-docx footers accessible via sections
    footers = []
    for section in doc.sections:
        footers.append(section.footer)

    # Check each footer text includes 'Page' and page number field
    page_num_found = False
    for footer in footers:
        texts = [p.text for p in footer.paragraphs]
        combined_text = "".join(texts)
        if "Page" in combined_text:
            page_num_found = True
            break

    if not page_num_found:
        return False, "Footer does not contain 'Page' text for page numbering"

    return True, "All checks passed"


if __name__ == "__main__":
    workspace = sys.argv[1]
    passed, detail = check_document(workspace)
    result = {
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "checks": [
            {"name": "existence_and_format", "passed": passed, "detail": detail}
        ]
    }
    print(json.dumps(result))
