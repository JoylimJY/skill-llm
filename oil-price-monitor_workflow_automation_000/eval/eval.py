import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
total_score = 0.0
max_score = 0.0


def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight


# ─────────────────────────────────────────────
# 1. Find fuel_alert.txt
# ─────────────────────────────────────────────
alert_files = list(workspace.rglob("fuel_alert.txt"))
if not alert_files:
    add_check("fuel_alert.txt exists", False, "File 'fuel_alert.txt' not found anywhere in workspace.", weight=2.0)
    alert_content = ""
else:
    alert_content = alert_files[0].read_text(encoding="utf-8", errors="replace")
    add_check("fuel_alert.txt exists", True, f"Found at {alert_files[0].relative_to(workspace)}", weight=2.0)

# ─────────────────────────────────────────────
# 2. Correct next adjustment date: Aug 14
#    Today = Aug 10, so next window = Aug 14 (NOT Aug 28, NOT Aug 7 from fake schedule)
# ─────────────────────────────────────────────
has_aug14 = bool(re.search(r'8\s*月\s*14\s*日|8月14日|8/14', alert_content))
add_check(
    "Correct next adjustment date (Aug 14)",
    has_aug14,
    f"Alert must reference '8月14日' as next adjustment. Content snippet: {alert_content[:300]}",
    weight=2.5
)

# ─────────────────────────────────────────────
# 3. Countdown = 4 days (Aug 14 - Aug 10 = 4 days)
# ─────────────────────────────────────────────
countdown_match = re.search(r'(\d+)\s*[天日]', alert_content)
correct_countdown = False
countdown_detail = "No countdown (X天) found in alert."
if countdown_match:
    val = int(countdown_match.group(1))
    correct_countdown = (val == 4)
    countdown_detail = f"Found countdown: {val}天. Expected: 4天 (Aug 14 - Aug 10)."
add_check("Correct countdown (4 days)", correct_countdown, countdown_detail, weight=2.0)

# ─────────────────────────────────────────────
# 4. Price increase per liter: 0.18 元/升
# ─────────────────────────────────────────────
has_018_liter = bool(re.search(r'0\.18\s*元[/／]升|0\.18元/升|涨幅.*0\.18|0\.18.*元.*升', alert_content))
add_check(
    "Correct per-liter adjustment (0.18 元/升)",
    has_018_liter,
    f"Alert must show '0.18元/升'. Content snippet: {alert_content[:400]}",
    weight=1.5
)

# ─────────────────────────────────────────────
# 5. Per-ton figure: 230 元/吨
# ─────────────────────────────────────────────
has_230_ton = bool(re.search(r'230\s*元[/／]吨|230元/吨|230.*吨', alert_content))
add_check(
    "Correct per-ton adjustment (230 元/吨)",
    has_230_ton,
    f"Alert must show '230元/吨'. Content: {alert_content[:400]}",
    weight=1.5
)

# ─────────────────────────────────────────────
# 6. Direction: 上涨 (price rising)
# ─────────────────────────────────────────────
has_rising = bool(re.search(r'上涨|价格上[升涨]|涨价', alert_content))
add_check(
    "Correct direction (上涨)",
    has_rising,
    f"Direction should be '上涨'. Found: {bool(has_rising)}",
    weight=1.0
)

# ─────────────────────────────────────────────
# 7. Recommendation: 提前加油 (fill up early, not 观望)
# ─────────────────────────────────────────────
has_fill_early = bool(re.search(r'提前加油', alert_content))
has_observe = bool(re.search(r'观望', alert_content)) and not has_fill_early
correct_recommendation = has_fill_early and not has_observe
add_check(
    "Correct recommendation (提前加油)",
    correct_recommendation,
    f"Should recommend '提前加油' for rising price. has_fill_early={has_fill_early}, has_observe={has_observe}",
    weight=1.5
)

# ─────────────────────────────────────────────
# 8. 50L tank cost calculation: 0.18 * 50 = 9.0 元
# ─────────────────────────────────────────────
# Accept 9 or 9.0 or 9.00
has_9yuan = bool(re.search(r'9[\s\.]?0*\s*元|约\s*9\s*元|多花.*9|9.*多花', alert_content))
add_check(
    "50L tank cost increase (9 元)",
    has_9yuan,
    f"50L × 0.18元/升 = 9元. Alert should mention approx 9元 extra cost. Content: {alert_content[:500]}",
    weight=2.0
)

# ─────────────────────────────────────────────
# 9. ⛽ emoji present (from template)
# ─────────────────────────────────────────────
has_emoji = '⛽' in alert_content
add_check(
    "Contains ⛽ emoji (template compliance)",
    has_emoji,
    f"Template requires ⛽ emoji. Found: {has_emoji}",
    weight=0.5
)

# ─────────────────────────────────────────────
# 10. cron-jobs.md updated with oil price entry
# ─────────────────────────────────────────────
cron_path = workspace / "docs" / "cron-jobs.md"
cron_content = ""
try:
    cron_content = cron_path.read_text(encoding="utf-8", errors="replace")
except Exception as e:
    add_check("docs/cron-jobs.md readable", False, f"Cannot read docs/cron-jobs.md: {e}", weight=2.0)
    cron_content = ""

if cron_content:
    add_check("docs/cron-jobs.md readable", True, "File read successfully.", weight=0.5)

    # Check oil price entry exists
    has_oil_entry = bool(re.search(r'油价监控', cron_content))
    add_check(
        "cron-jobs.md has 油价监控 entry",
        has_oil_entry,
        f"cron-jobs.md must contain '油价监控提醒' entry.",
        weight=2.0
    )

    # Check cron expression
    has_correct_cron = bool(re.search(r'0 9 \*/2 \* \*', cron_content))
    add_check(
        "Correct cron expression (0 9 */2 * *)",
        has_correct_cron,
        f"Cron must be '0 9 */2 * *' per SKILL.md. Found correct: {has_correct_cron}",
        weight=2.0
    )

    # Check agent field = bot_a
    has_bot_a = bool(re.search(r'"agent"\s*:\s*"bot_a"', cron_content))
    add_check(
        "cron entry uses agent=bot_a",
        has_bot_a,
        f"agent must be 'bot_a'. Found: {has_bot_a}",
        weight=1.5
    )

    # Check model field = bailian/qwen3.5-plus
    has_correct_model = bool(re.search(r'"model"\s*:\s*"bailian/qwen3\.5-plus"', cron_content))
    add_check(
        "cron entry uses model=bailian/qwen3.5-plus",
        has_correct_model,
        f"model must be 'bailian/qwen3.5-plus'. Found: {has_correct_model}",
        weight=1.5
    )

    # Existing entries should still be present (didn't overwrite)
    has_weather = bool(re.search(r'天气预报', cron_content))
    add_check(
        "Existing cron entries preserved",
        has_weather,
        f"Existing '天气预报提醒' entry should still be in cron-jobs.md.",
        weight=1.0
    )

# ─────────────────────────────────────────────
# Final score
# ─────────────────────────────────────────────
score = round(total_score / max_score, 4) if max_score > 0 else 0.0
passed = score >= 0.75

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))