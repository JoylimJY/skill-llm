#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

def main(workspace_dir):
    workspace_path = Path(workspace_dir)
    checks = []
    
    # Check if the screenshot file was created
    screenshot_path = workspace_path / "contact_screenshot.png"
    screenshot_exists = screenshot_path.exists()
    checks.append({
        "name": "Screenshot file created",
        "passed": screenshot_exists,
        "detail": f"Expected contact_screenshot.png to exist at {screenshot_path}"
    })
    
    screenshot_valid_size = False
    if screenshot_exists:
        # Check if the screenshot has reasonable file size (not empty)
        file_size = screenshot_path.stat().st_size
        screenshot_valid_size = file_size > 1000  # At least 1KB
        checks.append({
            "name": "Screenshot has valid size",
            "passed": screenshot_valid_size,
            "detail": f"Screenshot file size: {file_size} bytes (expected > 1000)"
        })
    else:
        checks.append({
            "name": "Screenshot has valid size",
            "passed": False,
            "detail": "Cannot check size - screenshot file does not exist"
        })
    
    # Check if HTML file still exists (shouldn't be modified)
    html_path = workspace_path / "contact.html"
    html_exists = html_path.exists()
    checks.append({
        "name": "Original HTML file preserved",
        "passed": html_exists,
        "detail": f"Expected contact.html to still exist at {html_path}"
    })
    
    # Verify HTML contains marker content
    html_has_marker = False
    if html_exists:
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                html_has_marker = "CONTACT_FORM_MARKER_XYZ123" in html_content
        except Exception as e:
            html_has_marker = False
    
    checks.append({
        "name": "HTML contains expected marker",
        "passed": html_has_marker,
        "detail": "HTML should contain the marker text CONTACT_FORM_MARKER_XYZ123"
    })
    
    # Check if there's evidence of Playwright usage (look for common automation files)
    # This is indirect but helps verify the approach
    playwright_evidence = False
    for potential_file in workspace_path.glob("*.py"):
        try:
            with open(potential_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "playwright" in content.lower() and "screenshot" in content.lower():
                    playwright_evidence = True
                    break
        except Exception:
            continue
    
    checks.append({
        "name": "Playwright automation script found",
        "passed": playwright_evidence,
        "detail": "Expected to find a Python script using Playwright for screenshots"
    })
    
    # Calculate overall score
    passed_checks = sum(1 for check in checks if check["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Task passes if screenshot exists with valid size and HTML is preserved
    task_passed = screenshot_exists and screenshot_valid_size and html_exists and html_has_marker
    
    result = {
        "passed": task_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: eval_script.py <workspace_directory>", file=sys.stderr)
        sys.exit(1)
    
    main(sys.argv[1])