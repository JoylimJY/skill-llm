#!/usr/bin/env python3

# This script creates no input files since the task is to create a document from scratch
# However, we need a deterministic marker that the eval can check for

import json

# Create a metadata file with expected content markers
expected_markers = {
    "title": "Smart City Initiative Proposal",
    "subtitle": "Transforming Urban Infrastructure Through Technology",
    "sections": [
        "Executive Summary",
        "Project Overview", 
        "Technical Implementation",
        "Budget Analysis"
    ],
    "conclusion": "Conclusion",
    "budget_table": True,
    "toc": True
}

with open('expected_content.json', 'w') as f:
    json.dump(expected_markers, f, indent=2)

print("Generated expected content markers for eval")