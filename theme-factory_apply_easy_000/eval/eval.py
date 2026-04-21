import sys
import os
import re
import json
from PyPDF2 import PdfReader

def check_showcase_pdf(path):
    pdf_path = os.path.join(path, "theme-showcase.pdf")
    if not os.path.isfile(pdf_path):
        return False, "theme-showcase.pdf not found"
    try:
        reader = PdfReader(pdf_path)
        full_text = "".join(page.extract_text() or "" for page in reader.pages).lower()
        keywords = [
            "ocean depths", "sunset boulevard", "forest canopy", "modern minimalist",
            "golden hour", "arctic frost", "desert rose", "tech innovation",
            "botanical garden", "midnight galaxy"
        ]
        if not all(any(k in full_text for k in keywords) for k in keywords):
            return False, "Not all theme names found in theme-showcase.pdf text"
        return True, ""
    except Exception as e:
        return False, f"Error reading PDF: {e}"

def check_styled_deck(path):
    styled_path = os.path.join(path, "deck_styled.md")
    if not os.path.isfile(styled_path):
        return False, "deck_styled.md output file not found"
    try:
        with open(styled_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        # Check that original content structure remains (look for slide titles)
        if not ("# sample slide deck" in content and "## agenda" in content):
            return False, "Styled deck.md missing expected slide headings"
        # Check for Ocean Depths theme colors and fonts applied
        # Ocean Depths color palette (example hexes): #004466, #0077a3, #66c2ff
        # Fonts for Ocean Depths: Headers: 'Montserrat', Body: 'Open Sans'

        colors = ["#004466", "#0077a3", "#66c2ff"]
        fonts = ["montserrat", "open sans"]

        color_found = any(c in content for c in colors)
        font_found = any(f in content for f in fonts)

        if not color_found:
            return False, "Ocean Depths theme colors not found in deck_styled.md"
        if not font_found:
            return False, "Ocean Depths theme fonts not found in deck_styled.md"

        return True, ""
    except Exception as e:
        return False, f"Error reading deck_styled.md: {e}"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg_check", "passed": False, "detail": "Missing workspace path argument."}]}))
        return

    workspace = sys.argv[1]
    checks = []

    # Check theme-showcase.pdf present and correct
    passed, detail = check_showcase_pdf(workspace)
    checks.append({"name": "theme_showcase_pdf", "passed": passed, "detail": detail})

    # Check styled deck output correctness
    passed_deck, detail_deck = check_styled_deck(workspace)
    checks.append({"name": "deck_styled_applied", "passed": passed_deck, "detail": detail_deck})

    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed_all = score == 1.0

    result = {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
