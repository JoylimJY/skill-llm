import os
import json

# Create theme-showcase.pdf placeholder
with open('theme-showcase.pdf', 'w') as f:
    f.write('THEME_SHOWCASE_PDF_PLACEHOLDER')

# Create themes directory and Tech Innovation theme
os.makedirs('themes', exist_ok=True)

tech_theme = {
    'name': 'Tech Innovation',
    'description': 'Bold and modern tech aesthetic',
    'colors': {
        'primary': '#0066CC',
        'secondary': '#FF6600',
        'accent': '#00CC66',
        'background': '#F8F9FA',
        'text': '#333333',
        'muted': '#6C757D'
    },
    'fonts': {
        'header': 'Roboto',
        'body': 'Open Sans'
    }
}

with open('themes/tech_innovation.json', 'w') as f:
    json.dump(tech_theme, f, indent=2)

# Create other theme files as placeholders
other_themes = [
    'ocean_depths', 'sunset_boulevard', 'forest_canopy', 'modern_minimalist',
    'golden_hour', 'arctic_frost', 'desert_rose', 'botanical_garden', 'midnight_galaxy'
]

for theme in other_themes:
    with open(f'themes/{theme}.json', 'w') as f:
        json.dump({'name': theme, 'placeholder': True}, f)

print('Input files generated successfully')