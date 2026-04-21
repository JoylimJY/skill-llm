import os
import json

# Create a simple reference file about liminal spaces
reference_content = {
    "concept": "liminal_spaces",
    "characteristics": [
        "transitional",
        "threshold",
        "uncanny",
        "empty",
        "familiar yet strange"
    ],
    "examples": [
        "empty hallways",
        "vacant shopping malls",
        "hotel corridors",
        "stairwells",
        "waiting rooms"
    ]
}

with open('reference.json', 'w') as f:
    json.dump(reference_content, f, indent=2)

# Create a simple instruction file
with open('instructions.txt', 'w') as f:
    f.write('Create artistic interpretation of liminal spaces theme\n')
    f.write('Focus on transitional, threshold environments\n')
    f.write('Capture the uncanny, familiar-yet-strange quality\n')

print('Input files generated successfully')