#!/usr/bin/env python3
import sys
import os
import json
import re

def check_communication_output(workspace_dir):
    checks = []
    score = 0.0
    
    # Look for output files that could contain the communication
    output_files = []
    for file in os.listdir(workspace_dir):
        if file.endswith(('.txt', '.md', '.doc', '.docx')) or 'communication' in file.lower() or 'update' in file.lower() or 'newsletter' in file.lower():
            output_files.append(file)
    
    if not output_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_exists", "passed": False, "detail": "No communication output file found"}]
        }
    
    # Read the content from output files
    content = ""
    for file in output_files:
        try:
            with open(os.path.join(workspace_dir, file), 'r', encoding='utf-8') as f:
                content += f.read() + "\n"
        except:
            continue
    
    if not content:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "content_readable", "passed": False, "detail": "Could not read communication content"}]
        }
    
    content_lower = content.lower()
    
    # Check 1: Contains company name and CEO context
    company_check = "neobank" in content_lower and any(name in content_lower for name in ["mike rodriguez", "ceo", "leadership"])
    checks.append({"name": "company_context", "passed": company_check, "detail": "Contains NeoBank and leadership context"})
    if company_check:
        score += 0.15
    
    # Check 2: Funding announcement with key details
    funding_check = ("series c" in content_lower or "$120m" in content_lower or "120 million" in content_lower) and "sequoia" in content_lower
    checks.append({"name": "funding_announcement", "passed": funding_check, "detail": "Includes Series C funding details"})
    if funding_check:
        score += 0.15
    
    # Check 3: Product launch information
    product_check = ("neocard" in content_lower or "credit card" in content_lower) and ("launch" in content_lower or "product" in content_lower)
    checks.append({"name": "product_launch", "passed": product_check, "detail": "Mentions NeoCard/credit card launch"})
    if product_check:
        score += 0.15
    
    # Check 4: User milestone
    users_check = ("500k" in content_lower or "500,000" in content_lower or "half million" in content_lower) and "users" in content_lower
    checks.append({"name": "user_milestone", "passed": users_check, "detail": "Mentions 500K user milestone"})
    if users_check:
        score += 0.15
    
    # Check 5: New CTO hire
    cto_check = "sarah chen" in content_lower and ("cto" in content_lower or "stripe" in content_lower)
    checks.append({"name": "cto_hire", "passed": cto_check, "detail": "Announces Sarah Chen as new CTO"})
    if cto_check:
        score += 0.10
    
    # Check 6: EU expansion challenges
    eu_check = ("eu" in content_lower or "europe" in content_lower) and ("delay" in content_lower or "regulatory" in content_lower)
    checks.append({"name": "eu_challenges", "passed": eu_challenge, "detail": "Addresses EU expansion delays"})
    if eu_check:
        score += 0.10
    
    # Check 7: Policy updates (hybrid work)
    policy_check = ("hybrid" in content_lower or "remote" in content_lower) and ("work" in content_lower or "policy" in content_lower)
    checks.append({"name": "work_policy", "passed": policy_check, "detail": "Addresses hybrid work policy"})
    if policy_check:
        score += 0.10
    
    # Check 8: Performance review information
    review_check = "performance" in content_lower and ("review" in content_lower or "feedback" in content_lower)
    checks.append({"name": "performance_reviews", "passed": review_check, "detail": "Mentions performance review process"})
    if review_check:
        score += 0.10
    
    # Check 9: Appropriate formatting and structure
    structure_check = len(content) > 500 and ("\n" in content or len(content.split('.')) > 5)
    checks.append({"name": "proper_structure", "passed": structure_check, "detail": "Has appropriate length and structure for company-wide communication"})
    if structure_check:
        score += 0.05
    
    # Overall pass condition: score >= 0.6 (covering most major topics)
    passed = score >= 0.6
    
    return {
        "passed": passed,
        "score": round(score, 2),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = check_communication_output(sys.argv[1])
    print(json.dumps(result))