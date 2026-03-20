import json
import os
import random

# Set deterministic seed
random.seed(12345)

# Create config file with research topic
config = {
    "topic": "artificial intelligence in climate change research",
    "min_sources": 3,
    "max_sources": 5,
    "output_format": "both",
    "include_visualizations": True,
    "marker_content": "EVAL_MARKER_2024_CLIMATE_AI_RESEARCH"
}

with open('research_config.json', 'w') as f:
    json.dump(config, f, indent=2)

# Create requirements.txt
requirements = """anthropic==0.40.0
python-docx==1.1.2
markdown==3.7
aiohttp==3.10.11
aiofiles==24.1.0
matplotlib==3.9.2
pandas==2.2.3
requests==2.32.3
jsonschema==4.23.0"""

with open('requirements.txt', 'w') as f:
    f.write(requirements)

# Create expected output structure info
expected_structure = {
    "files_to_create": [
        "research_report.md",
        "research_report.docx", 
        "research_dashboard.json",
        "research_log.txt"
    ],
    "marker_validation": "EVAL_MARKER_2024_CLIMATE_AI_RESEARCH",
    "min_report_sections": 4,
    "required_dashboard_fields": ["sources_found", "total_words", "processing_time", "citations_count"]
}

with open('expected_output.json', 'w') as f:
    json.dump(expected_structure, f, indent=2)

print("Generated input files: research_config.json, requirements.txt, expected_output.json")