#!/usr/bin/env python3
"""
Evaluation script for open-memory-system task.
Checks:
1. Preference recorded: communication style -> direct and efficient (user_preference category)
2. Event recorded: "ProteinFold-V3 Paper Submission" milestone event
3. Episodic memory: dependency version lesson with 'negative' sentiment
4. Short-term files in correct YYYY-MM-DD-HHMM.md format exist
5. distill_l2 was run: L2 event files exist in user/events/ with source=distill_l2
6. Working memory updated (contains recent entries)
7. Summary was run successfully (not strictly file-checked but working.json updated)
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime

def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def main(workspace):
    ws = Path(workspace)
    memory_dir = ws / ".openclaw" / "workspace" / "memory"
    
    checks = []
    total_score = 0.0
    weights = {
        "pref_communication": 0.15,
        "event_proteinfold": 0.15,
        "episode_dependency": 0.15,
        "short_term_valid_format": 0.15,
        "distill_l2_ran": 0.20,
        "working_memory_updated": 0.10,
        "auto_save_hook_deployed": 0.10,
    }

    # ── CHECK 1: Preference for communication style ────────────────────────────
    check_name = "pref_communication"
    try:
        pref_dir = memory_dir / "user" / "preferences"
        pref_files = list(pref_dir.glob("*.json"))
        found = False
        detail = f"Found {len(pref_files)} preference files."
        for pf in pref_files:
            try:
                data = load_json(pf)
                key_val = data.get("key", "").lower()
                val_val = data.get("value", "").lower()
                cat_val = data.get("category", "").lower()
                # Looking for communication/style preference with direct/efficient value
                if any(k in key_val for k in ["communication", "沟通", "style", "report", "format"]):
                    if any(v in val_val for v in ["direct", "brief", "concise", "efficient", "bullet", "直接"]):
                        found = True
                        detail = f"Found pref: key='{data.get('key')}' value='{data.get('value')}' category='{data.get('category')}'"
                        break
                # Also check category-based match
                if "preference" in cat_val or "用户偏好" in cat_val or "user" in cat_val:
                    if any(v in val_val for v in ["direct", "brief", "concise", "efficient", "bullet", "直接"]):
                        found = True
                        detail = f"Found pref (category match): key='{data.get('key')}' value='{data.get('value')}'"
                        break
            except Exception:
                continue
        checks.append({"name": check_name, "passed": found, "detail": detail})
        if found:
            total_score += weights[check_name]
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 2: Event about ProteinFold / milestone / paper ──────────────────
    check_name = "event_proteinfold"
    try:
        event_dir = memory_dir / "user" / "events"
        event_files = list(event_dir.glob("*.json"))
        found = False
        detail = f"Found {len(event_files)} event files."
        for ef in event_files:
            try:
                data = load_json(ef)
                # Only look at manually-recorded events (source != distill_l2)
                source = data.get("source", "manual")
                if source == "distill_l2":
                    continue
                title = data.get("title", "").lower()
                desc = data.get("description", "").lower()
                combined = title + " " + desc
                if any(k in combined for k in ["proteinfold", "protein", "paper", "milestone", "submission", "phase"]):
                    found = True
                    detail = f"Found event: title='{data.get('title')}' source='{source}'"
                    break
            except Exception:
                continue
        checks.append({"name": check_name, "passed": found, "detail": detail})
        if found:
            total_score += weights[check_name]
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 3: Episodic memory with negative sentiment + dependency lesson ──
    check_name = "episode_dependency"
    try:
        ep_dir = memory_dir / "agent" / "episodic"
        ep_files = list(ep_dir.glob("*.json"))
        found = False
        correct_sentiment = False
        detail = f"Found {len(ep_files)} episodic files."
        for ef in ep_files:
            try:
                data = load_json(ef)
                sentiment = data.get("sentiment", "")
                lesson = data.get("lesson", "").lower()
                title = data.get("title", "").lower()
                combined = lesson + " " + title
                if any(k in combined for k in ["depend", "version", "deploy", "install", "package", "依赖"]):
                    found = True
                    correct_sentiment = sentiment == "negative"
                    detail = (f"Found episode: title='{data.get('title')}' "
                              f"sentiment='{sentiment}' (expected: negative) "
                              f"lesson='{data.get('lesson')}'")
                    break
            except Exception:
                continue
        passed = found and correct_sentiment
        if found and not correct_sentiment:
            detail += " | FAIL: sentiment is not 'negative'"
        checks.append({"name": check_name, "passed": passed, "detail": detail})
        if passed:
            total_score += weights[check_name]
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 4: Valid short-term .md files (YYYY-MM-DD-HHMM.md format) ───────
    check_name = "short_term_valid_format"
    try:
        stm_dir = memory_dir / "short-term"
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}\.md$")
        valid_files = [f for f in stm_dir.glob("*.md") if pattern.match(f.name)]
        # Must have at least 1 valid-format short-term file
        found = len(valid_files) >= 1
        detail = (f"Valid-format short-term files: {[f.name for f in valid_files]}. "
                  f"Total .md files: {len(list(stm_dir.glob('*.md')))}")
        checks.append({"name": check_name, "passed": found, "detail": detail})
        if found:
            total_score += weights[check_name]
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 5: distill_l2 was run (events with source=distill_l2 exist) ─────
    check_name = "distill_l2_ran"
    try:
        event_dir = memory_dir / "user" / "events"
        event_files = list(event_dir.glob("*.json"))
        distilled = []
        for ef in event_files:
            try:
                data = load_json(ef)
                if data.get("source") == "distill_l2":
                    distilled.append(ef.name)
            except Exception:
                continue
        found = len(distilled) >= 1
        detail = f"Found {len(distilled)} distilled L2 events: {distilled[:3]}"
        # Additionally verify these came from valid-format source files
        if found:
            for ef in event_files:
                try:
                    data = load_json(ef)
                    if data.get("source") == "distill_l2":
                        src_file = data.get("source_file", "")
                        if re.match(r"^\d{4}-\d{2}-\d{2}-\d{4}\.md$", src_file):
                            detail += f" | source_file='{src_file}' format OK"
                            break
                except Exception:
                    continue
        checks.append({"name": check_name, "passed": found, "detail": detail})
        if found:
            total_score += weights[check_name]
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 6: Working memory was updated (has non-stale items) ─────────────
    check_name = "working_memory_updated"
    try:
        wm_file = memory_dir / "working.json"
        data = load_json(wm_file)
        items = data.get("items", [])
        # Must have items beyond the initial stale one
        non_stale = [it for it in items if it.get("type") != "stale"]
        updated_at = data.get("updated_at", "")
        found = len(non_stale) >= 1
        detail = (f"Working memory items: {len(items)} total, {len(non_stale)} non-stale. "
                  f"updated_at='{updated_at}'")
        checks.append({"name": check_name, "passed": found, "detail": detail})
        if found:
            total_score += weights[check_name]
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 7: auto-save-memory hook deployed to ~/.openclaw/hooks/ ─────────
    check_name = "auto_save_hook_deployed"
    try:
        hooks_dir = ws / ".openclaw" / "hooks"
        # Check for auto-save-memory directory or script
        candidates = [
            hooks_dir / "auto-save-memory" / "run.sh",
            hooks_dir / "auto-save-memory.sh",
            hooks_dir / "auto-save-memory" / "hook.sh",
        ]
        found = any(c.exists() for c in candidates)
        # Also check if any sh file exists in auto-save-memory subdir
        asave_dir = hooks_dir / "auto-save-memory"
        if not found and asave_dir.exists():
            sh_files = list(asave_dir.glob("*.sh"))
            found = len(sh_files) > 0
        detail = f"auto-save-memory hook in {hooks_dir}: found={found}"
        if found:
            found_path = next((str(c) for c in candidates if c.exists()), 
                              str(next(iter(asave_dir.glob("*.sh")), "")) if asave_dir.exists() else "")
            detail += f" at {found_path}"
        checks.append({"name": check_name, "passed": found, "detail": detail})
        if found:
            total_score += weights[check_name]
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Final result ──────────────────────────────────────────────────────────
    passed = total_score >= 0.60  # Need at least 60% to pass
    result = {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)