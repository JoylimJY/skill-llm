import sys
import json
import re
from pathlib import Path
from datetime import date, timedelta

def run_eval(workspace_root: str):
    ws = Path(workspace_root)
    skill_refs = ws / "skills" / "myfood-by" / "references"
    inventory_file = skill_refs / "my-food.md"

    checks = []

    # ── Helper ─────────────────────────────────────────────────────────────────
    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── CHECK 1: my-food.md exists at the correct skill-relative path ──────────
    try:
        exists = inventory_file.exists()
        add_check(
            "inventory_file_exists_at_correct_path",
            exists,
            f"Expected {inventory_file} — {'found' if exists else 'NOT found'}."
        )
        if not exists:
            raise FileNotFoundError("inventory file missing")
        content = inventory_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        # If file is missing, remaining checks auto-fail
        for name in [
            "required_items_registered",
            "consumed_item_removed",
            "no_health_data_stored",
        ]:
            add_check(name, False, "Skipped — inventory file not found.")
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # ── CHECK 2: Required items are present in inventory ──────────────────────
    # Task says: register eggs, broccoli, milk (2025-07-10), chicken breast (expiry
    # set to 3 days from "today" by the task, i.e., near-expiry).
    # We check for presence of the four food names (minus the consumed one).
    # The consumed item is "milk" — so milk should NOT be present.
    required_present = ["鸡蛋", "西兰花", "鸡胸肉"]   # Chinese names expected
    # Also accept English names as fallback
    required_present_en = ["egg", "broccoli", "chicken"]

    content_lower = content.lower()

    def item_found(cn_name, en_variants):
        if cn_name in content:
            return True
        for v in en_variants:
            if v in content_lower:
                return True
        return False

    item_map = [
        ("鸡蛋", ["egg", "eggs"]),
        ("西兰花", ["broccoli"]),
        ("鸡胸肉", ["chicken breast", "chicken"]),
    ]
    all_required_found = True
    missing = []
    for cn, en in item_map:
        if not item_found(cn, en):
            all_required_found = False
            missing.append(cn)

    add_check(
        "required_items_registered",
        all_required_found,
        f"All required items (鸡蛋, 西兰花, 鸡胸肉) must be in inventory. "
        f"Missing: {missing if missing else 'none'}."
    )

    # ── CHECK 3: Consumed item (牛奶/milk) is REMOVED from the file ───────────
    milk_present = "牛奶" in content or "milk" in content_lower
    add_check(
        "consumed_item_removed",
        not milk_present,
        f"牛奶 (milk) was marked as consumed and must be deleted from inventory. "
        f"Currently {'still present — FAIL' if milk_present else 'absent — PASS'}."
    )

    # ── CHECK 4: No health/dietary restriction data stored in inventory file ───
    # SKILL.md explicitly forbids storing health info; check for obvious violations
    health_keywords = [
        "过敏", "禁忌", "不耐受", "健康", "allerg", "intoleran",
        "lactose", "gluten", "禁止", "病史", "医疗"
    ]
    health_found = [kw for kw in health_keywords if kw.lower() in content.lower()]
    add_check(
        "no_health_data_stored",
        len(health_found) == 0,
        f"Inventory file must NOT store health/dietary restriction data. "
        f"Found prohibited keywords: {health_found if health_found else 'none'}."
    )

    # ── CHECK 5: Look for diet recommendation output file ─────────────────────
    # The agent should have produced a recommendation. We search for any .md or .txt
    # file (outside the inventory) that contains the 【已有】 marker and ⚠️ 临期提醒.
    recommendation_files = []
    for f in ws.rglob("*"):
        if f == inventory_file:
            continue
        if f.suffix in (".md", ".txt") and f.is_file():
            try:
                txt = f.read_text(encoding="utf-8", errors="ignore")
                if "【已有】" in txt or "⚠️" in txt or "临期" in txt:
                    recommendation_files.append(f)
            except Exception:
                pass

    # Also check if the agent wrote recommendation output to a conversation log
    # or any file under workspace
    all_workspace_text = ""
    for f in ws.rglob("*"):
        if f.is_file() and f.suffix in (".md", ".txt", ".json", ".log", ".out"):
            try:
                all_workspace_text += f.read_text(encoding="utf-8", errors="ignore") + "\n"
            except Exception:
                pass

    has_yiyou_marker = "【已有】" in all_workspace_text
    has_liqi_reminder = ("⚠️" in all_workspace_text or "临期提醒" in all_workspace_text)

    add_check(
        "recommendation_has_yiyou_marker",
        has_yiyou_marker,
        "Recommendation output must contain 【已有】 markers for ingredients "
        f"that come from the user's inventory. Found: {has_yiyou_marker}."
    )

    add_check(
        "recommendation_has_liqi_reminder",
        has_liqi_reminder,
        "Recommendation output must include a ⚠️ 临期提醒 section for near-expiry items. "
        f"Found: {has_liqi_reminder}."
    )

    # ── Scoring ────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)