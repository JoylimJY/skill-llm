import sys
import os
import json
from pptx import Presentation

def get_all_text_from_shape(shape):
    """递归提取形状中的所有文本，支持组合形状和表格"""
    texts = []
    
    # 1. 处理普通文本框或占位符
    if shape.has_text_frame:
        texts.append(shape.text_frame.text)
        
    # 2. 处理表格
    if shape.has_table:
        for row in shape.table.rows:
            for cell in row.cells:
                texts.append(cell.text_frame.text)
                
    # 3. 处理组合形状 (递归)
    if shape.shape_type == 6: # MSO_SHAPE_TYPE.GROUP
        for s in shape.shapes:
            texts.extend(get_all_text_from_shape(s))
            
    return texts

def check_presentation_styling(workspace_dir):
    output_file = os.path.join(workspace_dir, 'styled_presentation.pptx')
    if not os.path.exists(output_file):
        return {"passed": False, "score": 0.0, "checks": [{"name": "exists", "passed": False, "detail": "File not found"}]}

    checks = []
    try:
        prs = Presentation(output_file)
        checks.append({"name": "output_file_exists", "passed": True, "detail": "styled_presentation.pptx found"})
        checks.append({"name": "presentation_readable", "passed": True, "detail": "Readable"})
        
        # 幻灯片数量检查
        slide_count = len(prs.slides)
        checks.append({"name": "slides_preserved", "passed": slide_count >= 2, "detail": f"Slides: {slide_count}"})

        # 品牌颜色检测 (支持多层级检查)
        brand_colors_found = False
        anthropic_colors = {(20, 20, 19), (250, 249, 245), (217, 119, 87), (106, 155, 204), (120, 140, 93)}

        def check_color(color_obj):
            try:
                rgb = color_obj.rgb
                return (rgb[0], rgb[1], rgb[2]) in anthropic_colors
            except: return False

        for slide in prs.slides:
            for shape in slide.shapes:
                # 检查颜色应用
                if hasattr(shape, 'fill') and shape.fill.type == 1:
                    if check_color(shape.fill.fore_color): brand_colors_found = True
                
                if shape.has_text_frame:
                    for p in shape.text_frame.paragraphs:
                        for r in p.runs:
                            if check_color(r.font.color): brand_colors_found = True

        checks.append({"name": "brand_colors_applied", "passed": brand_colors_found, "detail": "Colors detected"})

    except Exception as e:
        return {"passed": False, "score": 0.0, "detail": str(e)}

    score = sum(1 for c in checks if c['passed']) / len(checks)
    return {"passed": score >= 0.75, "score": score, "checks": checks}

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(json.dumps(check_presentation_styling(workspace)))