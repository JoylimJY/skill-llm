import sys
import os
from pptx import Presentation
from pptx.dml.color import RGBColor
import json

def check_branded_presentation(workspace_dir):
    checks = []
    
    # Check if output file exists
    output_file = os.path.join(workspace_dir, 'branded_presentation.pptx')
    if not os.path.exists(output_file):
        checks.append({"name": "output_file_exists", "passed": False, "detail": "branded_presentation.pptx not found"})
        return checks
    
    checks.append({"name": "output_file_exists", "passed": True, "detail": "branded_presentation.pptx created successfully"})
    
    try:
        prs = Presentation(output_file)
        
        # Anthropic brand colors
        dark_color = RGBColor(20, 20, 19)  # #141413
        light_color = RGBColor(250, 249, 245)  # #faf9f5
        orange_color = RGBColor(217, 119, 87)  # #d97757
        blue_color = RGBColor(106, 155, 204)  # #6a9bcc
        green_color = RGBColor(120, 140, 93)  # #788c5d
        
        accent_colors = [orange_color, blue_color, green_color]
        
        # Check slides count
        if len(prs.slides) >= 3:
            checks.append({"name": "slides_preserved", "passed": True, "detail": f"All {len(prs.slides)} slides preserved"})
        else:
            checks.append({"name": "slides_preserved", "passed": False, "detail": f"Only {len(prs.slides)} slides found, expected at least 3"})
        
        # Check for title font styling (Poppins or Arial fallback)
        title_font_applied = False
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text_frame') and shape.text_frame.text.strip():
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            if run.font.size and run.font.size >= 240000:  # 24pt in EMU
                                font_name = run.font.name
                                if font_name and (font_name.lower() in ['poppins', 'arial']):
                                    title_font_applied = True
                                    break
        
        checks.append({"name": "title_font_applied", "passed": title_font_applied, "detail": "Poppins or Arial font applied to titles" if title_font_applied else "Title font not properly applied"})
        
        # Check for body text font (Lora or Georgia fallback)
        body_font_applied = False
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text_frame') and shape.text_frame.text.strip():
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            if not run.font.size or run.font.size < 240000:  # Less than 24pt
                                font_name = run.font.name
                                if font_name and (font_name.lower() in ['lora', 'georgia']):
                                    body_font_applied = True
                                    break
        
        checks.append({"name": "body_font_applied", "passed": body_font_applied, "detail": "Lora or Georgia font applied to body text" if body_font_applied else "Body font not properly applied"})
        
        # Check for brand color usage in text
        brand_colors_used = False
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text_frame'):
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            if hasattr(run.font, 'color') and hasattr(run.font.color, 'rgb'):
                                color = run.font.color.rgb
                                if color in [dark_color, light_color]:
                                    brand_colors_used = True
                                    break
        
        checks.append({"name": "brand_text_colors", "passed": brand_colors_used, "detail": "Anthropic brand colors applied to text" if brand_colors_used else "Brand colors not applied to text"})
        
        # Check for accent colors in shapes
        accent_colors_used = False
        shape_count = 0
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'fill') and not hasattr(shape, 'text_frame'):
                    shape_count += 1
                    if hasattr(shape.fill, 'fore_color') and hasattr(shape.fill.fore_color, 'rgb'):
                        shape_color = shape.fill.fore_color.rgb
                        for accent_color in accent_colors:
                            if (abs(shape_color.red - accent_color.red) <= 5 and 
                                abs(shape_color.green - accent_color.green) <= 5 and 
                                abs(shape_color.blue - accent_color.blue) <= 5):
                                accent_colors_used = True
                                break
        
        if shape_count > 0:
            checks.append({"name": "accent_colors_shapes", "passed": accent_colors_used, "detail": "Accent colors applied to shapes" if accent_colors_used else "Accent colors not applied to shapes"})
        else:
            checks.append({"name": "accent_colors_shapes", "passed": True, "detail": "No shapes found to style"})
        
        # Check content preservation
        content_preserved = True
        expected_texts = ['sample company presentation', 'marketing strategy', 'key performance metrics', 'future roadmap']
        found_texts = []
        
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text_frame') and shape.text_frame.text.strip():
                    found_texts.append(shape.text_frame.text.lower())
        
        all_text = ' '.join(found_texts)
        for expected in expected_texts:
            if expected not in all_text:
                content_preserved = False
                break
        
        checks.append({"name": "content_preserved", "passed": content_preserved, "detail": "Original content preserved" if content_preserved else "Some original content missing"})
        
    except Exception as e:
        checks.append({"name": "file_processing", "passed": False, "detail": f"Error processing presentation: {str(e)}"})
    
    return checks

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        return
    
    workspace_dir = sys.argv[1]
    checks = check_branded_presentation(workspace_dir)
    
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()