import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]
responses_dir = Path(workspace) / "inquiries" / "responses"

checks = []
total_score = 0.0

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

def read_response(inquiry_id):
    """Try to find response file for a given inquiry ID."""
    patterns = [
        responses_dir / f"response_{inquiry_id.lower().replace('-', '_')}.txt",
        responses_dir / f"response_{inquiry_id}.txt",
        responses_dir / f"response_{inquiry_id.upper()}.txt",
        responses_dir / f"response-{inquiry_id.lower()}.txt",
    ]
    # Also try rglob for any file containing the inquiry number
    inq_num = inquiry_id.split("-")[-1]  # e.g., "001", "002"
    for p in patterns:
        if p.exists():
            return p.read_text(encoding="utf-8")
    # Broader search
    for f in responses_dir.rglob(f"*{inq_num}*"):
        if f.suffix in [".txt", ".md", ""]:
            return f.read_text(encoding="utf-8")
    return None

# ─────────────────────────────────────────────────────────────
# INQ-001: 0 params → convergence 0% → probe all 4 mandatory
# ─────────────────────────────────────────────────────────────
try:
    content = read_response("INQ-001")
    if content is None:
        check("INQ-001 file exists", False, "Response file for INQ-001 not found")
        check("INQ-001 convergence 0%", False, "File missing")
        check("INQ-001 probe format header", False, "File missing")
        check("INQ-001 lists all 4 mandatory params", False, "File missing")
        check("INQ-001 no auto-route", False, "File missing")
    else:
        check("INQ-001 file exists", True, f"Found response content ({len(content)} chars)")

        # Convergence 0%
        has_convergence_0 = bool(re.search(r'收敛度[：:]\s*0%', content))
        check("INQ-001 convergence 0%", has_convergence_0,
              f"Expected '收敛度：0%' in output. Got: {content[:300]}")

        # Probe format header
        has_header = "📋" in content and "参数收集" in content
        check("INQ-001 probe format header (📋 参数收集)", has_header,
              f"Must contain '📋' and '参数收集'. Content snippet: {content[:200]}")

        # Lists all 4 mandatory params with 🔴
        mandatory_params = ["材料", "数量", "精度", "表面处理"]
        all_listed = all(
            ("🔴" in content and param in content) or
            (re.search(rf'🔴.*【{param}】', content) is not None or
             (param in content and "🔴" in content))
            for param in mandatory_params
        )
        missing_params = [p for p in mandatory_params if p not in content]
        check("INQ-001 lists all 4 mandatory params with 🔴",
              len(missing_params) == 0 and "🔴" in content,
              f"Missing params: {missing_params}. Has 🔴: {'🔴' in content}")

        # No auto-route declaration
        has_route = bool(re.search(r'cnc-quote-system|自动路由|auto.?route', content, re.IGNORECASE))
        check("INQ-001 no auto-route (convergence < 80%)", not has_route,
              f"Should NOT auto-route at 0%. Found route reference: {has_route}")

except Exception as e:
    check("INQ-001 processing error", False, str(e))

# ─────────────────────────────────────────────────────────────
# INQ-002: 2 mandatory (材料, 数量) → convergence 50% → probe 精度, 表面处理
# ─────────────────────────────────────────────────────────────
try:
    content = read_response("INQ-002")
    if content is None:
        check("INQ-002 file exists", False, "Response file for INQ-002 not found")
        check("INQ-002 convergence 50%", False, "File missing")
        check("INQ-002 probes only missing params", False, "File missing")
        check("INQ-002 does not re-ask provided params", False, "File missing")
    else:
        check("INQ-002 file exists", True, f"Found ({len(content)} chars)")

        has_convergence_50 = bool(re.search(r'收敛度[：:]\s*50%', content))
        check("INQ-002 convergence 50%", has_convergence_50,
              f"Expected '收敛度：50%'. Snippet: {content[:300]}")

        # Must ask for 精度 and 表面处理
        asks_jingdu = "精度" in content
        asks_biaomian = "表面处理" in content
        check("INQ-002 probes missing params (精度 and 表面处理)",
              asks_jingdu and asks_biaomian,
              f"精度 in content: {asks_jingdu}, 表面处理 in content: {asks_biaomian}")

        # Should NOT re-ask 材料 and 数量 with 🔴 prompt (they were provided)
        # It's acceptable to mention them as confirmed, but should not ask for them
        # Check: no "🔴【材料】" or "🔴【数量】"
        re_asks_material = bool(re.search(r'🔴.*【材料】', content))
        re_asks_quantity = bool(re.search(r'🔴.*【数量】', content))
        check("INQ-002 does not re-prompt provided params (材料/数量) with 🔴",
              not re_asks_material and not re_asks_quantity,
              f"Re-asks 材料: {re_asks_material}, Re-asks 数量: {re_asks_quantity}")

        # No auto-route
        has_route = bool(re.search(r'cnc-quote-system|自动路由', content))
        check("INQ-002 no auto-route (50% < 80%)", not has_route,
              f"Should not auto-route at 50%")

except Exception as e:
    check("INQ-002 processing error", False, str(e))

# ─────────────────────────────────────────────────────────────
# INQ-003: 3 mandatory (材料, 数量, 精度) → convergence 75% → probe 表面处理
# ─────────────────────────────────────────────────────────────
try:
    content = read_response("INQ-003")
    if content is None:
        check("INQ-003 file exists", False, "Response file for INQ-003 not found")
        check("INQ-003 convergence 75%", False, "File missing")
        check("INQ-003 probes only 表面处理", False, "File missing")
    else:
        check("INQ-003 file exists", True, f"Found ({len(content)} chars)")

        has_convergence_75 = bool(re.search(r'收敛度[：:]\s*75%', content))
        check("INQ-003 convergence 75%", has_convergence_75,
              f"Expected '收敛度：75%'. Snippet: {content[:300]}")

        # Must ask for 表面处理
        asks_surface = "表面处理" in content
        check("INQ-003 probes missing param (表面处理)", asks_surface,
              f"表面处理 in content: {asks_surface}")

        # No auto-route
        has_route = bool(re.search(r'cnc-quote-system|自动路由', content))
        check("INQ-003 no auto-route (75% < 80%)", not has_route,
              f"Should not auto-route at 75%")

        # Should not re-ask already provided params with 🔴
        re_asks = any(
            bool(re.search(rf'🔴.*【{p}】', content))
            for p in ["材料", "数量", "精度"]
        )
        check("INQ-003 does not re-prompt provided params",
              not re_asks,
              f"Re-prompts provided params with 🔴: {re_asks}")

except Exception as e:
    check("INQ-003 processing error", False, str(e))

# ─────────────────────────────────────────────────────────────
# INQ-004: all 4 mandatory → convergence 100% → auto-route to cnc-quote-system
# ─────────────────────────────────────────────────────────────
try:
    content = read_response("INQ-004")
    if content is None:
        check("INQ-004 file exists", False, "Response file for INQ-004 not found")
        check("INQ-004 convergence ≥80% → auto-route declared", False, "File missing")
        check("INQ-004 routes to cnc-quote-system", False, "File missing")
    else:
        check("INQ-004 file exists", True, f"Found ({len(content)} chars)")

        # Should declare convergence ≥80% (100%)
        has_high_convergence = bool(re.search(r'收敛度[：:]\s*(100|80|9\d)%', content))
        check("INQ-004 convergence ≥80% indicated",
              has_high_convergence,
              f"Expected convergence ≥80%. Snippet: {content[:300]}")

        # Must reference cnc-quote-system routing
        routes_to_quote = bool(re.search(r'cnc-quote-system|报价Skill|调用报价|自动路由|auto.?route', content, re.IGNORECASE))
        check("INQ-004 auto-routes to cnc-quote-system",
              routes_to_quote,
              f"Expected routing to cnc-quote-system. Content: {content[:400]}")

        # Must NOT be a probe (no 🔴 asking for params that were provided)
        is_probe = bool(re.search(r'❓\s*请提供以下信息', content))
        check("INQ-004 is NOT a parameter probe (all params provided)",
              not is_probe,
              f"Should not probe when convergence ≥80%. is_probe: {is_probe}")

except Exception as e:
    check("INQ-004 processing error", False, str(e))

# ─────────────────────────────────────────────────────────────
# INQ-005: all 4 mandatory + Ra → convergence 100% → auto-route
# ─────────────────────────────────────────────────────────────
try:
    content = read_response("INQ-005")
    if content is None:
        check("INQ-005 file exists", False, "Response file for INQ-005 not found")
        check("INQ-005 auto-routes (all params including optional Ra)", False, "File missing")
    else:
        check("INQ-005 file exists", True, f"Found ({len(content)} chars)")

        routes_to_quote = bool(re.search(r'cnc-quote-system|报价Skill|调用报价|自动路由|auto.?route', content, re.IGNORECASE))
        check("INQ-005 auto-routes to cnc-quote-system (all 5 params provided)",
              routes_to_quote,
              f"Expected routing. Content: {content[:300]}")

        # Must not probe for Ra (it was provided)
        probes_ra = bool(re.search(r'🔴.*【Ra】|🔴.*【粗糙度】', content))
        check("INQ-005 does not probe for Ra (already provided)",
              not probes_ra,
              f"Should not probe for Ra. probes_ra: {probes_ra}")

except Exception as e:
    check("INQ-005 processing error", False, str(e))

# ─────────────────────────────────────────────────────────────
# Global format check: reply example line in at least one probe response
# ─────────────────────────────────────────────────────────────
try:
    probe_responses = []
    for inq_id in ["INQ-001", "INQ-002", "INQ-003"]:
        c = read_response(inq_id)
        if c:
            probe_responses.append(c)

    has_reply_example = any(
        bool(re.search(r'回复示例', c))
        for c in probe_responses
    )
    check("Probe responses include 回复示例 line",
          has_reply_example,
          f"At least one probe response must include '回复示例'. Found in {len(probe_responses)} probe files.")

    has_checkbox = any("□" in c for c in probe_responses)
    check("Probe responses include checkbox options (□)",
          has_checkbox,
          f"At least one probe response must include '□' checkbox options.")

    has_question_section = any("❓" in c for c in probe_responses)
    check("Probe responses include ❓ section marker",
          has_question_section,
          f"At least one probe must have ❓ marker.")

except Exception as e:
    check("Global format checks error", False, str(e))

# ─────────────────────────────────────────────────────────────
# Score calculation
# ─────────────────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
score = round(len(passed_checks) / len(checks), 4) if checks else 0.0
all_passed = len(passed_checks) == len(checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))