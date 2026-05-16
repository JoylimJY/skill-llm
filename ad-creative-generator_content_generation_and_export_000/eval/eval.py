import sys
import json
import os
from pathlib import Path

def check_json_output(workspace):
    """Check ads_pipeline.json - should only have eco and minimalist categories"""
    checks = []
    
    # Find the file anywhere in workspace
    matches = list(Path(workspace).rglob('ads_pipeline.json'))
    
    if not matches:
        checks.append({
            "name": "ads_pipeline.json exists",
            "passed": False,
            "detail": "File ads_pipeline.json not found anywhere in workspace"
        })
        return checks, None
    
    filepath = matches[0]
    checks.append({
        "name": "ads_pipeline.json exists",
        "passed": True,
        "detail": f"Found at {filepath}"
    })
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        checks.append({
            "name": "ads_pipeline.json is valid JSON",
            "passed": False,
            "detail": f"Failed to parse JSON: {e}"
        })
        return checks, None
    
    checks.append({
        "name": "ads_pipeline.json is valid JSON",
        "passed": True,
        "detail": "File parsed successfully"
    })
    
    # Check top-level schema: must have 'product', 'generated_at', 'prompts'
    has_product = "product" in data
    has_generated_at = "generated_at" in data
    has_prompts = "prompts" in data
    
    checks.append({
        "name": "JSON schema has 'product' field",
        "passed": has_product,
        "detail": f"Fields found: {list(data.keys())}"
    })
    checks.append({
        "name": "JSON schema has 'generated_at' field",
        "passed": has_generated_at,
        "detail": f"Fields found: {list(data.keys())}"
    })
    checks.append({
        "name": "JSON schema has 'prompts' array",
        "passed": has_prompts,
        "detail": f"Fields found: {list(data.keys())}"
    })
    
    if not (has_product and has_generated_at and has_prompts):
        return checks, data
    
    # Check product name
    product_correct = "VitaGlow Botanical Face Oil" in str(data.get("product", ""))
    checks.append({
        "name": "JSON product field contains 'VitaGlow Botanical Face Oil'",
        "passed": product_correct,
        "detail": f"Product field value: {data.get('product', 'MISSING')}"
    })
    
    # Check prompts are a list
    prompts = data.get("prompts", [])
    is_list = isinstance(prompts, list)
    checks.append({
        "name": "JSON 'prompts' is an array",
        "passed": is_list,
        "detail": f"Type: {type(prompts).__name__}"
    })
    
    if not is_list:
        return checks, data
    
    # Check each prompt has category, style, prompt fields
    all_have_fields = all(
        isinstance(p, dict) and "category" in p and "style" in p and "prompt" in p
        for p in prompts
    )
    checks.append({
        "name": "Each prompt object has 'category', 'style', 'prompt' fields",
        "passed": all_have_fields,
        "detail": f"Checked {len(prompts)} prompts. First item keys: {list(prompts[0].keys()) if prompts else 'empty'}"
    })
    
    # Check ONLY eco and minimalist categories are present (not ALL categories)
    if prompts:
        categories_found = set(p.get("category", "") for p in prompts)
        expected_categories = {"Eco/Green", "Minimalist"}
        
        # Must contain both expected categories
        has_eco = "Eco/Green" in categories_found
        has_minimalist = "Minimalist" in categories_found
        
        checks.append({
            "name": "JSON contains 'Eco/Green' category prompts",
            "passed": has_eco,
            "detail": f"Categories found: {categories_found}"
        })
        checks.append({
            "name": "JSON contains 'Minimalist' category prompts",
            "passed": has_minimalist,
            "detail": f"Categories found: {categories_found}"
        })
        
        # Must NOT contain other categories (it's a filtered export)
        other_categories = categories_found - expected_categories
        no_extra_categories = len(other_categories) == 0
        checks.append({
            "name": "JSON contains ONLY eco and minimalist categories (not all)",
            "passed": no_extra_categories,
            "detail": f"Unexpected categories: {other_categories}" if not no_extra_categories else "Correctly filtered to only eco and minimalist"
        })
        
        # Check product name appears in prompts
        product_in_prompts = all(
            "VitaGlow Botanical Face Oil" in p.get("prompt", "")
            for p in prompts
        )
        checks.append({
            "name": "Product name appears in all prompt texts",
            "passed": product_in_prompts,
            "detail": f"Checked {len(prompts)} prompts for product name injection"
        })
    
    return checks, data


def check_markdown_output(workspace):
    """Check creative_brief_all.md - should contain ALL 10 categories"""
    checks = []
    
    matches = list(Path(workspace).rglob('creative_brief_all.md'))
    
    if not matches:
        checks.append({
            "name": "creative_brief_all.md exists",
            "passed": False,
            "detail": "File creative_brief_all.md not found anywhere in workspace"
        })
        return checks
    
    filepath = matches[0]
    checks.append({
        "name": "creative_brief_all.md exists",
        "passed": True,
        "detail": f"Found at {filepath}"
    })
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except IOError as e:
        checks.append({
            "name": "creative_brief_all.md is readable",
            "passed": False,
            "detail": f"IO Error: {e}"
        })
        return checks
    
    checks.append({
        "name": "creative_brief_all.md is readable",
        "passed": True,
        "detail": f"File size: {len(content)} chars"
    })
    
    # Check it's actually markdown (has ## headers)
    has_headers = "##" in content
    checks.append({
        "name": "creative_brief_all.md contains markdown headers (##)",
        "passed": has_headers,
        "detail": "Found '##' markdown headers" if has_headers else "No markdown headers found"
    })
    
    # Check top-level title references product
    has_title = "# Ad Creative Prompts" in content
    checks.append({
        "name": "Markdown has proper title (# Ad Creative Prompts...)",
        "passed": has_title,
        "detail": f"First 200 chars: {content[:200]}"
    })
    
    # Check product name in the markdown
    has_product = "VitaGlow Botanical Face Oil" in content
    checks.append({
        "name": "Markdown contains product name 'VitaGlow Botanical Face Oil'",
        "passed": has_product,
        "detail": "Product name found in content" if has_product else "Product name not found"
    })
    
    # All 10 category names must appear as ## headers
    all_10_categories = [
        "Minimalist",
        "Product Transformation",
        "Cultural/Exotic",
        "Lifestyle",
        "Technology",
        "Luxury",
        "Eco/Green",
        "Seasonal",
        "Emotional",
        "Playful"
    ]
    
    missing_categories = []
    for cat in all_10_categories:
        if f"## {cat}" not in content:
            missing_categories.append(cat)
    
    all_present = len(missing_categories) == 0
    checks.append({
        "name": "Markdown contains all 10 category headers",
        "passed": all_present,
        "detail": f"Missing categories: {missing_categories}" if not all_present else "All 10 categories present as ## headers"
    })
    
    # Check that product name is injected into actual prompt texts
    # Count occurrences - with all styles there should be many
    product_count = content.count("VitaGlow Botanical Face Oil")
    enough_injections = product_count >= 20  # Should have 20+ prompts with the product name
    checks.append({
        "name": "Product name appears in prompts (20+ times for all styles)",
        "passed": enough_injections,
        "detail": f"Product name appears {product_count} times in markdown"
    })
    
    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    all_checks = []
    
    # Run JSON checks
    json_checks, json_data = check_json_output(workspace)
    all_checks.extend(json_checks)
    
    # Run Markdown checks  
    md_checks = check_markdown_output(workspace)
    all_checks.extend(md_checks)
    
    # Calculate score
    passed_count = sum(1 for c in all_checks if c["passed"])
    total_count = len(all_checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    
    # Overall pass requires critical checks to pass
    critical_checks = [
        "ads_pipeline.json exists",
        "JSON schema has 'product' field",
        "JSON schema has 'generated_at' field",
        "JSON schema has 'prompts' array",
        "JSON contains ONLY eco and minimalist categories (not all)",
        "creative_brief_all.md exists",
        "Markdown contains all 10 category headers",
    ]
    
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in all_checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.80
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": all_checks
    }
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()