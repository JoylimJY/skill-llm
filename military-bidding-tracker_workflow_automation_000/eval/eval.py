import sys
import json
import sqlite3
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    db_path = workspace / "data" / "bids.db"
    checks = []

    # ── Helper: query DB ──────────────────────────────────────────────
    def query_db(sql, params=()):
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    # ── Check 1: DB exists and was initialized ─────────────────────
    def check_db_exists():
        if not db_path.exists():
            return False, f"DB not found at {db_path}"
        rows = query_db("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r['name'] for r in rows}
        if 'projects' not in tables:
            return False, f"'projects' table missing. Found tables: {tables}"
        return True, f"DB exists with tables: {tables}"
    checks.append(run_check("DB initialized with projects table", check_db_exists))

    # ── Check 2: Communication equipment project registered correctly ─
    def check_project1_registered():
        rows = query_db("SELECT * FROM projects WHERE project_name LIKE '%通信%' OR project_name LIKE '%通信设备%'")
        if not rows:
            rows = query_db("SELECT * FROM projects WHERE project_name LIKE '%维护保障%'")
        if not rows:
            all_proj = query_db("SELECT project_name, status FROM projects")
            return False, f"通信设备项目未找到. All projects: {all_proj}"
        p = rows[0]
        details = []
        # Check budget ~1280000
        budget = p.get('budget', 0)
        budget_ok = budget and abs(float(budget) - 1280000) < 1000
        details.append(f"budget={budget} (expected ~1280000, ok={budget_ok})")
        # Check manager
        manager = p.get('manager_name', '') or p.get('manager', '')
        manager_ok = '张' in str(manager)
        details.append(f"manager={manager} (expected 张经理, ok={manager_ok})")
        # Check bid_opening_time contains 2026-03-20
        bot = str(p.get('bid_opening_time', ''))
        bot_ok = '2026-03-20' in bot
        details.append(f"bid_opening_time={bot} (ok={bot_ok})")
        passed = budget_ok and manager_ok and bot_ok
        return passed, "; ".join(details)
    checks.append(run_check("通信设备项目注册正确（预算、负责人、开标时间）", check_project1_registered))

    # ── Check 3: Drone parts project registered correctly ─────────────
    def check_project2_registered():
        rows = query_db("SELECT * FROM projects WHERE project_name LIKE '%无人机%'")
        if not rows:
            rows = query_db("SELECT * FROM projects WHERE project_name LIKE '%零部件%'")
        if not rows:
            all_proj = query_db("SELECT project_name, status FROM projects")
            return False, f"无人机项目未找到. All projects: {all_proj}"
        p = rows[0]
        details = []
        budget = p.get('budget', 0)
        budget_ok = budget and abs(float(budget) - 850000) < 1000
        details.append(f"budget={budget} (expected ~850000, ok={budget_ok})")
        manager = p.get('manager_name', '') or p.get('manager', '')
        manager_ok = '李' in str(manager)
        details.append(f"manager={manager} (expected 李经理, ok={manager_ok})")
        bot = str(p.get('bid_opening_time', ''))
        bot_ok = '2026-03-25' in bot
        details.append(f"bid_opening_time={bot} (ok={bot_ok})")
        passed = budget_ok and manager_ok and bot_ok
        return passed, "; ".join(details)
    checks.append(run_check("无人机项目注册正确（预算、负责人、开标时间）", check_project2_registered))

    # ── Check 4: 通信设备项目最终状态为 won ───────────────────────────
    def check_project1_won():
        rows = query_db("SELECT * FROM projects WHERE (project_name LIKE '%通信%' OR project_name LIKE '%维护保障%')")
        if not rows:
            return False, "通信设备项目未找到"
        p = rows[0]
        status = p.get('status', '')
        if status != 'won':
            return False, f"状态为 '{status}'，期望 'won'"
        our_price = p.get('our_price', 0)
        price_ok = our_price and abs(float(our_price) - 1250000) < 1000
        return price_ok, f"status={status}, our_price={our_price} (expected ~1250000)"
    checks.append(run_check("通信设备项目状态=won且报价正确", check_project1_won))

    # ── Check 5: 无人机项目最终状态为 lost ────────────────────────────
    def check_project2_lost():
        rows = query_db("SELECT * FROM projects WHERE (project_name LIKE '%无人机%' OR project_name LIKE '%零部件%')")
        if not rows:
            return False, "无人机项目未找到"
        p = rows[0]
        status = p.get('status', '')
        if status != 'lost':
            return False, f"状态为 '{status}'，期望 'lost'"
        details = [f"status={status}"]
        our_price = p.get('our_price', 0)
        price_ok = our_price and abs(float(our_price) - 820000) < 1000
        details.append(f"our_price={our_price} (expected ~820000, ok={price_ok})")
        winning_price = p.get('winning_price', 0)
        wp_ok = winning_price and abs(float(winning_price) - 780000) < 1000
        details.append(f"winning_price={winning_price} (expected ~780000, ok={wp_ok})")
        winner = str(p.get('winner', ''))
        winner_ok = '飞翔' in winner or '西南' in winner
        details.append(f"winner={winner} (ok={winner_ok})")
        passed = price_ok and wp_ok and winner_ok
        return passed, "; ".join(details)
    checks.append(run_check("无人机项目状态=lost且完整信息正确", check_project2_lost))

    # ── Check 6: State machine traversal - both went through sealed ───
    def check_state_machine_traversal():
        """Verify projects went through proper state transitions by checking 
        that sealed_time is populated (meaning seal command was called)"""
        rows = query_db("SELECT project_name, status, sealed_time FROM projects WHERE project_name LIKE '%通信%' OR project_name LIKE '%维护保障%' OR project_name LIKE '%无人机%' OR project_name LIKE '%零部件%'")
        if len(rows) < 2:
            return False, f"Only found {len(rows)} relevant projects"
        details = []
        all_ok = True
        for p in rows:
            has_sealed_time = p.get('sealed_time') is not None and str(p.get('sealed_time', '')) != ''
            details.append(f"{p['project_name']}: sealed_time={p.get('sealed_time')}, present={has_sealed_time}")
            if not has_sealed_time:
                all_ok = False
        return all_ok, "; ".join(details)
    checks.append(run_check("两个项目均经过了封标（sealed_time已记录）", check_state_machine_traversal))

    # ── Check 7: manager_stats.json exists and is valid ───────────────
    def check_stats_file():
        # Search in workspace root first, then recursively
        candidates = list(workspace.glob("manager_stats.json"))
        if not candidates:
            candidates = list(workspace.rglob("manager_stats.json"))
        if not candidates:
            return False, "manager_stats.json 文件未找到"
        stats_file = candidates[0]
        content = stats_file.read_text(encoding="utf-8")
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return False, f"JSON解析失败: {e}. Content: {content[:200]}"
        # The file should contain stats data - check it has meaningful content
        content_str = str(data)
        has_zhang = '张' in content_str
        has_li = '李' in content_str
        details = f"File found at {stats_file}, has_张={has_zhang}, has_李={has_li}, keys/structure: {str(data)[:300]}"
        passed = has_zhang and has_li
        return passed, details
    checks.append(run_check("manager_stats.json存在且包含两位负责人数据", check_stats_file))

    # ── Check 8: Stats correctness - 张经理 should have 1 won ─────────
    def check_stats_correctness():
        candidates = list(workspace.glob("manager_stats.json")) or list(workspace.rglob("manager_stats.json"))
        if not candidates:
            return False, "manager_stats.json 文件未找到"
        content = candidates[0].read_text(encoding="utf-8")
        try:
            data = json.loads(content)
        except:
            return False, "JSON解析失败"
        content_str = json.dumps(data, ensure_ascii=False)
        # Look for win-related data
        # The stats should reflect 张经理 won 1, 李经理 lost 1
        # We just verify the data is stats output (not empty, not error)
        is_stats_output = (
            'status' in content_str.lower() or 
            'won' in content_str.lower() or
            '中标' in content_str or
            'win' in content_str.lower() or
            'manager' in content_str.lower() or
            '张' in content_str
        )
        return is_stats_output, f"Stats content appears to be valid stats output: {content_str[:400]}"
    checks.append(run_check("manager_stats.json内容为有效的按负责人统计数据", check_stats_correctness))

    # ── Scoring ───────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    overall = passed_count >= 6  # Need at least 6/8 to pass

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()