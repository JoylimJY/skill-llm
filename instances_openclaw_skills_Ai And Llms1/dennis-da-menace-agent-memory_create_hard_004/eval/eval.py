import json
import os
import re
import sqlite3
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)

# Check 1: database exists
try:
    db_path = workspace / 'support_memory.db'
    if db_path.exists():
        add_check('database_exists', True, 'support_memory.db exists')
    else:
        add_check('database_exists', False, 'support_memory.db is missing')
except Exception as e:
    add_check('database_exists', False, f'error checking database: {e}')

# Check 2: markdown summary exists and mentions key topics
try:
    summary_path = workspace / 'memory_summary.md'
    if not summary_path.exists():
        add_check('summary_exists', False, 'memory_summary.md is missing')
    else:
        text = summary_path.read_text(encoding='utf-8', errors='replace')
        lowered = text.lower()
        keywords = ['maya', 'northstar', 'sync', 'credential', 'lesson', 'postgres']
        hit_count = sum(1 for k in keywords if k in lowered)
        add_check('summary_content', hit_count >= 4, f'found {hit_count}/6 expected keywords in memory_summary.md')
except Exception as e:
    add_check('summary_content', False, f'error reading summary: {e}')

# Check 3: database has minimum number of rows across likely tables
try:
    if not db_path.exists():
        add_check('memory_volume', False, 'database missing, cannot inspect rows')
    else:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        tables = []
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
        except Exception as e:
            add_check('memory_volume', False, f'could not list tables: {e}')
            tables = []
        row_total = 0
        table_details = []
        for t in tables:
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{t}"')
                cnt = int(cur.fetchone()[0])
                row_total += cnt
                table_details.append(f'{t}:{cnt}')
            except Exception:
                continue
        conn.close()
        add_check('memory_volume', row_total >= 10, f'total rows across tables = {row_total}; tables = {", ".join(table_details) if table_details else "none"}')
except Exception as e:
    add_check('memory_volume', False, f'error inspecting database: {e}')

# Check 4: markers or source-related facts made it into the database text dump
try:
    if not db_path.exists():
        add_check('marker_preservation', False, 'database missing, cannot verify markers')
    else:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        blobs = []
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            for t in tables:
                try:
                    cur.execute(f'SELECT * FROM "{t}" LIMIT 50')
                    rows = cur.fetchall()
                    blobs.extend([str(r) for r in rows])
                except Exception:
                    pass
        finally:
            conn.close()
        combined = '\n'.join(blobs).lower()
        markers = ['am-marker-alpha-17', 'am-marker-beta-42', 'am-marker-gamma-88', 'am-marker-delta-03']
        found = sum(1 for m in markers if m in combined)
        add_check('marker_preservation', found >= 2, f'found {found}/4 expected markers in database contents')
except Exception as e:
    add_check('marker_preservation', False, f'error verifying markers: {e}')

# Check 5: evidence of facts/lessons/entities in summary or db text
try:
    evidence_text = ''
    if summary_path.exists():
        evidence_text += summary_path.read_text(encoding='utf-8', errors='replace') + '\n'
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            for (t,) in cur.fetchall():
                try:
                    cur.execute(f'SELECT * FROM "{t}" LIMIT 20')
                    evidence_text += '\n'.join(str(r) for r in cur.fetchall()) + '\n'
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
    lowered = evidence_text.lower()
    expected_terms = ['maya chen', 'northstar logistics', 'sync failures', 'credential rotation', 'postgres', 'token refresh']
    term_hits = sum(1 for t in expected_terms if t in lowered)
    add_check('semantic_coverage', term_hits >= 4, f'found {term_hits}/6 expected semantic terms')
except Exception as e:
    add_check('semantic_coverage', False, f'error checking semantic coverage: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
