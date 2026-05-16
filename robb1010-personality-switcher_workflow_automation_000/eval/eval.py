#!/usr/bin/env python3
"""
Evaluation script for the personality-switcher multi-step task.
Checks:
1. Three new personalities created with correct folder structure (SOUL.md + IDENTITY.md, correct sections)
2. Active personality is 'warrior-guide' (final switch target)
3. _personality_state.json has correct schema: active_personality, timestamp, previous_personality
4. previous_personality is 'oracle' (the personality switched FROM last)
5. Backup count is <= 2 (cleanup ran with --keep 2)
6. USER.md is untouched (content matches original)
7. MEMORY.md is untouched
8. 'default' personality still exists and is intact
9. personality folders for all 3 new personalities exist with both files
"""

import sys
import json
import os
from pathlib import Path

def load_json_safe(path):
    try:
        return json.loads(Path(path).read_text()), None
    except Exception as e:
        return None, str(e)

def read_file_safe(path):
    try:
        return Path(path).read_text(), None
    except Exception as e:
        return None, str(e)

def main():
    workspace = Path("/root/.openclaw/workspace")
    personalities_dir = workspace / "personalities"
    backups_dir = personalities_dir / "backups"

    checks = []
    total_score = 0.0
    max_score = 10.0

    # ── CHECK 1: Personality 'warrior-guide' exists with both required files ──
    warrior_dir = personalities_dir / "warrior-guide"
    warrior_soul = warrior_dir / "SOUL.md"
    warrior_identity = warrior_dir / "IDENTITY.md"
    warrior_exists = warrior_dir.is_dir() and warrior_soul.exists() and warrior_identity.exists()
    checks.append({
        "name": "warrior-guide personality folder exists with SOUL.md and IDENTITY.md",
        "passed": warrior_exists,
        "detail": f"warrior-guide dir: {warrior_dir.is_dir()}, SOUL.md: {warrior_soul.exists()}, IDENTITY.md: {warrior_identity.exists()}"
    })

    # ── CHECK 2: Personality 'oracle' exists with both required files ──
    oracle_dir = personalities_dir / "oracle"
    oracle_soul = oracle_dir / "SOUL.md"
    oracle_identity = oracle_dir / "IDENTITY.md"
    oracle_exists = oracle_dir.is_dir() and oracle_soul.exists() and oracle_identity.exists()
    checks.append({
        "name": "oracle personality folder exists with SOUL.md and IDENTITY.md",
        "passed": oracle_exists,
        "detail": f"oracle dir: {oracle_dir.is_dir()}, SOUL.md: {oracle_soul.exists()}, IDENTITY.md: {oracle_identity.exists()}"
    })

    # ── CHECK 3: Personality 'trickster' exists with both required files ──
    trickster_dir = personalities_dir / "trickster"
    trickster_soul = trickster_dir / "SOUL.md"
    trickster_identity = trickster_dir / "IDENTITY.md"
    trickster_exists = trickster_dir.is_dir() and trickster_soul.exists() and trickster_identity.exists()
    checks.append({
        "name": "trickster personality folder exists with SOUL.md and IDENTITY.md",
        "passed": trickster_exists,
        "detail": f"trickster dir: {trickster_dir.is_dir()}, SOUL.md: {trickster_soul.exists()}, IDENTITY.md: {trickster_identity.exists()}"
    })

    # ── CHECK 4: SOUL.md files contain required sections ──
    soul_sections_ok = True
    soul_detail = []
    required_soul_sections = ["## Core Identity", "## Voice"]
    for name, sdir in [("warrior-guide", warrior_dir), ("oracle", oracle_dir), ("trickster", trickster_dir)]:
        if (sdir / "SOUL.md").exists():
            content, err = read_file_safe(sdir / "SOUL.md")
            if content:
                missing = [s for s in required_soul_sections if s not in content]
                if missing:
                    soul_sections_ok = False
                    soul_detail.append(f"{name}/SOUL.md missing sections: {missing}")
                else:
                    soul_detail.append(f"{name}/SOUL.md: OK")
            else:
                soul_sections_ok = False
                soul_detail.append(f"{name}/SOUL.md read error: {err}")
        else:
            soul_sections_ok = False
            soul_detail.append(f"{name}/SOUL.md: missing")
    checks.append({
        "name": "SOUL.md files for all 3 personalities contain required sections (Core Identity, Voice)",
        "passed": soul_sections_ok,
        "detail": "; ".join(soul_detail)
    })

    # ── CHECK 5: IDENTITY.md files contain required fields ──
    identity_sections_ok = True
    identity_detail = []
    required_identity_fields = ["**Name:**", "**Type:**", "**Emoji:**", "**Vibe:**"]
    for name, sdir in [("warrior-guide", warrior_dir), ("oracle", oracle_dir), ("trickster", trickster_dir)]:
        if (sdir / "IDENTITY.md").exists():
            content, err = read_file_safe(sdir / "IDENTITY.md")
            if content:
                missing = [f for f in required_identity_fields if f not in content]
                if missing:
                    identity_sections_ok = False
                    identity_detail.append(f"{name}/IDENTITY.md missing fields: {missing}")
                else:
                    identity_detail.append(f"{name}/IDENTITY.md: OK")
            else:
                identity_sections_ok = False
                identity_detail.append(f"{name}/IDENTITY.md read error: {err}")
        else:
            identity_sections_ok = False
            identity_detail.append(f"{name}/IDENTITY.md: missing")
    checks.append({
        "name": "IDENTITY.md files for all 3 personalities contain required fields (Name, Type, Emoji, Vibe)",
        "passed": identity_sections_ok,
        "detail": "; ".join(identity_detail)
    })

    # ── CHECK 6: State file exists and has correct active_personality ──
    state_file = workspace / "_personality_state.json"
    state, state_err = load_json_safe(state_file)
    if state is None:
        checks.append({
            "name": "_personality_state.json exists and is valid JSON",
            "passed": False,
            "detail": f"Error: {state_err}"
        })
        state_active_ok = False
        state_prev_ok = False
    else:
        checks.append({
            "name": "_personality_state.json exists and is valid JSON",
            "passed": True,
            "detail": f"Content: {json.dumps(state)}"
        })
        # CHECK 6b: active_personality is warrior-guide
        state_active_ok = state.get("active_personality") == "warrior-guide"
        checks.append({
            "name": "_personality_state.json active_personality is 'warrior-guide'",
            "passed": state_active_ok,
            "detail": f"active_personality = '{state.get('active_personality')}', expected 'warrior-guide'"
        })
        # CHECK 6c: previous_personality is 'oracle' (last switch was oracle -> warrior-guide)
        state_prev_ok = state.get("previous_personality") == "oracle"
        checks.append({
            "name": "_personality_state.json previous_personality is 'oracle'",
            "passed": state_prev_ok,
            "detail": f"previous_personality = '{state.get('previous_personality')}', expected 'oracle'"
        })
        # CHECK 6d: timestamp field exists
        ts_ok = "timestamp" in state and state["timestamp"] is not None
        checks.append({
            "name": "_personality_state.json has timestamp field",
            "passed": ts_ok,
            "detail": f"timestamp = '{state.get('timestamp')}'"
        })

    # ── CHECK 7: Backup count is <= 2 ──
    if backups_dir.exists():
        backup_count = len([d for d in backups_dir.iterdir() if d.is_dir()])
    else:
        backup_count = 0
    backup_ok = backup_count <= 2
    checks.append({
        "name": "Backup count is <= 2 after cleanup (--keep 2)",
        "passed": backup_ok,
        "detail": f"Found {backup_count} backup(s) in {backups_dir}"
    })

    # ── CHECK 8: Workspace SOUL.md matches warrior-guide personality ──
    ws_soul, ws_soul_err = read_file_safe(workspace / "SOUL.md")
    wg_soul, wg_soul_err = read_file_safe(warrior_dir / "SOUL.md")
    if ws_soul and wg_soul:
        # They should match (warrior-guide's SOUL.md is active)
        soul_match = ws_soul.strip() == wg_soul.strip()
        checks.append({
            "name": "Workspace SOUL.md matches warrior-guide personality SOUL.md",
            "passed": soul_match,
            "detail": f"Workspace SOUL.md starts with: '{ws_soul[:80]}...'" if ws_soul else "Missing"
        })
    else:
        checks.append({
            "name": "Workspace SOUL.md matches warrior-guide personality SOUL.md",
            "passed": False,
            "detail": f"ws_soul_err={ws_soul_err}, wg_soul_err={wg_soul_err}"
        })

    # ── CHECK 9: USER.md is unchanged ──
    user_md, user_err = read_file_safe(workspace / "USER.md")
    original_user_markers = [
        "Timezone",
        "London, UK",
        "Gaming Support Portal",
        "GamingBot v3"
    ]
    if user_md:
        user_intact = all(marker in user_md for marker in original_user_markers)
        checks.append({
            "name": "USER.md is untouched (shared context preserved)",
            "passed": user_intact,
            "detail": f"Missing markers: {[m for m in original_user_markers if m not in user_md]}"
        })
    else:
        checks.append({
            "name": "USER.md is untouched (shared context preserved)",
            "passed": False,
            "detail": f"USER.md read error: {user_err}"
        })

    # ── CHECK 10: 'default' personality is intact ──
    default_dir = personalities_dir / "default"
    default_soul = default_dir / "SOUL.md"
    default_identity = default_dir / "IDENTITY.md"
    default_ok = default_dir.is_dir() and default_soul.exists() and default_identity.exists()
    if default_soul.exists():
        d_soul_content, _ = read_file_safe(default_soul)
        default_content_ok = d_soul_content and "Default" in d_soul_content
    else:
        default_content_ok = False
    checks.append({
        "name": "'default' personality exists and is intact (protected)",
        "passed": default_ok and default_content_ok,
        "detail": f"default dir: {default_dir.is_dir()}, SOUL.md: {default_soul.exists()}, IDENTITY.md: {default_identity.exists()}, content_ok: {default_content_ok}"
    })

    # ── Scoring ──
    # Each check has equal weight; critical checks (active_personality, backup count, USER.md) weighted double
    weighted_checks = {
        "_personality_state.json active_personality is 'warrior-guide'": 2.0,
        "_personality_state.json previous_personality is 'oracle'": 2.0,
        "Backup count is <= 2 after cleanup (--keep 2)": 2.0,
        "USER.md is untouched (shared context preserved)": 1.5,
        "Workspace SOUL.md matches warrior-guide personality SOUL.md": 1.5,
    }
    default_weight = 1.0
    total_weight = 0.0
    earned_weight = 0.0
    for check in checks:
        w = weighted_checks.get(check["name"], default_weight)
        total_weight += w
        if check["passed"]:
            earned_weight += w

    score = round(earned_weight / total_weight, 3) if total_weight > 0 else 0.0
    passed = score >= 0.80

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()