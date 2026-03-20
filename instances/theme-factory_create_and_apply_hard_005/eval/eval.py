import sys
import os
import json
from pptx import Presentation
from pptx.dml.color import RGBColor

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}".upper()

def check_presentation_theming(workspace_dir):
    checks = []
    
    # Check if presentation file exists
    pptx_path = os.path.join(workspace_dir, 'board_presentation.pptx')
    if not os.path.exists(pptx_path):
        checks.append({"name": "presentation_exists", "passed": False, "detail": "board_presentation.pptx not found"})
        return checks, False
    
    checks.append({"name": "presentation_exists", "passed": True, "detail": "Presentation file found"})
    
    try:
        prs = Presentation(pptx_path)
        
        # Check if presentation has expected number of slides
        slide_count = len(prs.slides)
        expected_slides = 5
        slide_count_ok = slide_count == expected_slides
        checks.append({"name": "slide_count", "passed": slide_count_ok, "detail": f"Expected {expected_slides} slides, found {slide_count}"})
        
        # Check for marker content preservation
        marker_found = False
        markers = ["MARKER_TITLE_SLIDE", "MARKER_CONTENT_BULLET", "MARKER_FINANCIAL_DATA", "MARKER_STRATEGY_PHASE", "MARKER_RISK_CONTENT"]
        found_markers = []
        
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text'):
                    text_content = shape.text
                    for marker in markers:
                        if marker in text_content:
                            found_markers.append(marker)
        
        marker_preservation = len(found_markers) >= 3  # At least 3 markers should be preserved
        checks.append({"name": "content_preservation", "passed": marker_preservation, "detail": f"Found {len(found_markers)} content markers preserved"})
        
        # Check for theme application - look for color changes from default
        themed_colors_found = 0
        default_black_rgb = (0, 0, 0)
        
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text_frame') and shape.text_frame is not None:
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            if run.font.color and run.font.color.rgb:
                                color_rgb = (run.font.color.rgb.red, run.font.color.rgb.green, run.font.color.rgb.blue)
                                if color_rgb != default_black_rgb:
                                    themed_colors_found += 1
        
        # Check background colors or fill colors
        background_themed = False
        for slide in prs.slides:
            if hasattr(slide.background, 'fill') and slide.background.fill:
                background_themed = True
                break
        
        # Check for font changes from default
        font_changes = 0
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text_frame') and shape.text_frame is not None:
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            if run.font.name and 'Calibri' in str(run.font.name):
                                font_changes += 1
        
        # Theme application check
        theme_applied = (themed_colors_found > 0) or background_themed or (font_changes > 3)
        checks.append({"name": "theme_applied", "passed": theme_applied, "detail": f"Theme elements detected: {themed_colors_found} color changes, fonts updated: {font_changes > 3}, background themed: {background_themed}"})
        
        # Check for professional formatting (titles should be formatted)
        title_formatting = 0
        for slide in prs.slides:
            if slide.shapes.title:
                title_shape = slide.shapes.title
                if hasattr(title_shape, 'text_frame') and title_shape.text_frame:
                    for paragraph in title_shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            if run.font.bold or (run.font.size and run.font.size.pt > 20):
                                title_formatting += 1
        
        formatting_check = title_formatting >= 3
        checks.append({"name": "professional_formatting", "passed": formatting_check, "detail": f"Found {title_formatting} properly formatted titles"})
        
        # Check if original business content is intact
        business_terms = ['Sustainable Energy', 'Board Review', 'Market Opportunity', 'Financial Projections', 'Strategic Implementation', 'Risk Assessment']
        content_intact = 0
        
        for slide in prs.slides:
            slide_text = ""
            for shape in slide.shapes:
                if hasattr(shape, 'text'):
                    slide_text += shape.text + " "
            
            for term in business_terms:
                if term in slide_text:
                    content_intact += 1
        
        content_preservation_check = content_intact >= 4
        checks.append({"name": "business_content_intact", "passed": content_preservation_check, "detail": f"Found {content_intact} key business terms preserved"})
        
        # Overall success - all major checks pass
        all_passed = all([
            slide_count_ok,
            marker_preservation,
            theme_applied,
            content_preservation_check
        ])
        
        return checks, all_passed
        
    except Exception as e:
        checks.append({"name": "presentation_processing", "passed": False, "detail": f"Error processing presentation: {str(e)}"})
        return checks, False

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Need workspace directory argument"}]}))
        return
    
    workspace_dir = sys.argv[1]
    checks, success = check_presentation_theming(workspace_dir)
    
    passed_count = sum(1 for check in checks if check["passed"])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    
    result = {
        "passed": success,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()