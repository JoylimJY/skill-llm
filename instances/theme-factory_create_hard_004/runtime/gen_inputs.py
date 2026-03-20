import os
import json
from pathlib import Path

# Create themes directory and sample themes
themes_dir = Path('themes')
themes_dir.mkdir(exist_ok=True)

# Create sample theme files
themes = {
    'ocean_depths': {
        'name': 'Ocean Depths',
        'colors': {'primary': '#1e3a8a', 'secondary': '#0ea5e9', 'accent': '#67e8f9', 'neutral': '#64748b', 'background': '#f8fafc'},
        'fonts': {'header': 'Montserrat', 'body': 'Source Sans Pro'}
    },
    'tech_innovation': {
        'name': 'Tech Innovation',
        'colors': {'primary': '#7c3aed', 'secondary': '#06b6d4', 'accent': '#10b981', 'neutral': '#6b7280', 'background': '#f9fafb'},
        'fonts': {'header': 'Inter', 'body': 'Roboto'}
    },
    'modern_minimalist': {
        'name': 'Modern Minimalist',
        'colors': {'primary': '#374151', 'secondary': '#6b7280', 'accent': '#f59e0b', 'neutral': '#9ca3af', 'background': '#ffffff'},
        'fonts': {'header': 'Helvetica Neue', 'body': 'Arial'}
    }
}

for theme_key, theme_data in themes.items():
    theme_file = themes_dir / f'{theme_key}.json'
    with open(theme_file, 'w') as f:
        json.dump(theme_data, f, indent=2)

# Create a minimal theme showcase PDF content (we'll create this as a text file for simplicity)
with open('theme-showcase.pdf', 'w') as f:
    f.write('THEME_SHOWCASE_MARKER_CONTENT\n')
    f.write('Available Themes:\n')
    for theme_data in themes.values():
        f.write(f"- {theme_data['name']}\n")

# Create marker file for validation
with open('marker_content.txt', 'w') as f:
    f.write('TECHFLOW_BRAND_GUIDE_MARKER_12345')

print('Generated input files for theme factory task')