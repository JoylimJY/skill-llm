import os
import json

# Create canvas-fonts directory with some basic fonts info
os.makedirs('canvas-fonts', exist_ok=True)

# Create font metadata file
font_data = {
    'available_fonts': [
        {'name': 'DejaVu Sans', 'style': 'modern', 'weight': 'light'},
        {'name': 'Liberation Sans', 'style': 'clean', 'weight': 'thin'},
        {'name': 'Noto Sans', 'style': 'minimal', 'weight': 'regular'}
    ],
    'marker': 'FONT_SYSTEM_READY_RESONANCE_2024'
}

with open('canvas-fonts/fonts.json', 'w') as f:
    json.dump(font_data, f)

# Create a marker file for verification
with open('task_marker.txt', 'w') as f:
    f.write('CANVAS_DESIGN_TASK_ELECTRONIC_MUSIC_COLLECTIVE_RESONANCE_DRIFT_2024')

print('Input files generated successfully')