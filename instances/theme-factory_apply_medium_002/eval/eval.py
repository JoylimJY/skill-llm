import sys
import os
import json
from bs4 import BeautifulSoup

def evaluate_task(workspace_dir):
    checks = []
    passed = True
    score = 0.0
    
    # Check if themed presentation exists
    themed_file = None
    for filename in ['themed_presentation.html', 'presentation_themed.html', 'presentation.html']:
        if os.path.exists(os.path.join(workspace_dir, filename)):
            themed_file = filename
            break
    
    if not themed_file:
        checks.append({
            'name': 'themed_file_exists',
            'passed': False,
            'detail': 'No themed presentation file found'
        })
        passed = False
    else:
        checks.append({
            'name': 'themed_file_exists', 
            'passed': True,
            'detail': f'Found themed file: {themed_file}'
        })
        score += 0.3
        
        # Parse HTML and check for theme application
        try:
            with open(os.path.join(workspace_dir, themed_file), 'r') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check if marker content is preserved
            markers_found = 0
            for i in range(1, 4):
                if f'MARKER_SLIDE_{i}' in content:
                    markers_found += 1
            
            if markers_found >= 2:
                checks.append({
                    'name': 'content_preserved',
                    'passed': True,
                    'detail': f'Found {markers_found}/3 slide markers'
                })
                score += 0.2
            else:
                checks.append({
                    'name': 'content_preserved',
                    'passed': False,
                    'detail': f'Only found {markers_found}/3 slide markers'
                })
                passed = False
            
            # Check for theme colors applied
            style_content = str(soup.find('style')) if soup.find('style') else ''
            tech_colors = ['#2563EB', '#64748B', '#0EA5E9', '#F8FAFC', '#1E293B']
            colors_applied = sum(1 for color in tech_colors if color.lower() in style_content.lower())
            
            if colors_applied >= 2:
                checks.append({
                    'name': 'theme_colors_applied',
                    'passed': True,
                    'detail': f'Applied {colors_applied}/5 theme colors'
                })
                score += 0.3
            else:
                checks.append({
                    'name': 'theme_colors_applied',
                    'passed': False,
                    'detail': f'Only applied {colors_applied}/5 theme colors'
                })
                passed = False
            
            # Check for font changes
            tech_fonts = ['Inter', 'Source Sans Pro']
            fonts_applied = sum(1 for font in tech_fonts if font in style_content)
            
            if fonts_applied >= 1:
                checks.append({
                    'name': 'theme_fonts_applied',
                    'passed': True,
                    'detail': f'Applied {fonts_applied}/2 theme fonts'
                })
                score += 0.2
            else:
                checks.append({
                    'name': 'theme_fonts_applied',
                    'passed': False,
                    'detail': 'No theme fonts detected'
                })
        
        except Exception as e:
            checks.append({
                'name': 'file_parsing',
                'passed': False,
                'detail': f'Error parsing themed file: {str(e)}'
            })
            passed = False
    
    return {
        'passed': passed and score >= 0.6,
        'score': min(score, 1.0),
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_directory>')
        sys.exit(1)
    
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result, indent=2))