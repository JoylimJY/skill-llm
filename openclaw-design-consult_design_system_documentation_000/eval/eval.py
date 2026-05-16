import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    ws = Path(workspace_dir)
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── DESIGN.md existence ──────────────────────────────────────────────────
    design_path = ws / "DESIGN.md"
    try:
        design_content = design_path.read_text(encoding="utf-8")
        total_score += add_check(
            "DESIGN.md exists",
            True,
            f"Found DESIGN.md ({len(design_content)} chars)",
            weight=0.5
        )
    except Exception as e:
        total_score += add_check("DESIGN.md exists", False, f"DESIGN.md not found: {e}", weight=0.5)
        design_content = ""

    # ── DESIGN.md: Required top-level sections ────────────────────────────────
    required_sections = [
        ("产品上下文", r"##\s*(产品上下文|Product Context)"),
        ("美学方向",   r"##\s*(美学方向|Aesthetic Direction)"),
        ("字体",       r"##\s*(字体|Typography|Fonts?)"),
        ("颜色",       r"##\s*(颜色|Colours?|Colors?)"),
        ("间距",       r"##\s*(间距|Spacing)"),
        ("布局",       r"##\s*(布局|Layout)"),
        ("动效",       r"##\s*(动效|Motion|Animation)"),
        ("决策日志",   r"##\s*(决策日志|Decision Log)"),
    ]
    for sec_name, pattern in required_sections:
        found = bool(re.search(pattern, design_content, re.IGNORECASE))
        total_score += add_check(
            f"DESIGN.md section: {sec_name}",
            found,
            f"Section '{sec_name}' {'found' if found else 'MISSING'} in DESIGN.md",
            weight=0.3
        )

    # ── DESIGN.md: 装饰等级 field present ────────────────────────────────────
    decoration_level = bool(re.search(r"装饰等级|Decoration Level|decorat", design_content, re.IGNORECASE))
    total_score += add_check(
        "DESIGN.md: 装饰等级 (decoration level) field present",
        decoration_level,
        "Field '装饰等级' or equivalent found" if decoration_level else "Field '装饰等级' MISSING — required by SKILL.md schema",
        weight=0.4
    )

    # ── DESIGN.md: 氛围 (vibe/mood) field present ────────────────────────────
    vibe_present = bool(re.search(r"氛围|Vibe|Mood|Atmosphere", design_content, re.IGNORECASE))
    total_score += add_check(
        "DESIGN.md: 氛围 (mood/vibe) field present",
        vibe_present,
        "Field '氛围' or equivalent found" if vibe_present else "Field '氛围' MISSING — required by SKILL.md schema",
        weight=0.3
    )

    # ── DESIGN.md: 决策日志 has table rows ───────────────────────────────────
    has_log_table = bool(re.search(r"\|\s*.+\s*\|\s*.+\s*\|\s*.+\s*\|", design_content))
    total_score += add_check(
        "DESIGN.md: 决策日志 contains markdown table",
        has_log_table,
        "Markdown table found in 决策日志" if has_log_table else "No table rows found in 决策日志 section",
        weight=0.3
    )

    # ── DESIGN.md: Hex color values present ──────────────────────────────────
    hex_colors = re.findall(r"#[0-9A-Fa-f]{6}\b", design_content)
    has_hex = len(hex_colors) >= 4
    total_score += add_check(
        "DESIGN.md: Contains hex color palette (≥4 values)",
        has_hex,
        f"Found {len(hex_colors)} hex color values: {hex_colors[:8]}",
        weight=0.4
    )

    # ── DESIGN.md: Semantic colors (success/warning/error) ───────────────────
    semantic = bool(re.search(r"success.{0,40}#[0-9A-Fa-f]{6}", design_content, re.IGNORECASE)) and \
               bool(re.search(r"error.{0,40}#[0-9A-Fa-f]{6}", design_content, re.IGNORECASE))
    total_score += add_check(
        "DESIGN.md: Semantic colors (success/error) with hex values",
        semantic,
        "Semantic color hex values present" if semantic else "Semantic colors missing hex values",
        weight=0.3
    )

    # ── DESIGN.md: Spacing base unit present ─────────────────────────────────
    spacing = bool(re.search(r"(4px|8px|base.{0,20}unit|unit.{0,20}(4|8))", design_content, re.IGNORECASE))
    total_score += add_check(
        "DESIGN.md: Spacing base unit specified (4px or 8px)",
        spacing,
        "Spacing base unit found" if spacing else "Spacing base unit (4px or 8px) not specified",
        weight=0.3
    )

    # ── DESIGN.md: Font rationale present ────────────────────────────────────
    font_rationale = bool(re.search(r"(展示|正文|UI|Display|Body|Label|Heading).{0,60}—.{5,}", design_content))
    total_score += add_check(
        "DESIGN.md: Font entries include rationale (— reason)",
        font_rationale,
        "Font entries with rationale (— ...) found" if font_rationale else "Font entries lack rationale",
        weight=0.3
    )

    # ── DESIGN.md: SAFE/RISK decomposition present ───────────────────────────
    safe_risk = bool(re.search(r"(SAFE|安全选择|safe.choice)", design_content, re.IGNORECASE)) and \
                bool(re.search(r"(RISK|风险|risk)", design_content, re.IGNORECASE))
    total_score += add_check(
        "DESIGN.md: Contains SAFE/RISK design decomposition",
        safe_risk,
        "SAFE and RISK sections found" if safe_risk else "SAFE/RISK decomposition missing — required by Phase 3",
        weight=0.4
    )

    # ── FONT BLACKLIST: Overused fonts NOT used as display/primary ────────────
    overused_fonts = ["Inter", "Roboto", "Arial", "Helvetica", "Open Sans", "Lato", "Montserrat", "Poppins"]
    blacklisted_used = []

    # Look for font definitions in the 字体 section
    font_section_match = re.search(
        r"##\s*(字体|Typography|Fonts?)(.*?)(?=\n##|\Z)",
        design_content,
        re.DOTALL | re.IGNORECASE
    )
    font_section_text = font_section_match.group(2) if font_section_match else design_content

    for font in overused_fonts:
        # Check if the font appears as a primary/display font recommendation
        # Allow it in a "do not use" context or as body/secondary only with caveats
        pattern_display = re.compile(
            rf"(展示|Display|Heading|Primary|主标题|主字体).{{0,120}}{font}",
            re.IGNORECASE
        )
        if pattern_display.search(font_section_text):
            blacklisted_used.append(font)

    no_blacklisted_display = len(blacklisted_used) == 0
    total_score += add_check(
        "Font blacklist respected: no overused font as display/primary",
        no_blacklisted_display,
        f"No blacklisted fonts as display/primary" if no_blacklisted_display
        else f"VIOLATION: overused font(s) used as display/primary: {blacklisted_used}",
        weight=0.8
    )

    # ── FONT BLACKLIST: Hard blacklisted fonts not present at all ────────────
    hard_blacklist = ["Papyrus", "Comic Sans", "Lobster", "Impact", "Jokerman",
                      "Bleeding Cowboys", "Permanent Marker", "Bradley Hand",
                      "Brush Script", "Hobo", "Trajan", "Raleway"]
    hard_violations = [f for f in hard_blacklist if f.lower() in design_content.lower()]
    no_hard_violations = len(hard_violations) == 0
    total_score += add_check(
        "Font hard blacklist: none of the banned fonts appear",
        no_hard_violations,
        f"No hard-blacklisted fonts found" if no_hard_violations
        else f"VIOLATION: hard-blacklisted font(s) found: {hard_violations}",
        weight=0.6
    )

    # ── AI JUNK ANTI-PATTERNS: No purple/violet gradient default accent ───────
    purple_gradient = bool(re.search(
        r"(purple|violet|#[89abcde][0-9a-f]{5})\b.*gradient|gradient.*\b(purple|violet)",
        design_content, re.IGNORECASE
    ))
    # More targeted: primary/accent color is purple-ish
    accent_section = re.search(r"(主色|次色|强调|Primary|Accent).{0,80}#([0-9A-Fa-f]{6})", design_content)
    if accent_section:
        hex_val = accent_section.group(2)
        r_val = int(hex_val[0:2], 16)
        g_val = int(hex_val[2:4], 16)
        b_val = int(hex_val[4:6], 16)
        # Purple heuristic: high blue+red, low green
        is_purple_accent = (r_val > 100 and b_val > 100 and g_val < 100 and abs(r_val - b_val) < 80)
    else:
        is_purple_accent = False

    no_purple_default = not is_purple_accent
    total_score += add_check(
        "Anti-pattern: Primary/accent color is NOT default purple/violet",
        no_purple_default,
        f"Accent color is not default purple/violet" if no_purple_default
        else f"AI junk detected: purple/violet default accent color used",
        weight=0.5
    )

    # ── CLAUDE.md: Design section appended ───────────────────────────────────
    claude_path = ws / "CLAUDE.md"
    try:
        claude_content = claude_path.read_text(encoding="utf-8")

        has_design_section = bool(re.search(r"##\s*设计系统", claude_content))
        total_score += add_check(
            "CLAUDE.md: ## 设计系统 section appended",
            has_design_section,
            "Section '## 设计系统' found in CLAUDE.md" if has_design_section
            else "MISSING: '## 设计系统' section not appended to CLAUDE.md",
            weight=0.8
        )

        # Must contain the key instruction about reading DESIGN.md
        has_read_instruction = bool(re.search(
            r"(read|读取|参阅)\s*DESIGN\.md",
            claude_content, re.IGNORECASE
        ))
        total_score += add_check(
            "CLAUDE.md: Design section instructs to read DESIGN.md",
            has_read_instruction,
            "Instruction to read DESIGN.md found in CLAUDE.md" if has_read_instruction
            else "MISSING: instruction to consult DESIGN.md before UI decisions",
            weight=0.4
        )

        # Original CLAUDE.md content preserved (check first section still there)
        original_preserved = "TypeScript strict mode" in claude_content
        total_score += add_check(
            "CLAUDE.md: Original content preserved (not overwritten)",
            original_preserved,
            "Original CLAUDE.md content intact" if original_preserved
            else "CRITICAL: CLAUDE.md appears to have been overwritten, not appended",
            weight=0.6
        )

    except Exception as e:
        total_score += add_check("CLAUDE.md: readable", False, f"Could not read CLAUDE.md: {e}", weight=1.8)

    # ── DESIGN.md: Product context correctly identifies the product ───────────
    product_context = bool(re.search(
        r"(RiskLens|risk.{0,15}analytics|portfolio.{0,15}risk|institutional|hedge.{0,10}fund|asset.{0,10}manag)",
        design_content, re.IGNORECASE
    ))
    total_score += add_check(
        "DESIGN.md: Product context reflects actual codebase (RiskLens/fintech)",
        product_context,
        "Product context correctly identifies fintech/risk analytics context" if product_context
        else "Product context doesn't reflect the actual codebase content",
        weight=0.4
    )

    # ── Compute final score ───────────────────────────────────────────────────
    max_score = sum([
        0.5,   # DESIGN.md exists
        0.3 * 8,  # 8 sections
        0.4,   # 装饰等级
        0.3,   # 氛围
        0.3,   # decision log table
        0.4,   # hex colors
        0.3,   # semantic colors
        0.3,   # spacing unit
        0.3,   # font rationale
        0.4,   # SAFE/RISK
        0.8,   # font overuse blacklist
        0.6,   # font hard blacklist
        0.5,   # no purple default
        0.8,   # CLAUDE.md design section
        0.4,   # CLAUDE.md read instruction
        0.6,   # CLAUDE.md original preserved
        0.4,   # product context
    ])

    normalized_score = min(1.0, total_score / max_score)
    passed = normalized_score >= 0.70 and \
             any(c["passed"] for c in checks if c["name"] == "DESIGN.md exists") and \
             any(c["passed"] for c in checks if "CLAUDE.md: ## 设计系统" in c["name"]) and \
             any(c["passed"] for c in checks if "CLAUDE.md: Original content preserved" in c["name"])

    return {
        "passed": passed,
        "score": round(normalized_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))