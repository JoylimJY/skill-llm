#!/usr/bin/env python3
"""Evaluation script for luxury travel plan task."""
import sys
import json
import re
from pathlib import Path

def find_plan_file(workspace: Path) -> Path | None:
    """Find the luxury plan file by exact name."""
    matches = list(workspace.rglob("nz_luxury_plan_li_jun.md"))
    if matches:
        return matches[0]
    return None

def parse_cny(text: str) -> float | None:
    """Extract a CNY value from text like ¥1,234,567 or ¥1234567."""
    patterns = [
        r'¥\s*([\d,]+(?:\.\d+)?)',
        r'（CNY）\s*([\d,]+)',
        r'CNY\s*([\d,]+)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return float(m.group(1).replace(',', ''))
    return None

def check_section_present(content: str, pattern: str) -> bool:
    return bool(re.search(pattern, content, re.IGNORECASE | re.UNICODE))

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── Find the file ─────────────────────────────────────────────────────────
    plan_file = find_plan_file(workspace)
    
    checks.append({
        "name": "file_exists: nz_luxury_plan_li_jun.md",
        "passed": plan_file is not None,
        "detail": f"Found at: {plan_file}" if plan_file else "File 'nz_luxury_plan_li_jun.md' not found anywhere in workspace"
    })
    
    if plan_file is None:
        score = 0.0
        result = {"passed": False, "score": score, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    try:
        content = plan_file.read_text(encoding='utf-8')
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}, ensure_ascii=False))
        return

    # ── CHECK 1: Title / Destination header ──────────────────────────────────
    has_title = check_section_present(content, r'#\s*💎.*奢华游定制方案')
    checks.append({
        "name": "template_title_emoji_header",
        "passed": has_title,
        "detail": "Must start with '# 💎 奢华游定制方案' per SKILL.md output template" if not has_title else "Title header found with 💎 emoji"
    })

    # ── CHECK 2: 行程概览 section with required fields ────────────────────────
    has_overview = check_section_present(content, r'##\s*✨\s*行程概览')
    checks.append({
        "name": "section_trip_overview_with_emoji",
        "passed": has_overview,
        "detail": "Missing '## ✨ 行程概览' section (must have ✨ emoji per template)" if not has_overview else "Found '## ✨ 行程概览'"
    })

    # Check overview contains required fields
    overview_fields = ['目的地', '旅行日期', '旅行天数', '旅行人数', '体验主题']
    overview_check = all(f in content for f in overview_fields)
    checks.append({
        "name": "overview_required_fields",
        "passed": overview_check,
        "detail": f"Overview must include: {', '.join(overview_fields)}" if not overview_check else "All overview fields present"
    })

    # ── CHECK 3: 交通方案 section ─────────────────────────────────────────────
    has_transport = check_section_present(content, r'##\s*🛩️\s*交通方案')
    checks.append({
        "name": "section_transport_with_emoji",
        "passed": has_transport,
        "detail": "Missing '## 🛩️ 交通方案' section with correct emoji" if not has_transport else "Found transport section"
    })

    # Client brief specifies Shanghai PVG - must mention PVG or 上海浦东
    has_pvg = bool(re.search(r'PVG|上海浦东|浦东机场', content))
    checks.append({
        "name": "transport_pvg_origin",
        "passed": has_pvg,
        "detail": "Must specify departure from Shanghai Pudong (PVG) as per client brief" if not has_pvg else "PVG/上海浦东 mentioned"
    })

    # Flight must use premium class - Singapore Airlines or Emirates or Cathay (from flyai results)
    # SKILL.md priority: private jet > first class > business
    has_premium_airline = bool(re.search(
        r'(新加坡航空|Singapore Airlines|SQ\d+|阿联酋航空|Emirates|EK\d+|国泰航空|Cathay|CX\d+|头等舱|First Class|商务舱|Business Class)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "transport_premium_class_airline",
        "passed": has_premium_airline,
        "detail": "Must recommend premium airline (Singapore Airlines, Emirates, Cathay) with business/first class per SKILL.md strategy" if not has_premium_airline else "Premium airline/class found"
    })

    # ── CHECK 4: 住宿方案 section ─────────────────────────────────────────────
    has_hotel_section = check_section_present(content, r'##\s*🏨\s*住宿方案')
    checks.append({
        "name": "section_accommodation_with_emoji",
        "passed": has_hotel_section,
        "detail": "Missing '## 🏨 住宿方案' section with 🏨 emoji" if not has_hotel_section else "Found accommodation section"
    })

    # Must mention a luxury hotel/lodge in NZ (from flyai results: Matakauri, Eagles Nest, Rees, Blanket Bay)
    has_luxury_nz_hotel = bool(re.search(
        r'(Matakauri|Eagles Nest|The Rees|Blanket Bay|Rees Hotel|matakauri|blanket bay)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "accommodation_luxury_nz_brand",
        "passed": has_luxury_nz_hotel,
        "detail": "Must include a recognized luxury NZ lodge/hotel (e.g., Matakauri, Blanket Bay, The Rees) from search results" if not has_luxury_nz_hotel else "Luxury NZ hotel found"
    })

    # ── CHECK 5: 独家体验 section ─────────────────────────────────────────────
    has_experience = check_section_present(content, r'##\s*🎯\s*独家体验')
    checks.append({
        "name": "section_exclusive_experience_with_emoji",
        "passed": has_experience,
        "detail": "Missing '## 🎯 独家体验' section with 🎯 emoji" if not has_experience else "Found exclusive experience section"
    })

    # Must include helicopter glacier experience (client must-have #1)
    has_helicopter = bool(re.search(
        r'(直升机|helicopter|Helicopter Line|Over The Top|冰川|glacier|Fox|Franz Josef)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "experience_helicopter_glacier",
        "passed": has_helicopter,
        "detail": "Client explicitly requested helicopter glacier experience (Fox Glacier/Franz Josef) - must be included" if not has_helicopter else "Helicopter glacier experience found"
    })

    # Must include yacht/boat experience (client must-have #3)
    has_yacht = bool(re.search(
        r'(游艇|yacht|Yacht|峡湾|fiord|Fiordland|Milford|milford|Doubtful|doubtful|Navigator|包船)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "experience_yacht_fiord",
        "passed": has_yacht,
        "detail": "Client requested Milford/Doubtful Sound boat charter - must be included" if not has_yacht else "Yacht/fiord boat experience found"
    })

    # Must include wine/vineyard experience (client must-have #2)
    has_wine = bool(re.search(
        r'(酒庄|vineyard|Vineyard|wine|Wine|品鉴|Cloudy Bay|Rippon|Marlborough|marlborough|Central Otago|奥塔哥)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "experience_wine_vineyard",
        "passed": has_wine,
        "detail": "Client requested private wine tasting in Marlborough/Central Otago - must be included" if not has_wine else "Wine/vineyard experience found"
    })

    # Must include supercar (client must-have #4)
    has_supercar = bool(re.search(
        r'(超跑|supercar|法拉利|Ferrari|兰博基尼|Lamborghini|保时捷|Porsche|豪车自驾|超级跑车)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "experience_supercar",
        "passed": has_supercar,
        "detail": "Client requested supercar self-drive on South Island - must be included" if not has_supercar else "Supercar experience found"
    })

    # ── CHECK 6: 餐饮体验 section ─────────────────────────────────────────────
    has_dining = check_section_present(content, r'##\s*🍽️\s*餐饮体验')
    checks.append({
        "name": "section_dining_with_emoji",
        "passed": has_dining,
        "detail": "Missing '## 🍽️ 餐饮体验' section with 🍽️ emoji" if not has_dining else "Found dining section"
    })

    # Must include at least one Michelin or top-tier restaurant
    has_michelin = bool(re.search(
        r'(米其林|Michelin|michelin|Amisfield|Pasture|Botswana Butchery|⭐)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "dining_michelin_or_equivalent",
        "passed": has_michelin,
        "detail": "Must include at least one Michelin-star or equivalent fine dining restaurant per SKILL.md quality standards" if not has_michelin else "Michelin/top-tier restaurant found"
    })

    # ── CHECK 7: 预算汇总 section with table ─────────────────────────────────
    has_budget = check_section_present(content, r'##\s*💰\s*预算汇总')
    checks.append({
        "name": "section_budget_summary_with_emoji",
        "passed": has_budget,
        "detail": "Missing '## 💰 预算汇总' section with 💰 emoji" if not has_budget else "Found budget section"
    })

    # Budget table must have required columns: 项目 | 预算 | 备注
    has_budget_table = bool(re.search(r'\|.*项目.*\|.*预算.*\|', content))
    checks.append({
        "name": "budget_table_format",
        "passed": has_budget_table,
        "detail": "Budget table must use markdown pipe format with columns '项目 | 预算 (CNY) | 备注' per SKILL.md template" if not has_budget_table else "Budget table found"
    })

    # Must have 总计 and 人均预算
    has_total = bool(re.search(r'总计|Total', content, re.IGNORECASE))
    has_per_person = bool(re.search(r'人均', content))
    checks.append({
        "name": "budget_has_total_and_per_person",
        "passed": has_total and has_per_person,
        "detail": f"Budget must include 总计 (total): {has_total}, and 人均预算 (per person): {has_per_person}" if not (has_total and has_per_person) else "总计 and 人均预算 both present"
    })

    # Per-person should = total / 2 (2 travelers) - check approximate consistency
    # Extract all ¥ values from budget table area
    budget_section_match = re.search(r'##\s*💰\s*预算汇总(.*?)(?=##|\Z)', content, re.DOTALL)
    budget_consistent = False
    budget_detail = "Could not extract budget section for verification"
    if budget_section_match:
        budget_text = budget_section_match.group(1)
        # Find 总计 line
        total_match = re.search(r'\*\*总计\*\*[^\|]*\|[^\|]*\*\*¥([\d,]+(?:\.\d+)?)\*\*', budget_text)
        perperson_match = re.search(r'人均[^¥\n]*¥\s*([\d,]+(?:\.\d+)?)', budget_text)
        if not total_match:
            total_match = re.search(r'总计[^\|]*\|\s*¥?([\d,]+(?:\.\d+)?)', budget_text)
        if total_match and perperson_match:
            try:
                total_val = float(total_match.group(1).replace(',', ''))
                pp_val = float(perperson_match.group(1).replace(',', ''))
                expected_pp = total_val / 2
                # Allow 10% tolerance
                ratio = abs(pp_val - expected_pp) / expected_pp if expected_pp > 0 else 1
                budget_consistent = ratio < 0.15
                budget_detail = f"总计=¥{total_val:,.0f}, 人均=¥{pp_val:,.0f}, 期望人均=¥{expected_pp:,.0f} (ratio_err={ratio:.2%})"
            except Exception as ex:
                budget_detail = f"Parse error: {ex}"
        else:
            budget_detail = f"Could not parse 总计 or 人均 values from budget table. total_match={bool(total_match)}, pp_match={bool(perperson_match)}"
    
    checks.append({
        "name": "budget_per_person_equals_total_div_2",
        "passed": budget_consistent,
        "detail": budget_detail
    })

    # ── CHECK 8: 增值服务 section ─────────────────────────────────────────────
    has_value_added = check_section_present(content, r'##\s*🎁\s*增值服务')
    checks.append({
        "name": "section_value_added_services",
        "passed": has_value_added,
        "detail": "Missing '## 🎁 增值服务' section - required by SKILL.md template" if not has_value_added else "Found 增值服务 section"
    })

    # Must mention 24小时中文管家服务 (required field in template)
    has_butler = bool(re.search(r'24小时中文管家', content))
    checks.append({
        "name": "value_added_chinese_butler_service",
        "passed": has_butler,
        "detail": "'24小时中文管家服务' must appear in 增值服务 section per SKILL.md template" if not has_butler else "24小时中文管家服务 found"
    })

    # ── CHECK 9: 行前准备 section ─────────────────────────────────────────────
    has_prep = check_section_present(content, r'##\s*📋\s*行前准备')
    checks.append({
        "name": "section_pre_trip_checklist",
        "passed": has_prep,
        "detail": "Missing '## 📋 行前准备' section with 📋 emoji" if not has_prep else "Found 行前准备 section"
    })

    # Must have checklist items (markdown checkboxes)
    has_checklist = bool(re.search(r'- \[ \]', content))
    checks.append({
        "name": "pre_trip_markdown_checklist",
        "passed": has_checklist,
        "detail": "行前准备 must contain markdown checkbox items '- [ ]' per SKILL.md template" if not has_checklist else "Markdown checklist items found"
    })

    # ── CHECK 10: Footer signature ────────────────────────────────────────────
    has_footer = bool(re.search(r'Curated by Luxury Travel Concierge', content))
    checks.append({
        "name": "footer_concierge_signature",
        "passed": has_footer,
        "detail": "Must end with '*Curated by Luxury Travel Concierge*' per SKILL.md template" if not has_footer else "Footer signature found"
    })

    # Must include 方案定制时间
    has_timestamp = bool(re.search(r'方案定制时间', content))
    checks.append({
        "name": "footer_plan_timestamp",
        "passed": has_timestamp,
        "detail": "Must include '方案定制时间' in footer per SKILL.md template" if not has_timestamp else "方案定制时间 found"
    })

    # ── CHECK 11: Link accuracy (no mismatched links) ─────────────────────────
    # SKILL.md warns: must not use mismatched links; missing links should be marked "需单独预订"
    # Check: any booking link present should at least be a real URL (not placeholder xxx)
    bad_links = re.findall(r'\[(?:预订链接|booking)\]\(https?://[^\)]*?xxx[^\)]*\)', content, re.IGNORECASE)
    has_no_bad_placeholder_links = len(bad_links) == 0
    checks.append({
        "name": "link_accuracy_no_placeholder_xxx_links",
        "passed": has_no_bad_placeholder_links,
        "detail": f"Found {len(bad_links)} placeholder links with 'xxx' - per SKILL.md link accuracy rules these must be removed or marked '需单独预订'" if not has_no_bad_placeholder_links else "No placeholder xxx links found"
    })

    # ── CHECK 12: NZ-specific destination correctness ─────────────────────────
    has_nz_locations = bool(re.search(
        r'(皇后镇|Queenstown|米尔福德|Milford|南岛|South Island|瓦纳卡|Wanaka|蒂卡波|Tekapo|奥克兰|Auckland|马尔伯勒|Marlborough)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "content_nz_specific_locations",
        "passed": has_nz_locations,
        "detail": "Plan must reference specific New Zealand South Island locations (Queenstown, Milford Sound, etc.)" if not has_nz_locations else "NZ-specific locations mentioned"
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 4)

    # Overall pass: need at least 80% checks AND critical checks must pass
    critical_checks = [
        "file_exists: nz_luxury_plan_li_jun.md",
        "template_title_emoji_header",
        "section_trip_overview_with_emoji",
        "section_transport_with_emoji",
        "section_accommodation_with_emoji",
        "section_exclusive_experience_with_emoji",
        "section_budget_summary_with_emoji",
        "experience_helicopter_glacier",
        "experience_yacht_fiord",
        "experience_supercar",
        "budget_has_total_and_per_person",
    ]
    critical_passed = all(
        any(c["name"] == cc and c["passed"] for c in checks)
        for cc in critical_checks
    )
    overall_passed = score >= 0.80 and critical_passed

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    run_eval(sys.argv[1])