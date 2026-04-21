import os
import json

# Create a simple reference file about digital archaeology concepts
with open('reference_notes.txt', 'w') as f:
    f.write("Digital Archaeology Research Notes\n")
    f.write("========================================\n\n")
    f.write("Key concepts:\n")
    f.write("- Obsolete file formats (.fla, .psd, .ai)\n")
    f.write("- Data layer stratification\n")
    f.write("- Digital artifact preservation\n")
    f.write("- Computational archaeology methods\n")
    f.write("- Binary data excavation techniques\n")
    f.write("\nResearch methodology should emphasize systematic documentation\n")
    f.write("and visual representation of data structures.\n")

# Create a sample metadata file to inspire systematic representation
metadata = {
    "project": "digital_archaeology_study",
    "data_types": ["binary", "metadata", "filesystem"],
    "preservation_methods": ["documentation", "visualization", "mapping"],
    "research_focus": "systematic observation of digital remnants"
}

with open('project_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print("Input files generated successfully")