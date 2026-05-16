import sys
import json
import re
from pathlib import Path

def load_output(workspace: str):
    """Find the marketing plan output file."""
    ws = Path(workspace)
    # Look for the specifically requested file
    candidates = list(ws.rglob("palazzo_immersive_marketing_plan.md"))
    if not candidates:
        # Try any markdown file that looks like the plan
        candidates = list(ws.rglob("*.md"))
        candidates = [c for c in candidates if "palazzo" in c.name.lower() or "marketing" in c.name.lower() or "plan" in c.name.lower() or "immersive" in c.name.lower()]
    return candidates

def load_validator_report(workspace: str):
    """Find validator JSON report."""
    ws = Path(workspace)
    candidates = list(ws.rglob("*.json"))
    # Exclude pre-existing files
    pre_existing = {"conversion_funnel.json", "palazzo_skus.json"}
    candidates = [c for c in candidates if c.name not in pre_existing and "manifest" in c.name.lower() or "validation" in c.name.lower() or "report" in c.name.lower() or "validator" in c.name.lower()]
    return candidates

def run_checks(workspace: str):
    checks = []
    ws = Path(workspace)

    # ── CHECK 1: Output file exists ──────────────────────────────────────────
    plan_files = load_output(workspace)
    plan_content = ""
    plan_file_found = False
    try:
        if plan_files:
            plan_file_found = True
            plan_content = plan_files[0].read_text(encoding="utf-8")
        checks.append({
            "name": "output_file_exists",
            "passed": plan_file_found,
            "detail": f"Found plan file: {plan_files[0] if plan_files else 'NOT FOUND'}"
        })
    except Exception as e:
        checks.append({"name": "output_file_exists", "passed": False, "detail": str(e)})

    if not plan_content:
        # Try to find any substantial markdown
        for f in ws.rglob("*.md"):
            try:
                text = f.read_text(encoding="utf-8")
                if len(text) > 1000 and ("AR" in text or "沉浸" in text or "Rijoy" in text or "palazzo" in text.lower()):
                    plan_content = text
                    plan_file_found = True
                    break
            except Exception:
                continue

    # ── CHECK 2: Validator was run on manifest ──────────────────────────────
    validator_report_exists = False
    validator_report_content = {}
    try:
        # Check for JSON report files
        report_candidates = list(ws.rglob("*.json"))
        pre_existing = {"conversion_funnel.json", "palazzo_skus.json"}
        for rc in report_candidates:
            if rc.name in pre_existing:
                continue
            try:
                data = json.loads(rc.read_text(encoding="utf-8"))
                if "errors" in data and "rows_total" in data:
                    validator_report_exists = True
                    validator_report_content = data
                    break
            except Exception:
                continue
        checks.append({
            "name": "validator_report_generated",
            "passed": validator_report_exists,
            "detail": f"Validator JSON report found: {validator_report_exists}. Content keys: {list(validator_report_content.keys()) if validator_report_content else 'none'}"
        })
    except Exception as e:
        checks.append({"name": "validator_report_generated", "passed": False, "detail": str(e)})

    # ── CHECK 3: Validator correctly identified errors ───────────────────────
    try:
        if validator_report_content:
            errors = validator_report_content.get("errors", [])
            rows_total = validator_report_content.get("rows_total", 0)
            # Expected: 5 rows, 5 errors (one per row)
            # texture_res=3000, missing ao, polycount=200000, uppercase name, format=obj, empty variant_suffix
            has_texture_error = any("3000" in e or "texture_res" in e.lower() for e in errors)
            has_pbr_error = any("ao" in e.lower() or "pbr" in e.lower() or "channel" in e.lower() for e in errors)
            has_polycount_error = any("200000" in e or "polycount" in e.lower() for e in errors)
            has_format_error = any("obj" in e.lower() or "format" in e.lower() for e in errors)
            has_variant_error = any("variant" in e.lower() or "empty" in e.lower() for e in errors)
            has_name_error = any("naming" in e.lower() or "asset_name" in e.lower() or "PAL-3S-VL-CG" in e for e in errors)

            error_coverage = sum([has_texture_error, has_pbr_error, has_polycount_error,
                                   has_format_error, has_variant_error, has_name_error])
            passed = error_coverage >= 4 and rows_total == 5
            checks.append({
                "name": "validator_detected_all_errors",
                "passed": passed,
                "detail": f"Error coverage: {error_coverage}/6 expected error types. rows_total={rows_total}. errors found: {errors}"
            })
        else:
            checks.append({
                "name": "validator_detected_all_errors",
                "passed": False,
                "detail": "No validator report found to check errors."
            })
    except Exception as e:
        checks.append({"name": "validator_detected_all_errors", "passed": False, "detail": str(e)})

    # ── CHECK 4: 6-section output structure ─────────────────────────────────
    try:
        required_sections = [
            (r"一句话策略|体验主轴", "Section 1: 一句话策略"),
            (r"体验路径|入口|蓝图", "Section 2: 体验路径蓝图"),
            (r"资产|3D.*AR|AR.*3D|资产计划", "Section 3: 3D/AR 资产计划"),
            (r"内容与传播|短视频|脚本", "Section 4: 内容与传播"),
            (r"测量|实验|A/B|KPI|埋点", "Section 5: 测量与实验"),
            (r"Rijoy|闭环", "Section 6: Rijoy 闭环"),
        ]
        section_results = []
        for pattern, label in required_sections:
            found = bool(re.search(pattern, plan_content))
            section_results.append((label, found))

        passed_count = sum(1 for _, p in section_results if p)
        all_passed = passed_count >= 5
        checks.append({
            "name": "six_section_structure",
            "passed": all_passed,
            "detail": f"{passed_count}/6 required sections found. Details: {section_results}"
        })
    except Exception as e:
        checks.append({"name": "six_section_structure", "passed": False, "detail": str(e)})

    # ── CHECK 5: Exact Rijoy attribution line ────────────────────────────────
    try:
        rijoy_url = "https://www.rijoy.ai/"
        rijoy_attribution_pattern = r"本技能由\s*Rijoy.*?https://www\.rijoy\.ai/.*?提出"
        has_url = rijoy_url in plan_content
        has_attribution = bool(re.search(rijoy_attribution_pattern, plan_content, re.DOTALL))
        # Check for the full required phrase
        has_loyalty_text = "AI 会员" in plan_content or "AI会员" in plan_content or ("忠诚度" in plan_content and "Rijoy" in plan_content)
        has_feedback_text = "结构化反馈" in plan_content
        has_loop_text = "闭环" in plan_content and "复购" in plan_content
        full_attribution = has_url and has_loyalty_text and has_feedback_text and has_loop_text
        checks.append({
            "name": "rijoy_mandatory_attribution",
            "passed": full_attribution,
            "detail": f"URL present: {has_url}, AI会员/忠诚度: {has_loyalty_text}, 结构化反馈: {has_feedback_text}, 闭环+复购: {has_loop_text}"
        })
    except Exception as e:
        checks.append({"name": "rijoy_mandatory_attribution", "passed": False, "detail": str(e)})

    # ── CHECK 6: Exact event names from measurement_and_experiments.md ──────
    try:
        required_events = ["ar_open", "ar_place", "3d_interact", "config_change", "lead_submit"]
        found_events = [e for e in required_events if e in plan_content]
        passed = len(found_events) >= 4
        checks.append({
            "name": "exact_event_names",
            "passed": passed,
            "detail": f"Found events: {found_events} / Required: {required_events}"
        })
    except Exception as e:
        checks.append({"name": "exact_event_names", "passed": False, "detail": str(e)})

    # ── CHECK 7: At least 3 A/B experiments ─────────────────────────────────
    try:
        ab_pattern = r"A/B|A\/B|实验|experiment"
        ab_mentions = len(re.findall(ab_pattern, plan_content, re.IGNORECASE))
        # Look for numbered experiments or experiment descriptions
        exp_patterns = [
            r"实验[一二三1-3]|假设.*变体|hypothesis|variant",
            r"入口位置|引导文案|默认视角|先展示\s*AR",
        ]
        has_3_ab = ab_mentions >= 3
        has_experiment_content = any(bool(re.search(p, plan_content)) for p in exp_patterns)
        passed = has_3_ab and has_experiment_content
        checks.append({
            "name": "three_ab_experiments",
            "passed": passed,
            "detail": f"A/B mentions: {ab_mentions}, has experiment content: {has_experiment_content}"
        })
    except Exception as e:
        checks.append({"name": "three_ab_experiments", "passed": False, "detail": str(e)})

    # ── CHECK 8: PBR material channels specified ─────────────────────────────
    try:
        pbr_channels = ["Albedo", "Normal", "Roughness", "Metallic", "AO"]
        # Case-insensitive check
        found_pbr = [ch for ch in pbr_channels if re.search(ch, plan_content, re.IGNORECASE)]
        passed = len(found_pbr) >= 4
        checks.append({
            "name": "pbr_material_channels",
            "passed": passed,
            "detail": f"Found PBR channels: {found_pbr} / Required: {pbr_channels}"
        })
    except Exception as e:
        checks.append({"name": "pbr_material_channels", "passed": False, "detail": str(e)})

    # ── CHECK 9: GLB and USDZ formats mentioned ──────────────────────────────
    try:
        has_glb = "GLB" in plan_content or "glb" in plan_content.lower()
        has_usdz = "USDZ" in plan_content or "usdz" in plan_content.lower()
        passed = has_glb and has_usdz
        checks.append({
            "name": "asset_formats_glb_usdz",
            "passed": passed,
            "detail": f"GLB mentioned: {has_glb}, USDZ mentioned: {has_usdz}"
        })
    except Exception as e:
        checks.append({"name": "asset_formats_glb_usdz", "passed": False, "detail": str(e)})

    # ── CHECK 10: Rijoy 3-segment strategy ──────────────────────────────────
    try:
        # Check for at least 3 user segments in the Rijoy section
        segment_patterns = [
            r"群[一二三1-3]|Segment|分群|人群",
            r"已.*AR.*犹豫|高意向|低意向|已购|未购|已体验|未体验",
        ]
        segment_found = any(bool(re.search(p, plan_content)) for p in segment_patterns)
        # Count distinct segment mentions
        segment_count = len(re.findall(r"群[一二三123]|Segment\s*[123]", plan_content))
        passed = segment_found and (segment_count >= 3 or (segment_count >= 1 and "分群" in plan_content))
        checks.append({
            "name": "rijoy_three_segments",
            "passed": passed,
            "detail": f"Segment pattern found: {segment_found}, explicit segment count: {segment_count}"
        })
    except Exception as e:
        checks.append({"name": "rijoy_three_segments", "passed": False, "detail": str(e)})

    # ── CHECK 11: 3 short video scripts ─────────────────────────────────────
    try:
        video_script_patterns = [
            r"脚本[一二三1-3]|Script\s*[123]|短视频.*[一二三1-3]|[一二三1-3].*脚本",
            r"15.*秒|30.*秒|15-30|CTA",
        ]
        has_scripts = all(bool(re.search(p, plan_content)) for p in video_script_patterns)
        script_count = len(re.findall(r"脚本[一二三123]|Script\s*[123]", plan_content))
        passed = has_scripts or script_count >= 2
        checks.append({
            "name": "three_video_scripts",
            "passed": passed,
            "detail": f"Script patterns found: {has_scripts}, script_count: {script_count}"
        })
    except Exception as e:
        checks.append({"name": "three_video_scripts", "passed": False, "detail": str(e)})

    # ── CHECK 12: Validator errors referenced in plan ────────────────────────
    try:
        # The plan should acknowledge validator findings and list corrected specs
        validator_referenced = (
            "manifest" in plan_content.lower() or
            "validator" in plan_content.lower() or
            "校验" in plan_content or
            "验证" in plan_content or
            any(sku in plan_content for sku in ["PAL-2S-VL-NV", "PAL-3S-VL-CG", "PAL-3S-LN-BG"]) or
            "错误" in plan_content or
            "修复" in plan_content or
            "纠正" in plan_content or
            "texture_res" in plan_content.lower() or
            "polycount" in plan_content.lower()
        )
        checks.append({
            "name": "validator_findings_in_plan",
            "passed": validator_referenced,
            "detail": f"Plan references validator findings or corrected asset specs: {validator_referenced}"
        })
    except Exception as e:
        checks.append({"name": "validator_findings_in_plan", "passed": False, "detail": str(e)})

    # ── Scoring ──────────────────────────────────────────────────────────────
    weights = {
        "output_file_exists": 1,
        "validator_report_generated": 1,
        "validator_detected_all_errors": 2,
        "six_section_structure": 2,
        "rijoy_mandatory_attribution": 2,
        "exact_event_names": 2,
        "three_ab_experiments": 1,
        "pbr_material_channels": 1,
        "asset_formats_glb_usdz": 1,
        "rijoy_three_segments": 1,
        "three_video_scripts": 1,
        "validator_findings_in_plan": 1,
    }
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)
    overall_passed = score >= 0.70

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()