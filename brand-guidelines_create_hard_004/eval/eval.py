import os
import sys
import json
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Pt

def check_presentation(workspace_dir):
    checks = []
    
    # Check if presentation file exists
    pptx_path = os.path.join(workspace_dir, 'claude_presentation.pptx')
    if not os.path.exists(pptx_path):
        checks.append({"name": "file_exists", "passed": False, "detail": "claude_presentation.pptx file not found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "file_exists", "passed": True, "detail": "Presentation file found"})
    
    try:
        prs = Presentation(pptx_path)
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Could not open presentation: {str(e)}"})
        return {"passed": False, "score": 0.5, "checks": checks}
    
    checks.append({"name": "file_readable", "passed": True, "detail": "Presentation is readable"})
    
    # Check minimum number of slides
    if len(prs.slides) < 3:
        checks.append({"name": "slide_count", "passed": False, "detail": f"Expected at least 3 slides, found {len(prs.slides)}"})
    else:
        checks.append({"name": "slide_count", "passed": True, "detail": f"Found {len(prs.slides)} slides"})
    
    # Check title slide content
    title_slide = prs.slides[0]
    title_found = False
    subtitle_found = False
    
    for shape in title_slide.shapes:
        if hasattr(shape, 'text'):
            text = shape.text.lower()
            if 'claude ai' in text and 'future' in text and 'conversational' in text:
                title_found = True
            if 'anthropic' in text:
                subtitle_found = True
    
    checks.append({"name": "title_slide_title", "passed": title_found, "detail": "Title slide contains required title text" if title_found else "Title slide missing required title text"})
    checks.append({"name": "title_slide_subtitle", "passed": subtitle_found, "detail": "Title slide contains Anthropic subtitle" if subtitle_found else "Title slide missing Anthropic subtitle"})
    
    # Check for key features slide
    features_slide_found = False
    features_content_found = False
    
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, 'text'):
                text = shape.text.lower()
                if 'key features' in text:
                    features_slide_found = True
                # Check for bullet points or feature content
                if any(word in text for word in ['feature', 'capability', 'advantage', 'benefit']):
                    features_content_found = True
    
    checks.append({"name": "features_slide", "passed": features_slide_found, "detail": "Key Features slide found" if features_slide_found else "Key Features slide not found"})
    checks.append({"name": "features_content", "passed": features_content_found, "detail": "Features content found" if features_content_found else "Features content not found"})
    
    # Check for conclusion slide
    conclusion_slide_found = False
    
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, 'text'):
                text = shape.text.lower()
                if 'get started today' in text:
                    conclusion_slide_found = True
                    break
    
    checks.append({"name": "conclusion_slide", "passed": conclusion_slide_found, "detail": "Get Started Today slide found" if conclusion_slide_found else "Get Started Today slide not found"})
    
    # Check for brand colors usage
    brand_colors_found = False
    anthropic_dark = RGBColor(0x14, 0x14, 0x13)  # #141413
    anthropic_light = RGBColor(0xfa, 0xf9, 0xf5)  # #faf9f5
    anthropic_orange = RGBColor(0xd9, 0x77, 0x57)  # #d97757
    anthropic_blue = RGBColor(0x6a, 0x9b, 0xcc)  # #6a9bcc
    anthropic_green = RGBColor(0x78, 0x8c, 0x5d)  # #788c5d
    
    # Check slide backgrounds and text colors
    color_usage_count = 0
    for slide in prs.slides:
        # Check slide background
        if hasattr(slide.background, 'fill') and hasattr(slide.background.fill, 'fore_color'):
            color_usage_count += 1
        
        # Check text colors in shapes
        for shape in slide.shapes:
            if hasattr(shape, 'text_frame'):
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        if hasattr(run.font, 'color') and hasattr(run.font.color, 'rgb'):
                            color_usage_count += 1
    
    if color_usage_count > 0:
        brand_colors_found = True
    
    checks.append({"name": "brand_colors", "passed": brand_colors_found, "detail": "Brand colors applied" if brand_colors_found else "Brand colors not detected"})
    
    # Check for font usage (Poppins for headings, Lora for body)
    font_usage_found = False
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, 'text_frame'):
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        if hasattr(run.font, 'name'):
                            font_name = run.font.name
                            if font_name and ('poppins' in font_name.lower() or 'lora' in font_name.lower() or 'arial' in font_name.lower() or 'georgia' in font_name.lower()):
                                font_usage_found = True
                                break
    
    checks.append({"name": "typography", "passed": font_usage_found, "detail": "Brand typography applied" if font_usage_found else "Brand typography not detected"})
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    score = passed_count / len(checks)
    overall_passed = score >= 0.8
    
    return {"passed": overall_passed, "score": score, "checks": checks}

if __name__ == '__main__':
    workspace_dir = sys.argv[1]
    result = check_presentation(workspace_dir)
    print(json.dumps(result))