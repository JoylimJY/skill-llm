#!/usr/bin/env python3
import json
import os

# Create a reference specification file
spec = {
    "title": "Digital Erosion",
    "concept": "Computational processes gradually wearing away structured forms",
    "required_features": [
        "seeded randomness",
        "parameter controls",
        "seed navigation",
        "regenerate button",
        "reset button",
        "erosion intensity parameter",
        "particle count parameter",
        "color palette controls"
    ],
    "output_format": "single HTML file",
    "filename": "erosion-art.html"
}

with open('task_spec.json', 'w') as f:
    json.dump(spec, f, indent=2)

print("Task specification created")
