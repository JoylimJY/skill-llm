import os
from pptxgen import PptxGenJS
import random

# Set deterministic seed
random.seed(42)

# Create a template presentation with varied layouts
pres = PptxGenJS()
pres.layout = 'LAYOUT_16x9'
pres.author = 'Template Author'
pres.title = 'Quarterly Template'

# Slide 1: Title slide with dark background
slide1 = pres.addSlide()
slide1.background = {'color': '1E2761'}
slide1.addText('QUARTERLY TEMPLATE TITLE', {
    'x': 0.5, 'y': 1.5, 'w': 9, 'h': 1.2,
    'fontSize': 44, 'bold': True, 'color': 'FFFFFF',
    'align': 'center'
})
slide1.addText('TEMPLATE_SUBTITLE_PLACEHOLDER', {
    'x': 0.5, 'y': 3, 'w': 9, 'h': 0.8,
    'fontSize': 24, 'color': 'CADCFC',
    'align': 'center'
})

# Slide 2: Executive summary with icon bullets
slide2 = pres.addSlide()
slide2.addText('Executive Summary', {
    'x': 0.5, 'y': 0.3, 'w': 9, 'h': 0.8,
    'fontSize': 36, 'bold': True, 'color': '1E2761'
})
# Add circular backgrounds for icons
for i in range(3):
    slide2.addShape('oval', {
        'x': 0.8, 'y': 1.5 + i * 1.2, 'w': 0.4, 'h': 0.4,
        'fill': {'color': 'CADCFC'}
    })
    slide2.addText(f'EXECUTIVE_POINT_{i+1}_PLACEHOLDER', {
        'x': 1.5, 'y': 1.5 + i * 1.2, 'w': 7.5, 'h': 1,
        'fontSize': 18, 'bold': True, 'color': '2C5F2D'
    })
    slide2.addText(f'Executive detail text placeholder for point {i+1}', {
        'x': 1.5, 'y': 1.8 + i * 1.2, 'w': 7.5, 'h': 0.6,
        'fontSize': 14, 'color': '36454F'
    })

# Slide 3: Two-column layout with chart area
slide3 = pres.addSlide()
slide3.addText('Revenue Analysis', {
    'x': 0.5, 'y': 0.3, 'w': 9, 'h': 0.8,
    'fontSize': 36, 'bold': True, 'color': '1E2761'
})
# Chart placeholder area
slide3.addShape('rectangle', {
    'x': 0.5, 'y': 1.2, 'w': 5.5, 'h': 3.5,
    'fill': {'color': 'F2F2F2'},
    'line': {'color': 'CADCFC', 'width': 2}
})
slide3.addText('CHART_PLACEHOLDER', {
    'x': 0.5, 'y': 2.8, 'w': 5.5, 'h': 0.5,
    'fontSize': 20, 'align': 'center', 'color': '84B59F'
})
# Text content area
slide3.addText('Key Insights', {
    'x': 6.2, 'y': 1.2, 'w': 3.3, 'h': 0.5,
    'fontSize': 24, 'bold': True, 'color': '2C5F2D'
})
for i in range(3):
    slide3.addText(f'REVENUE_INSIGHT_{i+1}_PLACEHOLDER', {
        'x': 6.2, 'y': 2 + i * 0.8, 'w': 3.3, 'h': 0.6,
        'fontSize': 14, 'color': '36454F'
    })

# Slide 4: Challenges grid layout
slide4 = pres.addSlide()
slide4.addText('Challenges & Obstacles', {
    'x': 0.5, 'y': 0.3, 'w': 9, 'h': 0.8,
    'fontSize': 36, 'bold': True, 'color': '1E2761'
})
# 2x2 grid of challenge cards
for i in range(4):
    row = i // 2
    col = i % 2
    x = 0.5 + col * 4.7
    y = 1.4 + row * 1.8
    
    slide4.addShape('rectangle', {
        'x': x, 'y': y, 'w': 4.2, 'h': 1.5,
        'fill': {'color': 'FFFFFF'},
        'line': {'color': 'F96167', 'width': 3}
    })
    slide4.addText(f'CHALLENGE_{i+1}_TITLE_PLACEHOLDER', {
        'x': x + 0.2, 'y': y + 0.1, 'w': 3.8, 'h': 0.5,
        'fontSize': 18, 'bold': True, 'color': 'B85042'
    })
    slide4.addText(f'Challenge {i+1} description placeholder text goes here', {
        'x': x + 0.2, 'y': y + 0.6, 'w': 3.8, 'h': 0.8,
        'fontSize': 14, 'color': '36454F'
    })

# Slide 5: Closing slide with action items
slide5 = pres.addSlide()
slide5.background = {'color': '2C5F2D'}
slide5.addText('NEXT_STEPS_TITLE_PLACEHOLDER', {
    'x': 0.5, 'y': 1, 'w': 9, 'h': 1,
    'fontSize': 40, 'bold': True, 'color': 'FFFFFF',
    'align': 'center'
})
# Action items with numbering
for i in range(3):
    slide5.addShape('oval', {
        'x': 1, 'y': 2.5 + i * 0.8, 'w': 0.5, 'h': 0.5,
        'fill': {'color': 'F9E795'}
    })
    slide5.addText(str(i+1), {
        'x': 1, 'y': 2.5 + i * 0.8, 'w': 0.5, 'h': 0.5,
        'fontSize': 20, 'bold': True, 'color': '2C5F2D',
        'align': 'center', 'valign': 'middle'
    })
    slide5.addText(f'ACTION_ITEM_{i+1}_PLACEHOLDER', {
        'x': 1.8, 'y': 2.5 + i * 0.8, 'w': 7.2, 'h': 0.6,
        'fontSize': 18, 'color': 'F5F5F5'
    })

# Write the template file
pres.writeFile({'fileName': 'quarterly_template.pptx'})
print('Generated quarterly_template.pptx with 5 varied layout slides')