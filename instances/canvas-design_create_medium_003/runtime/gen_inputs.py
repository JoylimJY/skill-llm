import os
import json

# Create marker file to verify task completion
marker_data = {
    'venue_name': 'Resonance Chamber',
    'theme': 'experimental music',
    'style_keywords': ['sound waves', 'frequency', 'underground', 'gallery quality'],
    'expected_sophistication': 'museum quality',
    'multi_page_requested': True
}

with open('task_markers.json', 'w') as f:
    json.dump(marker_data, f, indent=2)

# Create canvas-fonts directory with some mock font references
os.makedirs('canvas-fonts', exist_ok=True)
with open('canvas-fonts/available_fonts.txt', 'w') as f:
    f.write('Helvetica\nFutura\nGaramond\nArial\nTimes\n')

print('Input files generated successfully')