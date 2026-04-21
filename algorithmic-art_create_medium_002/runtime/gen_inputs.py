import json
import os

# Create a reference specification file
spec = {
    'title': 'Recursive Bloom',
    'algorithm': 'recursive_branching',
    'required_features': [
        'recursion_depth_slider',
        'branch_angle_variation_slider',
        'sub_branches_slider',
        'primary_color_picker',
        'leaf_color_picker',
        'seed_navigation',
        'regenerate_button',
        'reset_button',
        'download_button'
    ],
    'parameter_ranges': {
        'recursion_depth': {'min': 1, 'max': 8, 'default': 5},
        'branch_angle_variation': {'min': 0, 'max': 45, 'default': 15},
        'sub_branches': {'min': 2, 'max': 5, 'default': 3}
    },
    'canvas_size': 1200,
    'seed_marker': 'RECURSIVE_BLOOM_SEED'
}

with open('task_spec.json', 'w') as f:
    json.dump(spec, f, indent=2)

print('Generated task specification')
