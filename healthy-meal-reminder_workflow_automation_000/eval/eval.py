import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []

    # ── 1. Find alice_cron_setup.sh ──────────────────────────────────────────
    cron_files = list(workspace.rglob("alice_cron_setup.sh"))
    if not cron_files:
        checks.append(check("alice_cron_setup.sh exists", False, "File not found anywhere in workspace"))
        cron_content = ""
    else:
        cron_content = cron_files[0].read_text(encoding="utf-8")
        checks.append(check("alice_cron_setup.sh exists", True, str(cron_files[0])))

    # ── 2. Find diet_log_2024-12-10.md ───────────────────────────────────────
    log_files = list(workspace.rglob("diet_log_2024-12-10.md"))
    if not log_files:
        checks.append(check("diet_log_2024-12-10.md exists", False, "File not found anywhere in workspace"))
        log_content = ""
    else:
        log_content = log_files[0].read_text(encoding="utf-8")
        checks.append(check("diet_log_2024-12-10.md exists", True, str(log_files[0])))

    # ══════════════════════════════════════════════════════════════════════════
    # CRON SCRIPT CHECKS
    # ══════════════════════════════════════════════════════════════════════════

    # Check: must use openclaw cron add
    uses_openclaw = "openclaw cron add" in cron_content
    checks.append(check(
        "Uses 'openclaw cron add' command",
        uses_openclaw,
        f"Found 'openclaw cron add': {uses_openclaw}"
    ))

    # Check: --tz "Asia/Shanghai" present
    tz_ok = 'Asia/Shanghai' in cron_content
    checks.append(check(
        "--tz Asia/Shanghai present",
        tz_ok,
        "Timezone flag Asia/Shanghai found" if tz_ok else "Missing --tz Asia/Shanghai"
    ))

    # Check: 早餐 at 0 7 * * * (07:00)
    breakfast_schedule = bool(re.search(r'--schedule\s+["\']?0 7 \* \* \*["\']?', cron_content))
    checks.append(check(
        "早餐 cron schedule: 0 7 * * *",
        breakfast_schedule,
        "Found schedule '0 7 * * *'" if breakfast_schedule else "Missing '0 7 * * *' schedule for 早餐"
    ))

    # Check: 午餐 at 0 12 * * *
    lunch_schedule = bool(re.search(r'--schedule\s+["\']?0 12 \* \* \*["\']?', cron_content))
    checks.append(check(
        "午餐 cron schedule: 0 12 * * *",
        lunch_schedule,
        "Found schedule '0 12 * * *'" if lunch_schedule else "Missing '0 12 * * *' schedule for 午餐"
    ))

    # Check: 晚餐 at 30 18 * * *
    dinner_schedule = bool(re.search(r'--schedule\s+["\']?30 18 \* \* \*["\']?', cron_content))
    checks.append(check(
        "晚餐 cron schedule: 30 18 * * *",
        dinner_schedule,
        "Found schedule '30 18 * * *'" if dinner_schedule else "Missing '30 18 * * *' schedule for 晚餐"
    ))

    # Check: 下午茶 at 0 15 * * *
    tea_schedule = bool(re.search(r'--schedule\s+["\']?0 15 \* \* \*["\']?', cron_content))
    checks.append(check(
        "下午茶 cron schedule: 0 15 * * *",
        tea_schedule,
        "Found schedule '0 15 * * *'" if tea_schedule else "Missing '0 15 * * *' schedule for 下午茶"
    ))

    # Check: 早餐跟进 at 30 7 * * * (follow-up 30min after)
    breakfast_followup = bool(re.search(r'--schedule\s+["\']?30 7 \* \* \*["\']?', cron_content))
    checks.append(check(
        "早餐跟进 cron schedule: 30 7 * * *",
        breakfast_followup,
        "Found '30 7 * * *' for breakfast follow-up" if breakfast_followup else "Missing '30 7 * * *' for 早餐跟进"
    ))

    # Check: 午餐跟进 at 30 12 * * *
    lunch_followup = bool(re.search(r'--schedule\s+["\']?30 12 \* \* \*["\']?', cron_content))
    checks.append(check(
        "午餐跟进 cron schedule: 30 12 * * *",
        lunch_followup,
        "Found '30 12 * * *' for lunch follow-up" if lunch_followup else "Missing '30 12 * * *' for 午餐跟进"
    ))

    # Check: 晚餐跟进 at 0 19 * * *
    dinner_followup = bool(re.search(r'--schedule\s+["\']?0 19 \* \* \*["\']?', cron_content))
    checks.append(check(
        "晚餐跟进 cron schedule: 0 19 * * *",
        dinner_followup,
        "Found '0 19 * * *' for dinner follow-up" if dinner_followup else "Missing '0 19 * * *' for 晚餐跟进"
    ))

    # Check: 运动提醒 at 0 20 * * *
    exercise_schedule = bool(re.search(r'--schedule\s+["\']?0 20 \* \* \*["\']?', cron_content))
    checks.append(check(
        "运动提醒 cron schedule: 0 20 * * *",
        exercise_schedule,
        "Found '0 20 * * *' for 运动提醒" if exercise_schedule else "Missing '0 20 * * *' for 运动提醒"
    ))

    # Check: 周报 cron at 0 21 * * 0 (Sunday 21:00)
    weekly_schedule = bool(re.search(r'--schedule\s+["\']?0 21 \* \* 0["\']?', cron_content))
    checks.append(check(
        "周报打卡 cron schedule: 0 21 * * 0",
        weekly_schedule,
        "Found '0 21 * * 0' for 周报打卡" if weekly_schedule else "Missing '0 21 * * 0' for 周报打卡"
    ))

    # Check: 增肌 mode calorie target mentioned in messages (2000-2500)
    jiangjin_kcal = bool(re.search(r'2000[-–]2500', cron_content))
    checks.append(check(
        "增肌 mode calorie target (2000-2500) in cron messages",
        jiangjin_kcal,
        "Found '2000-2500' kcal range in cron messages" if jiangjin_kcal else "Missing 2000-2500 kcal target for 增肌 mode"
    ))

    # Check: --name flags used (at least 4 distinct names)
    name_count = len(re.findall(r'--name\s+["\']?[^"\']+["\']?', cron_content))
    names_ok = name_count >= 8  # 4 meals + 3 followups + exercise + weekly = 9 minimum
    checks.append(check(
        "Sufficient --name entries (>=8)",
        names_ok,
        f"Found {name_count} --name entries (need >=8)"
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # DIET LOG CHECKS
    # ══════════════════════════════════════════════════════════════════════════

    # Check: Header with correct date
    header_ok = bool(re.search(r'##\s*饮食记录\s*2024-12-10', log_content))
    checks.append(check(
        "Diet log header: ## 饮食记录 2024-12-10",
        header_ok,
        "Found correct date header" if header_ok else "Missing '## 饮食记录 2024-12-10' header"
    ))

    # Check: 早餐 entry with A option from winter breakfast A pool
    # Winter A: 红枣小米粥+水煮蛋 ~240kcal
    breakfast_entry = bool(re.search(r'早餐\s*\([0-9:]+\)\s*:\s*A[\.\。]', log_content))
    checks.append(check(
        "Diet log: 早餐 entry labeled A",
        breakfast_entry,
        "Found 早餐(XX:XX): A. entry" if breakfast_entry else "Missing 早餐(...): A. entry"
    ))

    # Check: 早餐 A from winter pool — 红枣小米粥 or 水煮蛋
    breakfast_winter_a = bool(re.search(r'红枣小米粥|红枣.*粥', log_content))
    checks.append(check(
        "Diet log: 早餐 A matches winter pool (红枣小米粥+水煮蛋)",
        breakfast_winter_a,
        "Found 红枣小米粥 in breakfast entry" if breakfast_winter_a else "Missing winter A breakfast item (红枣小米粥+水煮蛋 ~240kcal)"
    ))

    # Check: 午餐 entry with B option from winter lunch B pool
    # Winter B: 红枣枸杞乌鸡汤+清炒菠菜 ~320kcal
    lunch_entry = bool(re.search(r'午餐\s*\([0-9:]+\)\s*:\s*B[\.\。]', log_content))
    checks.append(check(
        "Diet log: 午餐 entry labeled B",
        lunch_entry,
        "Found 午餐(XX:XX): B. entry" if lunch_entry else "Missing 午餐(...): B. entry"
    ))

    lunch_winter_b = bool(re.search(r'乌鸡|红枣枸杞', log_content))
    checks.append(check(
        "Diet log: 午餐 B matches winter pool (红枣枸杞乌鸡汤+清炒菠菜)",
        lunch_winter_b,
        "Found winter B lunch item" if lunch_winter_b else "Missing winter B lunch item (红枣枸杞乌鸡汤+清炒菠菜 ~320kcal)"
    ))

    # Check: 下午茶 entry with A option — Winter A is 红茶/姜茶 0kcal
    teatime_entry = bool(re.search(r'下午茶\s*\([0-9:]+\)\s*:\s*A[\.\。]', log_content))
    checks.append(check(
        "Diet log: 下午茶 entry labeled A",
        teatime_entry,
        "Found 下午茶(XX:XX): A. entry" if teatime_entry else "Missing 下午茶(...): A. entry"
    ))

    teatime_0kcal = bool(re.search(r'[红姜]茶|0\s*kcal', log_content, re.IGNORECASE))
    checks.append(check(
        "Diet log: 下午茶 A is 0kcal (红茶/姜茶)",
        teatime_0kcal,
        "Found 0kcal tea entry" if teatime_0kcal else "Missing 0kcal for winter A tea (红茶/姜茶)"
    ))

    # Check: 晚餐 entry with C option from winter dinner C pool
    # Winter C: 红薯+无糖酸奶 ~220kcal OR 今天不吃了 0kcal
    dinner_entry = bool(re.search(r'晚餐\s*\([0-9:]+\)\s*:\s*C[\.\。]', log_content))
    checks.append(check(
        "Diet log: 晚餐 entry labeled C",
        dinner_entry,
        "Found 晚餐(XX:XX): C. entry" if dinner_entry else "Missing 晚餐(...): C. entry"
    ))

    dinner_winter_c = bool(re.search(r'红薯.*酸奶|无糖酸奶|今天不吃|0\s*kcal', log_content))
    checks.append(check(
        "Diet log: 晚餐 C matches winter pool (红薯+无糖酸奶 or 不吃)",
        dinner_winter_c,
        "Found winter C dinner item" if dinner_winter_c else "Missing winter C dinner (红薯+无糖酸奶 ~220kcal or 今天不吃了)"
    ))

    # Check: separator line ---
    separator_ok = '---' in log_content
    checks.append(check(
        "Diet log: contains separator '---'",
        separator_ok,
        "Found '---' separator" if separator_ok else "Missing '---' separator line"
    ))

    # Check: 当日总摄入 footer present
    total_footer = bool(re.search(r'当日总摄入\s*:\s*\d+', log_content))
    checks.append(check(
        "Diet log: 当日总摄入: XXXX kcal footer",
        total_footer,
        "Found 当日总摄入 footer" if total_footer else "Missing '当日总摄入: XXXX kcal' footer"
    ))

    # Check: 目标 reflects 增肌 mode (2000-2500 kcal)
    goal_jiangjin = bool(re.search(r'目标\s*:\s*2000[-–]2500', log_content))
    checks.append(check(
        "Diet log: 目标: 2000-2500 kcal (增肌 mode)",
        goal_jiangjin,
        "Found '目标: 2000-2500 kcal'" if goal_jiangjin else "Missing '目标: 2000-2500 kcal' — wrong mode or default 减肥 target used"
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # SCORING
    # ══════════════════════════════════════════════════════════════════════════
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall = passed_count >= int(total * 0.80)  # 80% threshold

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace_dir)