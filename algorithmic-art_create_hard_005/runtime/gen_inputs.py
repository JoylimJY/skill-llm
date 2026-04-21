#!/usr/bin/env python3
import json
import os

# Create a reference specification file
spec = {
    "title": "Recursive Echoes",
    "concept": "Self-similar patterns from iterative rules",
    "required_parameters": ["recursion_depth", "branching_angle", "line_thickness"],
    "required_features": ["seed_navigation", "parameter_controls", "download_button"],
    "branding": "Anthropic light theme with Poppins/Lora fonts",
    "output_format": "single HTML file"
}

with open('task_spec.json', 'w') as f:
    json.dump(spec, f, indent=2)

print("Task specification created.")
