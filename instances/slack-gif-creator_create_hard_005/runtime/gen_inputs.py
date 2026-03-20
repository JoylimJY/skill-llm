import os
import json

# Create a deterministic marker file for validation
marker_data = {
    'task_type': 'bouncing_spinning_star_gif',
    'requirements': {
        'emoji_size': True,
        'dimensions': '128x128',
        'phases': ['fall', 'bounce', 'spin_pulse'],
        'colors': 'cycling_vibrant',
        'duration_max': 2.5,
        'optimization': 'slack_emoji'
    },
    'validation_seed': 12345
}

with open('task_requirements.json', 'w') as f:
    json.dump(marker_data, f, indent=2)

print('Generated task requirements marker file')