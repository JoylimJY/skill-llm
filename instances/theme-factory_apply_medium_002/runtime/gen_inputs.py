import os
import json
import random

# Set deterministic seed
random.seed(42)

# Create themes directory
os.makedirs('themes', exist_ok=True)

# Create theme files
tech_theme = {
    'name': 'Tech Innovation',
    'description': 'Bold and modern tech aesthetic',
    'colors': {
        'primary': '#2563EB',
        'secondary': '#64748B',
        'accent': '#0EA5E9',
        'background': '#F8FAFC',
        'text': '#1E293B',
        'highlight': '#3B82F6'
    },
    'fonts': {
        'header': 'Inter',
        'body': 'Source Sans Pro'
    }
}

with open('themes/tech-innovation.json', 'w') as f:
    json.dump(tech_theme, f, indent=2)

# Create a simple HTML presentation deck
html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Q4 Financial Results</title>
    <style>
        body { margin: 20px; font-family: Arial, sans-serif; }
        .slide { page-break-after: always; margin-bottom: 40px; }
        h1 { color: #000; font-size: 24px; }
        h2 { color: #000; font-size: 20px; }
        p { color: #000; font-size: 14px; }
        .marker-content { display: none; }
    </style>
</head>
<body>
    <div class="slide">
        <h1>Q4 Financial Results</h1>
        <p>Quarterly Performance Review</p>
        <div class="marker-content">MARKER_SLIDE_1</div>
    </div>
    
    <div class="slide">
        <h2>Revenue Growth</h2>
        <p>Year-over-year growth exceeded expectations</p>
        <ul>
            <li>Revenue: $2.4M (+35%)</li>
            <li>User acquisition: 15,000 new customers</li>
            <li>Retention rate: 92%</li>
        </ul>
        <div class="marker-content">MARKER_SLIDE_2</div>
    </div>
    
    <div class="slide">
        <h2>Growth Projections</h2>
        <p>Forecasted performance for next quarter</p>
        <ul>
            <li>Projected revenue: $3.1M</li>
            <li>Target market expansion</li>
            <li>New product launches</li>
        </ul>
        <div class="marker-content">MARKER_SLIDE_3</div>
    </div>
</body>
</html>'''

with open('presentation.html', 'w') as f:
    f.write(html_content)

# Create theme showcase PDF placeholder (would normally be generated)
showcase_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Theme Showcase</title>
    <style>
        body { margin: 20px; font-family: Arial, sans-serif; }
        .theme { margin: 20px 0; padding: 20px; border: 1px solid #ccc; }
        .tech-innovation { background: #F8FAFC; color: #1E293B; }
        .tech-innovation h3 { color: #2563EB; }
    </style>
</head>
<body>
    <h1>Available Themes</h1>
    <div class="theme tech-innovation">
        <h3>Tech Innovation</h3>
        <p>Bold and modern tech aesthetic</p>
        <p>Primary: #2563EB | Accent: #0EA5E9</p>
        <p>Fonts: Inter (headers), Source Sans Pro (body)</p>
    </div>
    <!-- Other themes would be listed here -->
</body>
</html>'''

with open('theme-showcase.html', 'w') as f:
    f.write(showcase_html)

print('Input files generated successfully')