import sys
import json
import re
import os
from pathlib import Path

workspace = sys.argv[1]
checks = []
total_score = 0.0

def make_check(name, passed, detail, weight=1.0):
    return {"name": name, "passed": passed, "detail": detail, "_weight": weight}

# ---- Locate the three required files ----
template_dir = Path(workspace) / "project" / "prompts" / "templates"

system_prompt_path = template_dir / "triage_system_prompt.txt"
user_template_path = template_dir / "triage_user_template.txt"
prefill_path = template_dir / "triage_prefill.json"

# Also do a broader search in case agent placed them elsewhere
def find_file(name):
    results = list(Path(workspace).rglob(name))
    # Prefer the expected location
    expected = template_dir / name
    if expected.exists():
        return expected
    return results[0] if results else None

sp_file = find_file("triage_system_prompt.txt")
ut_file = find_file("triage_user_template.txt")
pf_file = find_file("triage_prefill.json")

# ============================================================
# CHECK 1: Files exist
# ============================================================
for fname, fpath, label in [
    ("triage_system_prompt.txt", sp_file, "System Prompt"),
    ("triage_user_template.txt", ut_file, "User Template"),
    ("triage_prefill.json", pf_file, "Prefill JSON"),
]:
    exists = fpath is not None and Path(fpath).exists()
    checks.append(make_check(
        f"File exists: {fname}",
        exists,
        f"Found at {fpath}" if exists else f"{fname} not found anywhere in workspace",
        weight=0.5
    ))

# ============================================================
# READ FILES
# ============================================================
system_content = ""
user_content = ""
prefill_content = ""

try:
    if sp_file and Path(sp_file).exists():
        system_content = Path(sp_file).read_text(encoding="utf-8")
except Exception as e:
    checks.append(make_check("Read system prompt", False, str(e)))

try:
    if ut_file and Path(ut_file).exists():
        user_content = Path(ut_file).read_text(encoding="utf-8")
except Exception as e:
    checks.append(make_check("Read user template", False, str(e)))

try:
    if pf_file and Path(pf_file).exists():
        prefill_content = Path(pf_file).read_text(encoding="utf-8")
except Exception as e:
    checks.append(make_check("Read prefill json", False, str(e)))

# ============================================================
# CHECK 2: System Prompt - Specific role, not generic "best AI"
# ============================================================
try:
    bad_patterns = [
        r"你是最好的",
        r"你是一个很厉害",
        r"you are the best",
        r"没有什么是你不知道的",
    ]
    has_bad = any(re.search(p, system_content, re.IGNORECASE) for p in bad_patterns)
    
    # Must have specific role description - looking for medical/doctor role with experience
    good_role_patterns = [
        r"(主任|急诊|医师|医生|专家|医学)",
        r"(\d+\s*年|二十年|多年).*(经验|从业|临床)",
        r"(经验|专长|擅长).*(急诊|分诊|临床|医疗)",
    ]
    has_good_role = any(re.search(p, system_content, re.IGNORECASE) for p in good_role_patterns)
    
    passed = not has_bad and has_good_role and len(system_content.strip()) > 50
    checks.append(make_check(
        "System prompt: specific role (not generic 'best AI')",
        passed,
        f"has_bad_pattern={has_bad}, has_specific_role={has_good_role}, length={len(system_content)}",
        weight=1.5
    ))
except Exception as e:
    checks.append(make_check("System prompt: specific role", False, str(e), weight=1.5))

# ============================================================
# CHECK 3: System Prompt - Chinese language directive
# ============================================================
try:
    chinese_directive = bool(re.search(r"(用中文|中文回[复答]|以中文|Chinese|中文输出)", system_content, re.IGNORECASE))
    checks.append(make_check(
        "System prompt: Chinese language directive",
        chinese_directive,
        f"Found Chinese language instruction: {chinese_directive}",
        weight=1.0
    ))
except Exception as e:
    checks.append(make_check("System prompt: Chinese language directive", False, str(e), weight=1.0))

# ============================================================
# CHECK 4: User Template - Has XML tag structure
# ============================================================
try:
    xml_tags_found = []
    for tag in ["context", "task", "output_format", "examples", "document"]:
        if re.search(rf"<{tag}[\s>]", user_content, re.IGNORECASE) and re.search(rf"</{tag}>", user_content, re.IGNORECASE):
            xml_tags_found.append(tag)
    
    has_xml = len(xml_tags_found) >= 2
    checks.append(make_check(
        "User template: XML tag structure (at least 2 XML tag pairs)",
        has_xml,
        f"Found XML tag pairs: {xml_tags_found}",
        weight=2.0
    ))
except Exception as e:
    checks.append(make_check("User template: XML tag structure", False, str(e), weight=2.0))

# ============================================================
# CHECK 5: User Template - Has <examples> with proper nesting
# ============================================================
try:
    # Must have <examples> containing <example> containing <input> and <output>
    has_examples_block = bool(re.search(r"<examples>", user_content, re.IGNORECASE))
    has_example_tag = bool(re.search(r"<example>", user_content, re.IGNORECASE))
    has_input_tag = bool(re.search(r"<input>", user_content, re.IGNORECASE))
    has_output_tag = bool(re.search(r"<output>", user_content, re.IGNORECASE))
    
    # Check nesting: <examples>...<example>...<input>...</input>...<output>...</output>...</example>...</examples>
    nested_pattern = re.search(
        r"<examples>.*?<example>.*?<input>.*?</input>.*?<output>.*?</output>.*?</example>.*?</examples>",
        user_content, re.DOTALL | re.IGNORECASE
    )
    proper_nesting = bool(nested_pattern)
    
    checks.append(make_check(
        "User template: <examples><example><input><output> proper nesting",
        proper_nesting,
        f"has_examples={has_examples_block}, has_example={has_example_tag}, "
        f"has_input={has_input_tag}, has_output={has_output_tag}, proper_nesting={proper_nesting}",
        weight=2.5
    ))
except Exception as e:
    checks.append(make_check("User template: proper examples nesting", False, str(e), weight=2.5))

# ============================================================
# CHECK 6: User Template - Has at least 2 examples (few-shot)
# ============================================================
try:
    example_count = len(re.findall(r"<example>", user_content, re.IGNORECASE))
    has_multiple_examples = example_count >= 2
    checks.append(make_check(
        "User template: at least 2 few-shot examples",
        has_multiple_examples,
        f"Found {example_count} <example> tags",
        weight=1.5
    ))
except Exception as e:
    checks.append(make_check("User template: at least 2 few-shot examples", False, str(e), weight=1.5))

# ============================================================
# CHECK 7: User Template - Chain-of-thought with <thinking> tag instruction
# ============================================================
try:
    thinking_instruction = bool(re.search(r"<thinking>|thinking\s*标签|thinking.*分析|展示.*思(考|维|路)|推理过程", user_content, re.IGNORECASE))
    checks.append(make_check(
        "User template: <thinking> tag instruction for chain-of-thought",
        thinking_instruction,
        f"Found thinking/CoT instruction: {thinking_instruction}",
        weight=2.0
    ))
except Exception as e:
    checks.append(make_check("User template: <thinking> CoT instruction", False, str(e), weight=2.0))

# ============================================================
# CHECK 8: User Template - JSON output format specification
# ============================================================
try:
    json_output = bool(re.search(r"(JSON|json)\s*(格式|输出|format)", user_content, re.IGNORECASE))
    required_fields = ["triage_level", "primary_diagnosis", "recommended_actions", "urgency_reasoning"]
    fields_found = [f for f in required_fields if f in user_content]
    
    output_format_specified = json_output and len(fields_found) >= 3
    checks.append(make_check(
        "User template: JSON output format with required fields",
        output_format_specified,
        f"json_output={json_output}, required fields found={fields_found}",
        weight=1.5
    ))
except Exception as e:
    checks.append(make_check("User template: JSON output format", False, str(e), weight=1.5))

# ============================================================
# CHECK 9: User Template - Template variables (placeholders)
# ============================================================
try:
    placeholders = re.findall(r"\{\{(\w+)\}\}", user_content)
    has_placeholders = len(placeholders) >= 2
    medical_placeholders = any(p in placeholders for p in [
        "patient_data", "chief_complaint", "vital_signs", "symptoms", "medical_history", "data"
    ])
    checks.append(make_check(
        "User template: has template variable placeholders {{...}}",
        has_placeholders and medical_placeholders,
        f"Placeholders found: {placeholders}",
        weight=1.0
    ))
except Exception as e:
    checks.append(make_check("User template: template placeholders", False, str(e), weight=1.0))

# ============================================================
# CHECK 10: Primacy/Recency - Important instruction at start AND end
# ============================================================
try:
    lines = user_content.strip().split('\n')
    total_lines = len(lines)
    
    if total_lines >= 6:
        first_20pct = '\n'.join(lines[:max(3, total_lines//5)])
        last_20pct = '\n'.join(lines[-max(3, total_lines//5):])
        
        # Check that there's meaningful instruction content (not just XML closing tags) at both ends
        instruction_pattern = r"(请|必须|需要|分析|评估|输出|JSON|用中文|按照|格式|triage|严格|确保)"
        has_instruction_start = bool(re.search(instruction_pattern, first_20pct, re.IGNORECASE))
        has_instruction_end = bool(re.search(instruction_pattern, last_20pct, re.IGNORECASE))
        
        primacy_recency = has_instruction_start and has_instruction_end
        checks.append(make_check(
            "User template: key instructions at both start and end (primacy+recency)",
            primacy_recency,
            f"Instruction at start: {has_instruction_start}, at end: {has_instruction_end}",
            weight=1.5
        ))
    else:
        checks.append(make_check(
            "User template: key instructions at both start and end (primacy+recency)",
            False,
            f"Template too short ({total_lines} lines) to evaluate placement",
            weight=1.5
        ))
except Exception as e:
    checks.append(make_check("User template: primacy+recency placement", False, str(e), weight=1.5))

# ============================================================
# CHECK 11: Prefill JSON - Correct structure
# ============================================================
try:
    prefill_data = json.loads(prefill_content)
    has_role = prefill_data.get("role") == "assistant"
    has_content = "content" in prefill_data and len(str(prefill_data.get("content", ""))) > 0
    
    # Prefill should guide toward JSON output - should start with { or ```json
    content_val = str(prefill_data.get("content", ""))
    starts_json = content_val.strip().startswith(("{", "```json", "{\n"))
    
    prefill_valid = has_role and has_content and starts_json
    checks.append(make_check(
        "Prefill JSON: correct structure with role=assistant and JSON-guiding content",
        prefill_valid,
        f"role_correct={has_role}, has_content={has_content}, starts_with_json={starts_json}, content='{content_val[:50]}'",
        weight=2.5
    ))
except json.JSONDecodeError as e:
    checks.append(make_check(
        "Prefill JSON: valid JSON format",
        False,
        f"JSON parse error: {e}",
        weight=2.5
    ))
except Exception as e:
    checks.append(make_check("Prefill JSON: structure check", False, str(e), weight=2.5))

# ============================================================
# CHECK 12: System prompt - No hallucination encouragement; includes uncertainty handling
# ============================================================
try:
    uncertainty_handling = bool(re.search(
        r"(不知道|不确定|无法判断|缺乏信息|说.{0,10}不知道|如果.*不.*确定|uncertain|unknown)",
        system_content, re.IGNORECASE
    ))
    checks.append(make_check(
        "System prompt: uncertainty/hallucination handling instruction",
        uncertainty_handling,
        f"Found uncertainty instruction: {uncertainty_handling}",
        weight=1.0
    ))
except Exception as e:
    checks.append(make_check("System prompt: uncertainty handling", False, str(e), weight=1.0))

# ============================================================
# COMPUTE FINAL SCORE
# ============================================================
total_weight = sum(c["_weight"] for c in checks)
earned_weight = sum(c["_weight"] for c in checks if c["passed"])
score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0

# Clean output (remove internal _weight field)
output_checks = [{"name": c["name"], "passed": c["passed"], "detail": c["detail"]} for c in checks]

passed_overall = score >= 0.70

result = {
    "passed": passed_overall,
    "score": score,
    "checks": output_checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))