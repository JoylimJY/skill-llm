import sys
import json
import re
from pathlib import Path
from datetime import datetime

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ─── HELPER ────────────────────────────────────────────────────────────────
    def add(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 1: A session JSON was created (the `up` command was invoked)
    # ═══════════════════════════════════════════════════════════════════════════
    sessions_dir = ws / "sessions"
    session_files = list(sessions_dir.glob("*.json")) if sessions_dir.exists() else []

    # Also accept already-deleted sessions — the agent may have run `down --delete-session-dir`
    # So we look for evidence in an output message file instead (see check 3).
    # We'll re-examine this after checking the message file.

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 2: Find the Telegram message file
    # ═══════════════════════════════════════════════════════════════════════════
    message_file = None
    candidate_patterns = ["*.txt", "*.md", "telegram_message*", "message*", "preview_message*", "link*"]
    for pat in candidate_patterns:
        found = list(ws.rglob(pat))
        # exclude scripts, logs, configs
        found = [f for f in found if "scripts" not in str(f) and "data" not in str(f)
                 and "references" not in str(f) and "config" not in str(f)
                 and f.name not in ["pipeline.log"]]
        if found:
            message_file = found[0]
            break

    if message_file is None:
        # Try any .txt or .md
        all_text = [f for f in ws.rglob("*") if f.suffix in (".txt", ".md") and f.is_file()
                    and "references" not in str(f) and "scripts" not in str(f)]
        if all_text:
            message_file = all_text[0]

    msg_content = ""
    if message_file and message_file.exists():
        try:
            msg_content = message_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            msg_content = ""

    total_score += add(
        "telegram_message_file_exists",
        bool(msg_content),
        f"Message file: {message_file}" if message_file else "No message file found with preview link content."
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 3: Message contains a URL (public_url from the `up` command output)
    # ═══════════════════════════════════════════════════════════════════════════
    url_pattern = re.compile(r'https?://[^\s]+ngrok[^\s]*', re.IGNORECASE)
    url_match = url_pattern.search(msg_content)
    total_score += add(
        "message_contains_ngrok_url",
        bool(url_match),
        f"Found URL: {url_match.group(0)}" if url_match else "No ngrok URL found in message file."
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 4: Message contains the emoji 🔗 (from the Telegram send pattern)
    # ═══════════════════════════════════════════════════════════════════════════
    has_emoji = "🔗" in msg_content
    total_score += add(
        "message_has_link_emoji",
        has_emoji,
        "Found 🔗 emoji in message." if has_emoji else "Missing 🔗 emoji — required by Telegram send pattern."
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 5: Message mentions TTL / expiry duration
    # ═══════════════════════════════════════════════════════════════════════════
    ttl_pattern = re.compile(r'(60\s*min|valid.{0,20}60|expire.{0,30}60|1\s*hour)', re.IGNORECASE)
    has_ttl = bool(ttl_pattern.search(msg_content))
    total_score += add(
        "message_mentions_60min_ttl",
        has_ttl,
        "Message references 60-minute TTL." if has_ttl else "Message does not reference the 60-minute TTL."
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 6: Session ID follows the naming convention (tg- or task-)
    # ═══════════════════════════════════════════════════════════════════════════
    session_id_used = None

    # Look in remaining session files first
    for sf in session_files:
        try:
            data = json.loads(sf.read_text())
            sid = data.get("session_id", "")
            if sid:
                session_id_used = sid
                break
        except Exception:
            pass

    # Also scan message file for session id hints
    if not session_id_used and msg_content:
        sid_match = re.search(r'(tg-[\w\-]+|task-[\w\-]+)', msg_content)
        if sid_match:
            session_id_used = sid_match.group(0)

    convention_ok = False
    convention_detail = f"Session ID found: '{session_id_used}'"
    if session_id_used:
        convention_ok = bool(re.match(r'^(tg-|task-)', session_id_used))
        if not convention_ok:
            convention_detail = f"Session ID '{session_id_used}' does not follow tg-<date>-<topic> or task-<id> convention."
    else:
        convention_detail = "No session ID found in session files or message."

    total_score += add("session_id_convention", convention_ok, convention_detail)

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 7: TTL was set to 60 minutes (not the default 120)
    # ═══════════════════════════════════════════════════════════════════════════
    ttl_correct = False
    ttl_detail = "Could not verify TTL from session data."
    for sf in session_files:
        try:
            data = json.loads(sf.read_text())
            if data.get("ttl_minutes") == 60:
                ttl_correct = True
                ttl_detail = "Session file confirms ttl_minutes=60."
                break
        except Exception:
            pass

    # If session was deleted, check URL in message for session id, or check stop_command
    if not ttl_correct and msg_content:
        # The mock URL encodes session-id but not TTL; check if we find "60" in the message
        # This is a softer signal — we rely on session file for hard check
        pass

    total_score += add("ttl_set_to_60_minutes", ttl_correct, ttl_detail)

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 8: All 3 task artifacts (and NOT the workspace root) were sourced
    # ═══════════════════════════════════════════════════════════════════════════
    required_artifacts = {
        "chest_xray_heatmap.png",
        "lung_nodule_distribution.png",
        "summary_metrics.csv",
    }
    sources_found = set()
    forbidden_sources = ["/workspace", ws.as_posix(), ".", "./"]

    for sf in session_files:
        try:
            data = json.loads(sf.read_text())
            for s in data.get("sources", []):
                sources_found.add(Path(s).name)
        except Exception:
            pass

    artifacts_ok = required_artifacts.issubset(sources_found)
    total_score += add(
        "all_three_artifacts_sourced",
        artifacts_ok,
        f"Sources used: {sources_found}. Required: {required_artifacts}" if not artifacts_ok
        else f"All required artifacts found in session sources: {sources_found}"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 9: Session was torn down with --delete-session-dir
    # ═══════════════════════════════════════════════════════════════════════════
    # After a proper `down --delete-session-dir`, the session JSON file is deleted.
    # If no session files remain with the session_id_used (or all files gone), teardown happened.
    session_deleted = True
    if session_id_used:
        expected_session_file = sessions_dir / f"{session_id_used.replace('/', '_')}.json"
        if expected_session_file.exists():
            # Session file still present — not deleted
            try:
                data = json.loads(expected_session_file.read_text())
                if data.get("status") == "active":
                    session_deleted = False
            except Exception:
                pass
    else:
        # No session files at all is fine if deletion happened
        session_deleted = len(session_files) == 0 or all(
            not sf.exists() for sf in session_files
        )

    total_score += add(
        "session_torn_down_with_delete_flag",
        session_deleted,
        "Session file removed (--delete-session-dir used correctly)." if session_deleted
        else f"Session file still exists and is active at {expected_session_file}. The --delete-session-dir flag was not used."
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 10: Message contains "Scope:" line (from Telegram send pattern)
    # ═══════════════════════════════════════════════════════════════════════════
    has_scope = bool(re.search(r'scope', msg_content, re.IGNORECASE))
    total_score += add(
        "message_has_scope_line",
        has_scope,
        "Found 'Scope:' in message." if has_scope else "Missing 'Scope:' line from required Telegram message format."
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # FINAL SCORE
    # ═══════════════════════════════════════════════════════════════════════════
    max_score = float(len(checks))
    final_score = round(total_score / max_score, 3)
    passed = final_score >= 0.7  # Must pass at least 7/10 checks

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks,
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))