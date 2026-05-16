#!/usr/bin/env python3
import sys
import json
import os
import subprocess
import hashlib
import re
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Precompute expected values ────────────────────────────────────────────────
# These mirror exactly what create_order.py and clawtip/run.py produce
LOCATION = "成都"
EXPECTED_ORDER_NO = "ORD-20240315-CHENGDU-8842"
EXPECTED_AMOUNT_FEN = 150  # fen, not yuan

encrypted_data_raw = "ENC_" + hashlib.md5((LOCATION + "secret_salt_42").encode()).hexdigest()[:16].upper()
PAY_TO = "PAYEE_WEATHER_SVC_JD_001"

token_base = f"{EXPECTED_ORDER_NO}:{encrypted_data_raw}:{PAY_TO}:VALID"
EXPECTED_CREDENTIAL = "CRED_" + hashlib.sha256(token_base.encode()).hexdigest()[:24].upper()

# ── CHECK 1: weather_report_result.txt exists ─────────────────────────────────
result_file = None
try:
    candidates = list(Path(workspace).rglob("weather_report_result.txt"))
    if candidates:
        result_file = candidates[0]
        add_check(
            "weather_report_result.txt 文件存在",
            True,
            f"找到文件: {result_file}"
        )
    else:
        add_check(
            "weather_report_result.txt 文件存在",
            False,
            "未找到 weather_report_result.txt 文件"
        )
except Exception as e:
    add_check("weather_report_result.txt 文件存在", False, f"搜索文件时出错: {e}")

# ── CHECK 2: PAY_STATUS is SUCCESS ────────────────────────────────────────────
pay_status_ok = False
if result_file:
    try:
        content = result_file.read_text(encoding="utf-8")
        match = re.search(r"PAY_STATUS[:\s]+(\S+)", content)
        if match:
            pay_status = match.group(1).strip()
            if pay_status == "SUCCESS":
                pay_status_ok = True
                add_check(
                    "PAY_STATUS 为 SUCCESS",
                    True,
                    f"PAY_STATUS={pay_status}"
                )
            else:
                add_check(
                    "PAY_STATUS 为 SUCCESS",
                    False,
                    f"PAY_STATUS={pay_status}，期望 SUCCESS"
                )
        else:
            add_check(
                "PAY_STATUS 为 SUCCESS",
                False,
                "结果文件中未找到 PAY_STATUS 字段"
            )
    except Exception as e:
        add_check("PAY_STATUS 为 SUCCESS", False, f"读取结果文件出错: {e}")
else:
    add_check("PAY_STATUS 为 SUCCESS", False, "结果文件不存在，跳过此检查")

# ── CHECK 3: Correct location in output ──────────────────────────────────────
if result_file:
    try:
        content = result_file.read_text(encoding="utf-8")
        if "成都" in content:
            add_check(
                "结果文件包含正确位置（成都）",
                True,
                "文件中包含'成都'"
            )
        else:
            add_check(
                "结果文件包含正确位置（成都）",
                False,
                f"文件中未找到'成都'，内容片段: {content[:200]}"
            )
    except Exception as e:
        add_check("结果文件包含正确位置（成都）", False, f"读取出错: {e}")
else:
    add_check("结果文件包含正确位置（成都）", False, "结果文件不存在，跳过此检查")

# ── CHECK 4: Weather content present ─────────────────────────────────────────
if result_file and pay_status_ok:
    try:
        content = result_file.read_text(encoding="utf-8")
        weather_keywords = ["天气", "气温", "风", "湿度"]
        found = [kw for kw in weather_keywords if kw in content]
        if len(found) >= 3:
            add_check(
                "结果文件包含天气报告内容",
                True,
                f"找到天气关键词: {found}"
            )
        else:
            add_check(
                "结果文件包含天气报告内容",
                False,
                f"天气关键词不足，仅找到: {found}"
            )
    except Exception as e:
        add_check("结果文件包含天气报告内容", False, f"读取出错: {e}")
else:
    add_check("结果文件包含天气报告内容", False, "PAY_STATUS 非 SUCCESS 或文件不存在，跳过")

# ── CHECK 5: Validate clawtip was called with correct parameters ──────────────
# We verify this indirectly: the credential verification server registered
# the expected credential. We re-run the credential check via the local server.
import urllib.request

try:
    check_data = json.dumps({
        "credential": EXPECTED_CREDENTIAL,
        "order_no": EXPECTED_ORDER_NO
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:9988/verify_credential",
        data=check_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if result.get("valid"):
        add_check(
            "clawtip 以正确参数调用（凭证已正确注册）",
            True,
            f"预期凭证 {EXPECTED_CREDENTIAL} 已在验证服务中注册"
        )
    else:
        add_check(
            "clawtip 以正确参数调用（凭证已正确注册）",
            False,
            f"预期凭证未注册。原因: {result.get('reason', '未知')}。"
            f"这意味着 clawtip 未以正确参数调用（skill-id、resource_url、skill_name、description 或 amount 不正确）"
        )
except Exception as e:
    add_check(
        "clawtip 以正确参数调用（凭证已正确注册）",
        False,
        f"无法连接验证服务: {e}"
    )

# ── CHECK 6: Amount passed as fen (not yuan) ──────────────────────────────────
# This is the "proprietary trap": agent must pass 150 (fen), not 1.5 or 1 (yuan)
# We detect this by checking if the credential is the expected one (already done in check 5)
# but we also look for any log/output files the agent may have created showing the amount
amount_check_passed = False
amount_detail = ""
try:
    # Search for any output file that might show clawtip invocation
    log_files = list(Path(workspace).rglob("*.log")) + list(Path(workspace).rglob("*.txt")) + list(Path(workspace).rglob("*.json"))
    for lf in log_files:
        if lf == result_file:
            continue
        try:
            text = lf.read_text(encoding="utf-8", errors="ignore")
            # If agent wrote amount as 1.5 or "1.50" yuan instead of 150 fen
            if re.search(r'"amount"\s*:\s*["\']?1\.5', text) or re.search(r'"amount"\s*:\s*["\']?1\b', text):
                amount_check_passed = False
                amount_detail = f"在 {lf} 中发现 amount 可能被错误地转换为元（非分）"
                break
        except Exception:
            continue
    else:
        # Primary evidence: if credential was correctly registered (check 5 passed),
        # the amount must have been passed as fen (150), because the mock clawtip rejects amount < 10
        cred_check = [c for c in checks if "clawtip 以正确参数调用" in c["name"]]
        if cred_check and cred_check[0]["passed"]:
            amount_check_passed = True
            amount_detail = "凭证已成功注册，说明 amount 字段以分（fen=150）传入，而非元（yuan=1.5）"
        else:
            amount_check_passed = False
            amount_detail = "凭证未正确注册，无法确认 amount 单位是否正确"
except Exception as e:
    amount_detail = f"检查 amount 单位时出错: {e}"

add_check("amount 字段以分（fen）传入 clawtip（非元）", amount_check_passed, amount_detail)

# ── CHECK 7: Order number in result file ──────────────────────────────────────
if result_file:
    try:
        content = result_file.read_text(encoding="utf-8")
        if EXPECTED_ORDER_NO in content:
            add_check(
                "结果文件包含正确订单号",
                True,
                f"找到订单号: {EXPECTED_ORDER_NO}"
            )
        else:
            add_check(
                "结果文件包含正确订单号",
                False,
                f"未找到订单号 {EXPECTED_ORDER_NO}，内容片段: {content[:300]}"
            )
    except Exception as e:
        add_check("结果文件包含正确订单号", False, f"读取出错: {e}")
else:
    add_check("结果文件包含正确订单号", False, "结果文件不存在，跳过")

# ── Scoring ───────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0
overall_passed = all(c["passed"] for c in checks)

output = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(output, ensure_ascii=False, indent=2))