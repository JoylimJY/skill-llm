import json

# No input files needed since document is created from scratch

# Create a simple config JSON describing doc title and paragraph
config = {
    "filename": "ProjectSummary.docx",
    "title": "Project Summary",
    "paragraph": "This document summarizes the key project details and milestones.",
    "page_size": "US Letter",
    "margins_inch": 1,
    "font": "Arial",
    "font_size_pt": 12
}

with open('config.json', 'w') as f:
    json.dump(config, f)
