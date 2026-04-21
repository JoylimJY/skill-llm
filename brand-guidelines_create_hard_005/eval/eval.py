import sys
import os
from pptx import Presentation
from pptx.dml.color import RGBColor
import json

def eval_presentation(workspace_path):
    checks = []
    
    # Find the presentation file
    pptx_files = [f for f in os.listdir(workspace_path) if f.endswith('.pptx')]
    if not pptx_files:
        checks.append({"name": "file_exists", "passed": False, "detail": "No PowerPoint file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Check for correct filename
    target_file = None
    for f in pptx_files:
        if 'anthropic' in f.lower() and 'presentation' in f.lower():
            target_file = f
            break
    
    if not target_file:
        target_file = pptx_files[0]
        checks.append({"name": "correct_filename", "passed": False, "detail": "File not named anthropic_presentation.pptx"})
    else:
        checks.append({"name": "correct_filename", "passed": True, "detail": "Correct filename found"})
    
    try:
        prs = Presentation(os.path.join(workspace_path, target_file))
        checks.append({"name": "file_readable", "passed": True, "detail": "PowerPoint file loads successfully"})
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Cannot read PowerPoint file: {str(e)}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Check minimum number of slides
    if len(prs.slides) >= 5:
        checks.append({"name": "slide_count", "passed": True, "detail": f"Found {len(prs.slides)} slides (minimum 5 required)"})
    else:
        checks.append({"name": "slide_count", "passed": False, "detail": f"Only {len(prs.slides)} slides found, need at least 5"})
    
    # Check for title slide content
    title_found = False
    subtitle_found = False
    if len(prs.slides) > 0:
        first_slide = prs.slides[0]
        slide_text = ""
        for shape in first_slide.shapes:
            if hasattr(shape, 'text'):
                slide_text += shape.text.lower() + " "
        
        if 'anthropic' in slide_text and 'brand' in slide_text and 'showcase' in slide_text:
            title_found = True
        if 'official' in slide_text and 'guidelines' in slide_text and 'demo' in slide_text:
            subtitle_found = True
    
    checks.append({"name": "title_content", "passed": title_found, "detail": "Title slide contains required heading" if title_found else "Title slide missing required content"})
    checks.append({"name": "subtitle_content", "passed": subtitle_found, "detail": "Title slide contains required subtitle" if subtitle_found else "Title slide missing required subtitle"})
    
    # Check for brand colors usage
    brand_colors_found = False
    anthropic_colors = ['141413', 'faf9f5', 'd97757', '6a9bcc', '788c5d', 'b0aea5', 'e8e6dc']
    
    for slide in prs.slides:
        for shape in first_slide.shapes:
            if hasattr(shape, 'text'):
                text_content = shape.text.lower()
                if any(color.lower() in text_content for color in anthropic_colors):
                    brand_colors_found = True
                    break
    
    checks.append({"name": "brand_colors_displayed", "passed": brand_colors_found, "detail": "Brand colors found in presentation" if brand_colors_found else "Brand colors not clearly displayed"})
    
    # Check for typography content
    typography_content = False
    font_references = False
    
    for slide in prs.slides:
        slide_text = ""
        for shape in slide.shapes:
            if hasattr(shape, 'text'):
                slide_text += shape.text.lower() + " "
        
        if 'typography' in slide_text or 'font' in slide_text:
            typography_content = True
        if 'poppins' in slide_text and 'lora' in slide_text:
            font_references = True
    
    checks.append({"name": "typography_slide", "passed": typography_content, "detail": "Typography demonstration found" if typography_content else "No typography demonstration found"})
    checks.append({"name": "font_references", "passed": font_references, "detail": "Poppins and Lora fonts referenced" if font_references else "Required fonts not referenced"})
    
    # Check for shapes/visual elements
    shapes_found = False
    shape_count = 0
    
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, 'shape_type') and shape.shape_type != 1:  # Not text box
                shape_count += 1
    
    if shape_count >= 3:
        shapes_found = True
    
    checks.append({"name": "visual_shapes", "passed": shapes_found, "detail": f"Found {shape_count} visual shapes" if shapes_found else f"Only {shape_count} visual shapes found, need more variety"})
    
    # Check for mixed content slide
    mixed_content = False
    complex_slides = 0
    
    for slide in prs.slides:
        text_shapes = 0
        other_shapes = 0
        
        for shape in slide.shapes:
            if hasattr(shape, 'text') and shape.text.strip():
                text_shapes += 1
            elif hasattr(shape, 'shape_type') and shape.shape_type != 1:
                other_shapes += 1
        
        if text_shapes >= 2 and other_shapes >= 1:
            complex_slides += 1
    
    if complex_slides >= 1:
        mixed_content = True
    
    checks.append({"name": "mixed_content", "passed": mixed_content, "detail": "Mixed content slide found" if mixed_content else "No slide with mixed text and visual elements found"})
    
    # Calculate final score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    return {
        "passed": score >= 0.7,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1]
    result = eval_presentation(workspace)
    print(json.dumps(result))