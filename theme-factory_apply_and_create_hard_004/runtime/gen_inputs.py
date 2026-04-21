#!/usr/bin/env python3
import json
import os

os.makedirs('themes', exist_ok=True)

# Create theme showcase content
theme_showcase_content = """# Theme Showcase

## Available Themes

1. Ocean Depths - Professional and calming maritime theme
   Colors: #1A5F7A (primary), #2E8B9E (secondary), #87CEEB (accent)
   Fonts: Georgia (headers), Verdana (body)

2. Sunset Boulevard - Warm and vibrant sunset colors
   Colors: #FF6B35 (primary), #F7931E (secondary), #FDB833 (accent)
   Fonts: Montserrat (headers), Open Sans (body)

3. Forest Canopy - Natural and grounded earth tones
   Colors: #2D5016 (primary), #6B8E23 (secondary), #9ACD32 (accent)
   Fonts: Garamond (headers), Tahoma (body)

4. Modern Minimalist - Clean and contemporary grayscale
   Colors: #333333 (primary), #666666 (secondary), #CCCCCC (accent)
   Fonts: Helvetica (headers), Arial (body)

5. Golden Hour - Rich and warm autumnal palette
   Colors: #D4A574 (primary), #C19A6B (secondary), #FFD700 (accent)
   Fonts: Georgia (headers), Garamond (body)

6. Arctic Frost - Cool and crisp winter-inspired theme
   Colors: #B0E0E6 (primary), #ADD8E6 (secondary), #F0F8FF (accent)
   Fonts: Trebuchet MS (headers), Verdana (body)

7. Desert Rose - Soft and sophisticated dusty tones
   Colors: #A0826D (primary), #C9ADA7 (secondary), #E8D5C4 (accent)
   Fonts: Palatino (headers), Georgia (body)

8. Tech Innovation - Bold and modern tech aesthetic
   Colors: #00D9FF (primary), #0099CC (secondary), #FF006E (accent)
   Fonts: Roboto (headers), Source Sans Pro (body)

9. Botanical Garden - Fresh and organic garden colors
   Colors: #52B788 (primary), #74C69D (secondary), #B7E4C7 (accent)
   Fonts: Trebuchet MS (headers), Verdana (body)

10. Midnight Galaxy - Dramatic and cosmic deep tones
    Colors: #0B1929 (primary), #1B263B (secondary), #415A77 (accent)
    Fonts: Courier New (headers), Consolas (body)
"""

with open('theme-showcase.pdf', 'w') as f:
    f.write(theme_showcase_content)

# Create Ocean Depths theme
ocean_depths = {
    "name": "Ocean Depths",
    "description": "Professional and calming maritime theme",
    "colors": {
        "primary": "#1A5F7A",
        "secondary": "#2E8B9E",
        "accent": "#87CEEB",
        "text": "#1A5F7A",
        "background": "#F0F8FF"
    },
    "fonts": {
        "headers": "Georgia",
        "body": "Verdana"
    }
}

with open('themes/ocean_depths.json', 'w') as f:
    json.dump(ocean_depths, f, indent=2)

# Create sample presentation
presentation_content = """# Company Quarterly Report

## Q1 Performance

This presentation covers our quarterly performance metrics and strategic initiatives.

### Revenue Growth

We achieved 15% year-over-year growth in Q1.

### Market Expansion

New markets in Asia-Pacific region showing strong potential.

### Team Highlights

- Successfully launched 3 new products
- Expanded engineering team by 25%
- Improved customer satisfaction scores

## Q2 Outlook

Expected continued growth with focus on product innovation.
"""

with open('presentation.md', 'w') as f:
    f.write(presentation_content)

print("Input files generated successfully")
