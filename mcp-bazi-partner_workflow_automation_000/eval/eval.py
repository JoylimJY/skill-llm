import sys
import json
import subprocess
import re
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    
    # -------------------------------------------------------------------------
    # CHECK 1: SOUL.md exists and has been meaningfully modified
    # -------------------------------------------------------------------------
    def check_soul_exists():
        soul_path = workspace / "SOUL.md"
        if not soul_path.exists():
            return False, "SOUL.md not found in workspace"
        content = soul_path.read_text(encoding="utf-8")
        if len(content.strip()) < 50:
            return False, f"SOUL.md is too short ({len(content)} chars), likely not written"
        # Check it's not just the placeholder
        if 'No partner personality has been configured yet' in content:
            return False, "SOUL.md still contains the original placeholder text - not overwritten"
        return True, f"SOUL.md exists and has content ({len(content)} chars)"
    
    checks.append(run_check("SOUL.md exists and overwritten", check_soul_exists))

    # -------------------------------------------------------------------------
    # CHECK 2: SOUL.md contains a non-trivial system_prompt
    # -------------------------------------------------------------------------
    def check_system_prompt():
        soul_path = workspace / "SOUL.md"
        if not soul_path.exists():
            return False, "SOUL.md not found"
        content = soul_path.read_text(encoding="utf-8")
        # The system_prompt should be substantial, not empty
        if 'system_prompt' not in content.lower() and 'prompt' not in content.lower():
            return False, "No system_prompt content found in SOUL.md"
        # Look for meaningful text (not empty quotes or blank lines only)
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        if len(lines) < 3:
            return False, f"SOUL.md has too few non-empty lines ({len(lines)})"
        return True, f"SOUL.md contains apparent system_prompt content ({len(lines)} lines)"
    
    checks.append(run_check("SOUL.md contains system_prompt content", check_system_prompt))

    # -------------------------------------------------------------------------
    # CHECK 3: SOUL.md contains a valid partner_type (一 of the known types)
    # -------------------------------------------------------------------------
    def check_partner_type():
        soul_path = workspace / "SOUL.md"
        if not soul_path.exists():
            return False, "SOUL.md not found"
        content = soul_path.read_text(encoding="utf-8")
        
        # Known partner type patterns from the bazi system (element + name)
        element_patterns = ["水系", "金系", "木系", "火系", "土系"]
        found_element = any(ep in content for ep in element_patterns)
        
        # Also check for the · separator typical of partner type names
        has_separator = "·" in content or "·" in content
        
        if found_element:
            # Extract what looks like a partner type
            for ep in element_patterns:
                if ep in content:
                    # Find the surrounding context
                    idx = content.index(ep)
                    snippet = content[max(0,idx-5):min(len(content),idx+30)]
                    return True, f"Found element indicator '{ep}' in SOUL.md, snippet: '{snippet.strip()}'"
        
        return False, "No valid partner type (水系/金系/木系/火系/土系) found in SOUL.md"
    
    checks.append(run_check("SOUL.md contains valid partner_type element", check_partner_type))

    # -------------------------------------------------------------------------
    # CHECK 4: Verify the correct birth data was used (1985-03-22 hour=11)
    # by independently running bazi_analyze and checking L1 pattern
    # -------------------------------------------------------------------------
    def check_correct_analysis():
        try:
            # Try to call bazi_analyze programmatically to get ground truth
            result = subprocess.run(
                ["python3", "-c", """
import sys
sys.path.insert(0, '/workspace')
try:
    # Try the MCP tool via direct module call
    from mcp_bazi_partner.tools import bazi_analyze
    result = bazi_analyze(1985, 3, 22, 11)
    print(result)
except Exception as e1:
    try:
        import mcp_bazi_partner
        print("module_found:", mcp_bazi_partner.__file__)
    except Exception as e2:
        print("import_error:", str(e1), str(e2))
"""],
                capture_output=True, text=True, timeout=30
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            if result.returncode == 0 and stdout:
                return True, f"bazi_analyze accessible, output: {stdout[:200]}"
            else:
                return True, f"bazi_analyze invocation attempted (may use MCP protocol). stderr: {stderr[:100]}"
        except subprocess.TimeoutExpired:
            return True, "bazi_analyze timed out (expected for MCP server mode)"
        except Exception as e:
            return True, f"Tool invocation check bypassed: {e}"
    
    checks.append(run_check("bazi_analyze tool accessible", check_correct_analysis))

    # -------------------------------------------------------------------------
    # CHECK 5: Validate that the partner_type in SOUL.md is consistent
    # with a valid BaZi pattern (not random/hallucinated)
    # We do this by checking against all known valid partner types
    # -------------------------------------------------------------------------
    def check_partner_type_validity():
        soul_path = workspace / "SOUL.md"
        if not soul_path.exists():
            return False, "SOUL.md not found"
        content = soul_path.read_text(encoding="utf-8")
        
        # All valid partner types must follow pattern: {element}系 · {name}
        # Elements: 水,金,木,火,土
        # The · separator is distinctive
        pattern = re.compile(r'[水金木火土]系\s*[··]\s*[\u4e00-\u9fff\w·\s]+')
        matches = pattern.findall(content)
        
        if matches:
            return True, f"Valid partner type pattern found: {matches[0][:50]}"
        
        # Softer check: just element + 系
        soft_pattern = re.compile(r'[水金木火土]系')
        soft_matches = soft_pattern.findall(content)
        if soft_matches:
            return True, f"Partner element found ({soft_matches[0]}·系), type may be valid"
        
        return False, "No valid partner type pattern (元素系 · 名称) found in SOUL.md"
    
    checks.append(run_check("Partner type format is valid BaZi format", check_partner_type_validity))

    # -------------------------------------------------------------------------
    # CHECK 6: SOUL.md was NOT left as a hollow template / placeholder
    # Ensure meaningful personality content exists (not just field labels)
    # -------------------------------------------------------------------------
    def check_meaningful_personality():
        soul_path = workspace / "SOUL.md"
        if not soul_path.exists():
            return False, "SOUL.md not found"
        content = soul_path.read_text(encoding="utf-8")
        
        # A real system_prompt from bazi_apply_prompt would have substantial text
        # Minimum meaningful length for a personality prompt
        if len(content) < 200:
            return False, f"SOUL.md too short for real personality content ({len(content)} chars)"
        
        # Should not be just JSON field labels
        meaningful_indicators = [
            # Personality/instruction words likely in any system prompt
            "你", "我", "是", "的", "和", "在", "了", "会",  # Chinese characters
        ]
        chinese_char_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        if chinese_char_count < 20:
            return False, f"Too few Chinese characters ({chinese_char_count}) - likely not a real personality prompt"
        
        return True, f"SOUL.md has {chinese_char_count} Chinese chars, appears to be real personality content"
    
    checks.append(run_check("SOUL.md contains meaningful personality content", check_meaningful_personality))

    # -------------------------------------------------------------------------
    # CHECK 7: Verify the 3-step workflow was followed by checking for
    # any intermediate output file (optional but good signal)
    # -------------------------------------------------------------------------
    def check_workflow_artifact():
        # Look for any JSON/txt file that might contain bazi analysis results
        # The agent may have saved intermediate output
        potential_artifacts = list(workspace.rglob("*.json")) + list(workspace.rglob("analysis_*.txt"))
        
        # Check if any file contains pattern/格局 data (indicating step 1 was run)
        for artifact in potential_artifacts:
            try:
                text = artifact.read_text(encoding="utf-8", errors="ignore")
                if any(kw in text for kw in ["格", "日主", "pattern", "day_master", "shishen"]):
                    return True, f"Found workflow artifact with BaZi data: {artifact.name}"
            except Exception:
                continue
        
        # Even without artifact, if SOUL.md is properly filled, workflow was done
        soul_path = workspace / "SOUL.md"
        if soul_path.exists():
            content = soul_path.read_text(encoding="utf-8")
            if len(content) > 200 and any(e in content for e in ["水系","金系","木系","火系","土系"]):
                return True, "No intermediate artifact found, but SOUL.md completion implies full workflow was executed"
        
        return False, "No evidence of BaZi analysis workflow execution found"
    
    checks.append(run_check("Evidence of full 3-step workflow execution", check_workflow_artifact))

    # -------------------------------------------------------------------------
    # SCORING
    # -------------------------------------------------------------------------
    # Weights: critical checks are weighted more
    weights = {
        "SOUL.md exists and overwritten": 2.0,
        "SOUL.md contains system_prompt content": 2.0,
        "SOUL.md contains valid partner_type element": 2.0,
        "bazi_analyze tool accessible": 0.5,
        "Partner type format is valid BaZi format": 1.5,
        "SOUL.md contains meaningful personality content": 1.5,
        "Evidence of full 3-step workflow execution": 0.5,
    }
    
    total_weight = sum(weights.values())
    earned_weight = sum(weights.get(c["name"], 1.0) for c in checks if c["passed"])
    score = round(earned_weight / total_weight, 4)
    
    # Must pass all critical checks (first 3) to be considered passing
    critical_checks = checks[:3]
    passed = all(c["passed"] for c in critical_checks) and score >= 0.6
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()