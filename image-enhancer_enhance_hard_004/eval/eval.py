import os
import sys
import json
from PIL import Image

def main(workspace_dir):
    checks = []
    
    # Check 1: Enhanced dashboard-screenshot exists
    dashboard_enhanced = os.path.join(workspace_dir, 'dashboard-screenshot-enhanced.png')
    dashboard_original = os.path.join(workspace_dir, 'dashboard-screenshot.png')
    
    if os.path.exists(dashboard_enhanced) and os.path.exists(dashboard_original):
        try:
            orig_img = Image.open(dashboard_original)
            enh_img = Image.open(dashboard_enhanced)
            orig_width = orig_img.width
            enh_width = enh_img.width
            if enh_width >= 2048 and enh_width > orig_width:
                checks.append({"name": "dashboard_enhanced_upscaled", "passed": True, "detail": f"Dashboard enhanced from {orig_width}px to {enh_width}px width"})
            else:
                checks.append({"name": "dashboard_enhanced_upscaled", "passed": False, "detail": f"Dashboard not properly upscaled: {orig_width}px -> {enh_width}px"})
        except Exception as e:
            checks.append({"name": "dashboard_enhanced_upscaled", "passed": False, "detail": f"Error processing dashboard images: {str(e)}"})
    else:
        checks.append({"name": "dashboard_enhanced_upscaled", "passed": False, "detail": "Dashboard enhanced file not found or original missing"})
    
    # Check 2: Enhanced company-logo exists and upscaled
    logo_enhanced_png = os.path.join(workspace_dir, 'company-logo-enhanced.png')
    logo_enhanced_jpg = os.path.join(workspace_dir, 'company-logo-enhanced.jpg')
    logo_original = os.path.join(workspace_dir, 'company-logo.jpg')
    
    logo_enhanced = logo_enhanced_png if os.path.exists(logo_enhanced_png) else (logo_enhanced_jpg if os.path.exists(logo_enhanced_jpg) else None)
    
    if logo_enhanced and os.path.exists(logo_original):
        try:
            orig_img = Image.open(logo_original)
            enh_img = Image.open(logo_enhanced)
            orig_width = orig_img.width
            enh_width = enh_img.width
            if enh_width >= 2048 and enh_width > orig_width:
                checks.append({"name": "logo_enhanced_upscaled", "passed": True, "detail": f"Logo enhanced from {orig_width}px to {enh_width}px width"})
            else:
                checks.append({"name": "logo_enhanced_upscaled", "passed": False, "detail": f"Logo not properly upscaled: {orig_width}px -> {enh_width}px"})
        except Exception as e:
            checks.append({"name": "logo_enhanced_upscaled", "passed": False, "detail": f"Error processing logo images: {str(e)}"})
    else:
        checks.append({"name": "logo_enhanced_upscaled", "passed": False, "detail": "Logo enhanced file not found or original missing"})
    
    # Check 3: Enhanced sales-chart exists
    chart_enhanced = os.path.join(workspace_dir, 'sales-chart-enhanced.png')
    chart_original = os.path.join(workspace_dir, 'sales-chart.png')
    
    if os.path.exists(chart_enhanced) and os.path.exists(chart_original):
        try:
            orig_img = Image.open(chart_original)
            enh_img = Image.open(chart_enhanced)
            orig_width = orig_img.width
            enh_width = enh_img.width
            if enh_width >= 2048 and enh_width >= orig_width:
                checks.append({"name": "chart_enhanced_processed", "passed": True, "detail": f"Chart processed from {orig_width}px to {enh_width}px width"})
            else:
                checks.append({"name": "chart_enhanced_processed", "passed": False, "detail": f"Chart not properly processed: {orig_width}px -> {enh_width}px"})
        except Exception as e:
            checks.append({"name": "chart_enhanced_processed", "passed": False, "detail": f"Error processing chart images: {str(e)}"})
    else:
        checks.append({"name": "chart_enhanced_processed", "passed": False, "detail": "Chart enhanced file not found or original missing"})
    
    # Check 4: Original files preserved
    originals_preserved = all(os.path.exists(os.path.join(workspace_dir, f)) for f in ['dashboard-screenshot.png', 'company-logo.jpg', 'sales-chart.png'])
    if originals_preserved:
        checks.append({"name": "originals_preserved", "passed": True, "detail": "All original files preserved as backups"})
    else:
        checks.append({"name": "originals_preserved", "passed": False, "detail": "Some original files were not preserved"})
    
    # Check 5: Enhancement report exists with proper content
    report_file = os.path.join(workspace_dir, 'enhancement-report.md')
    if os.path.exists(report_file):
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report_content = f.read().lower()
            
            required_elements = [
                ('dashboard-screenshot', 'dashboard-screenshot mentioned'),
                ('company-logo', 'company-logo mentioned'),
                ('sales-chart', 'sales-chart mentioned'),
                ('dimension', 'dimensions information included'),
                ('size', 'file size information included'),
                ('enhancement', 'enhancement details included')
            ]
            
            missing_elements = []
            for element, description in required_elements:
                if element not in report_content:
                    missing_elements.append(description)
            
            if not missing_elements:
                checks.append({"name": "enhancement_report_complete", "passed": True, "detail": "Enhancement report contains all required information"})
            else:
                checks.append({"name": "enhancement_report_complete", "passed": False, "detail": f"Enhancement report missing: {', '.join(missing_elements)}"})
        except Exception as e:
            checks.append({"name": "enhancement_report_complete", "passed": False, "detail": f"Error reading enhancement report: {str(e)}"})
    else:
        checks.append({"name": "enhancement_report_complete", "passed": False, "detail": "Enhancement report file 'enhancement-report.md' not found"})
    
    # Check 6: Non-image files ignored
    readme_enhanced = os.path.join(workspace_dir, 'readme-enhanced.txt')
    if not os.path.exists(readme_enhanced):
        checks.append({"name": "non_image_files_ignored", "passed": True, "detail": "Non-image files correctly ignored"})
    else:
        checks.append({"name": "non_image_files_ignored", "passed": False, "detail": "Non-image file was incorrectly processed"})
    
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main(sys.argv[1])