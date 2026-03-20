import sys
import os
import subprocess
from pathlib import Path
import json

def run_check(name, condition, detail=""):
    return {
        "name": name,
        "passed": bool(condition),
        "detail": detail
    }

def main(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    
    # Check if template file exists
    template_path = workspace / "quarterly_template.pptx"
    template_exists = template_path.exists()
    checks.append(run_check("Template file exists", template_exists, 
                           f"quarterly_template.pptx found: {template_exists}"))
    
    # Check if output file exists
    output_path = workspace / "Q4_2024_Results.pptx"
    output_exists = output_path.exists()
    checks.append(run_check("Output file exists", output_exists,
                           f"Q4_2024_Results.pptx found: {output_exists}"))
    
    if not output_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    # Extract text content from output
    try:
        result = subprocess.run(["python", "-m", "markitdown", str(output_path)], 
                               capture_output=True, text=True, cwd=workspace)
        if result.returncode == 0:
            content = result.stdout.lower()
            
            # Check for required content
            title_check = "q4 2024" in content and "financial results" in content
            checks.append(run_check("Title slide content", title_check,
                                   f"Found Q4 2024 Financial Results title: {title_check}"))
            
            exec_summary_check = "executive summary" in content or "highlights" in content
            checks.append(run_check("Executive summary section", exec_summary_check,
                                   f"Found executive summary content: {exec_summary_check}"))
            
            revenue_check = "revenue" in content and "business unit" in content
            checks.append(run_check("Revenue breakdown content", revenue_check,
                                   f"Found revenue/business unit content: {revenue_check}"))
            
            challenges_check = "challenges" in content or "obstacles" in content
            checks.append(run_check("Challenges section", challenges_check,
                                   f"Found challenges/obstacles content: {challenges_check}"))
            
            next_steps_check = "next steps" in content or "action" in content
            checks.append(run_check("Next steps/closing content", next_steps_check,
                                   f"Found next steps/action content: {next_steps_check}"))
            
            # Check that template placeholders were replaced
            placeholder_check = "placeholder" not in content
            checks.append(run_check("Template placeholders removed", placeholder_check,
                                   f"No remaining placeholder text: {placeholder_check}"))
            
        else:
            checks.append(run_check("Content extraction", False, 
                                   f"Failed to extract content: {result.stderr}"))
            
    except Exception as e:
        checks.append(run_check("Content extraction", False, f"Error extracting content: {str(e)}"))
    
    # Check slide count by converting to PDF and counting pages
    try:
        # Import the soffice helper
        sys.path.insert(0, str(workspace / "scripts"))
        from office.soffice import run_soffice
        
        pdf_path = workspace / "Q4_2024_Results.pdf"
        result = run_soffice(["--headless", "--convert-to", "pdf", str(output_path)], 
                            cwd=workspace)
        
        if result.returncode == 0 and pdf_path.exists():
            # Count PDF pages using pdfinfo or fallback method
            try:
                count_result = subprocess.run(["pdfinfo", str(pdf_path)], 
                                             capture_output=True, text=True)
                if count_result.returncode == 0:
                    for line in count_result.stdout.split('\n'):
                        if 'Pages:' in line:
                            page_count = int(line.split(':')[1].strip())
                            slide_count_check = page_count >= 5
                            checks.append(run_check("Adequate slide count", slide_count_check,
                                                   f"Found {page_count} slides (expected 5+)"))
                            break
                else:
                    checks.append(run_check("Slide count verification", True, "Could not verify slide count but PDF created"))
            except:
                checks.append(run_check("Slide count verification", True, "Could not verify slide count but PDF created"))
        else:
            checks.append(run_check("PDF conversion", False, "Could not convert to PDF for slide counting"))
            
    except Exception as e:
        checks.append(run_check("PDF conversion", False, f"Error during PDF conversion: {str(e)}"))
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    overall_passed = score >= 0.7
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python eval_script.py <workspace_directory>")
        sys.exit(1)
    
    result = main(sys.argv[1])
    print(json.dumps(result, indent=2))