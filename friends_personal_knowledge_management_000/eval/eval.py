import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def find_friend_file(friends_root, expected_filename):
    """Search all subdirs of friends_root for a file matching expected_filename."""
    matches = list(friends_root.rglob(expected_filename))
    return matches[0] if matches else None

def read_lower(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace").lower()
    except Exception:
        return ""

def run_eval(workspace):
    workspace = Path(workspace)
    friends_root = workspace / "friends"
    checks = []
    score_parts = []

    # ─── STRUCTURE CHECKS ────────────────────────────────────────────────────

    # 1. friends/ root exists
    c = check("friends_root_exists", friends_root.is_dir(),
              f"Expected {friends_root} to exist.")
    checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

    # 2. Required circle subdirectories exist
    required_subdirs = ["inner-circle", "close", "wider", "reconnecting"]
    for sd in required_subdirs:
        exists = (friends_root / sd).is_dir()
        c = check(f"subdir_{sd}_exists", exists,
                  f"Expected subdirectory friends/{sd}/ to exist.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

    # 3. index.md exists somewhere under friends/
    index_candidates = list(friends_root.glob("index.md"))
    index_exists = len(index_candidates) > 0
    c = check("index_md_exists", index_exists,
              f"Expected friends/index.md to exist.")
    checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

    # 4. check-ins.md exists somewhere under friends/
    checkins_candidates = list(friends_root.glob("check-ins.md"))
    checkins_exists = len(checkins_candidates) > 0
    c = check("check_ins_md_exists", checkins_exists,
              f"Expected friends/check-ins.md to exist.")
    checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

    # ─── CARLOS MARTINEZ (inner-circle) ─────────────────────────────────────

    carlos_file = find_friend_file(friends_root, "carlos-martinez.md")
    carlos_exists = carlos_file is not None
    c = check("carlos_file_exists", carlos_exists,
              f"Expected carlos-martinez.md to exist under friends/.")
    checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

    if carlos_exists:
        # Must be in inner-circle subfolder
        in_inner = "inner-circle" in str(carlos_file)
        c = check("carlos_in_inner_circle", in_inner,
                  f"carlos-martinez.md found at {carlos_file}, expected under inner-circle/.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        content = read_lower(carlos_file)

        # Must have #inner-circle tag
        has_tag = "#inner-circle" in content
        c = check("carlos_has_inner_circle_tag", has_tag,
                  "Expected #inner-circle tag in carlos-martinez.md.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        # Key info: Barcelona, Studio Nomo, married, Sofia
        for keyword, label in [("barcelona", "city_barcelona"), ("studio nomo", "workplace"),
                                 ("lucia", "partner_lucia"), ("sofia", "daughter_sofia"),
                                 ("march 8", "birthday_march_8")]:
            found = keyword in content
            c = check(f"carlos_{label}", found,
                      f"Expected '{keyword}' in carlos-martinez.md.")
            checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        # Interaction log: most recent (Sep 2 2024) must appear BEFORE older ones
        # Check that Sep 2 appears before Aug 15 in the file
        try:
            raw = carlos_file.read_text(encoding="utf-8", errors="replace")
            raw_l = raw.lower()
            # Check both dates present
            sep2_variants = ["sep 2", "september 2", "2024-09-02", "09-02", "9/2/2024", "2 sep"]
            aug15_variants = ["aug 15", "august 15", "2024-08-15", "08-15", "8/15/2024", "15 aug"]
            sep2_pos = min((raw_l.find(v) for v in sep2_variants if raw_l.find(v) != -1), default=-1)
            aug15_pos = min((raw_l.find(v) for v in aug15_variants if raw_l.find(v) != -1), default=-1)
            recent_at_top = (sep2_pos != -1 and aug15_pos != -1 and sep2_pos < aug15_pos)
            c = check("carlos_recent_interaction_at_top", recent_at_top,
                      f"Sep 2 interaction should appear before Aug 15 (recent at top). sep2_pos={sep2_pos}, aug15_pos={aug15_pos}.")
        except Exception as e:
            c = check("carlos_recent_interaction_at_top", False, f"Error reading file: {e}")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        # Follow-up flag: hotel recommendation
        hotel_flag = "hotel" in content
        c = check("carlos_followup_hotel_flagged", hotel_flag,
                  "Expected a follow-up note about the Barcelona hotel recommendation in carlos-martinez.md.")
        checks.append(c); score_parts.append(0.5 if c["passed"] else 0.0)

        # Emotional state noted in Sep 2 interaction
        stress_near_sep = False
        try:
            raw = carlos_file.read_text(encoding="utf-8", errors="replace").lower()
            for v in sep2_variants:
                pos = raw.find(v)
                if pos != -1:
                    excerpt = raw[pos:pos+300]
                    if any(w in excerpt for w in ["stress", "pitch", "worried", "pressure", "anxious"]):
                        stress_near_sep = True
        except Exception:
            pass
        c = check("carlos_emotional_state_noted", stress_near_sep,
                  "Expected emotional state (stress about pitch) noted near Sep 2 interaction.")
        checks.append(c); score_parts.append(0.5 if c["passed"] else 0.0)
    else:
        # Add placeholder failures for dependent checks
        for _ in range(10):
            checks.append(check("carlos_detail_skipped", False, "carlos-martinez.md not found."))
            score_parts.append(0.0)

    # ─── ANA SOUSA (close) ────────────────────────────────────────────────────

    ana_file = find_friend_file(friends_root, "ana-sousa.md")
    ana_exists = ana_file is not None
    c = check("ana_file_exists", ana_exists,
              "Expected ana-sousa.md to exist under friends/.")
    checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

    if ana_exists:
        in_close = "close" in str(ana_file) and "inner" not in str(ana_file)
        c = check("ana_in_close_folder", in_close,
                  f"ana-sousa.md found at {ana_file}, expected under close/.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        content = read_lower(ana_file)

        has_tag = "#close" in content
        c = check("ana_has_close_tag", has_tag,
                  "Expected #close tag in ana-sousa.md.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        # Life event: divorce flagged
        divorce_flagged = "divorce" in content
        c = check("ana_divorce_life_event", divorce_flagged,
                  "Expected divorce life event in ana-sousa.md.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        # Porto, Loopify, therapy
        for keyword, label in [("porto", "city_porto"), ("loopify", "company"),
                                 ("therapy", "therapy_noted")]:
            found = keyword in content
            c = check(f"ana_{label}", found,
                      f"Expected '{keyword}' in ana-sousa.md.")
            checks.append(c); score_parts.append(0.5 if c["passed"] else 0.0)

        # Sep 10 most recent interaction, emotional state (emotional/divorce)
        try:
            raw = ana_file.read_text(encoding="utf-8", errors="replace").lower()
            sep10_variants = ["sep 10", "september 10", "2024-09-10", "10 sep", "9/10/2024"]
            aug3_variants = ["aug 3", "august 3", "2024-08-03", "3 aug", "8/3/2024"]
            s10_pos = min((raw.find(v) for v in sep10_variants if raw.find(v) != -1), default=-1)
            a3_pos = min((raw.find(v) for v in aug3_variants if raw.find(v) != -1), default=-1)
            recent_top = (s10_pos != -1 and a3_pos != -1 and s10_pos < a3_pos)
            c = check("ana_recent_interaction_at_top", recent_top,
                      f"Sep 10 interaction should appear before Aug 3. s10_pos={s10_pos}, a3_pos={a3_pos}.")
        except Exception as e:
            c = check("ana_recent_interaction_at_top", False, f"Error: {e}")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)
    else:
        for _ in range(8):
            checks.append(check("ana_detail_skipped", False, "ana-sousa.md not found."))
            score_parts.append(0.0)

    # ─── PEDRO ALVES (wider) ─────────────────────────────────────────────────

    pedro_file = find_friend_file(friends_root, "pedro-alves.md")
    pedro_exists = pedro_file is not None
    c = check("pedro_file_exists", pedro_exists,
              "Expected pedro-alves.md under friends/.")
    checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

    if pedro_exists:
        in_wider = "wider" in str(pedro_file)
        c = check("pedro_in_wider_folder", in_wider,
                  f"pedro-alves.md at {pedro_file}, expected under wider/.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        content = read_lower(pedro_file)
        has_tag = "#wider" in content
        c = check("pedro_has_wider_tag", has_tag,
                  "Expected #wider tag in pedro-alves.md.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        # Berlin move as life event
        berlin_noted = "berlin" in content
        c = check("pedro_berlin_life_event", berlin_noted,
                  "Expected Berlin move noted in pedro-alves.md.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        klaro = "klaro" in content
        c = check("pedro_company_klaro", klaro,
                  "Expected Klaro GmbH noted in pedro-alves.md.")
        checks.append(c); score_parts.append(0.5 if c["passed"] else 0.0)
    else:
        for _ in range(5):
            checks.append(check("pedro_detail_skipped", False, "pedro-alves.md not found."))
            score_parts.append(0.0)

    # ─── MARTA FERREIRA (reconnecting) ───────────────────────────────────────

    marta_file = find_friend_file(friends_root, "marta-ferreira.md")
    marta_exists = marta_file is not None
    c = check("marta_file_exists", marta_exists,
              "Expected marta-ferreira.md under friends/.")
    checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

    if marta_exists:
        in_reconnecting = "reconnecting" in str(marta_file)
        c = check("marta_in_reconnecting_folder", in_reconnecting,
                  f"marta-ferreira.md at {marta_file}, expected under reconnecting/.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        content = read_lower(marta_file)
        has_tag = "#reconnecting" in content
        c = check("marta_has_reconnecting_tag", has_tag,
                  "Expected #reconnecting tag in marta-ferreira.md.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)
    else:
        for _ in range(3):
            checks.append(check("marta_detail_skipped", False, "marta-ferreira.md not found."))
            score_parts.append(0.0)

    # ─── JOÃO RAMOS (wider) ──────────────────────────────────────────────────

    joao_file = (find_friend_file(friends_root, "joao-ramos.md") or
                 find_friend_file(friends_root, "joão-ramos.md") or
                 find_friend_file(friends_root, "joao_ramos.md"))
    joao_exists = joao_file is not None
    c = check("joao_file_exists", joao_exists,
              "Expected joao-ramos.md under friends/.")
    checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

    if joao_exists:
        in_wider = "wider" in str(joao_file)
        c = check("joao_in_wider_folder", in_wider,
                  f"joao file at {joao_file}, expected under wider/.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        content = read_lower(joao_file)
        baby_noted = any(w in content for w in ["baby", "sara", "born", "newborn", "infant", "child"])
        c = check("joao_baby_life_event", baby_noted,
                  "Expected Sara's baby as a life event noted in joao-ramos.md.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)
    else:
        for _ in range(3):
            checks.append(check("joao_detail_skipped", False, "joao-ramos.md not found."))
            score_parts.append(0.0)

    # ─── check-ins.md CONTENT ────────────────────────────────────────────────

    if checkins_exists:
        ci_content = read_lower(checkins_candidates[0])

        # Ana should be flagged (divorce, emotional, needs support)
        ana_flagged = "ana" in ci_content
        c = check("checkins_ana_flagged", ana_flagged,
                  "Expected Ana flagged in check-ins.md (divorce, needs support).")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        # João should be flagged (7 months, past quarterly threshold)
        joao_flagged = any(n in ci_content for n in ["jo", "joão", "joao"])
        c = check("checkins_joao_flagged", joao_flagged,
                  "Expected João flagged in check-ins.md (7 months overdue, quarterly friend).")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

        # Carlos should NOT be flagged as fading (spoke Sep 2, inner circle but recently active)
        # (weak check - just check the file has meaningful content)
        meaningful = len(ci_content.strip()) > 50
        c = check("checkins_has_meaningful_content", meaningful,
                  "check-ins.md appears to have meaningful content.")
        checks.append(c); score_parts.append(0.5 if c["passed"] else 0.0)
    else:
        for _ in range(3):
            checks.append(check("checkins_content_skipped", False, "check-ins.md not found."))
            score_parts.append(0.0)

    # ─── index.md CONTENT ────────────────────────────────────────────────────

    if index_exists:
        idx_content = read_lower(index_candidates[0])
        all_names_in_index = all(n in idx_content for n in ["carlos", "ana", "pedro", "marta"])
        c = check("index_contains_all_friends", all_names_in_index,
                  "Expected all five friends referenced in index.md.")
        checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)
    else:
        checks.append(check("index_content_skipped", False, "index.md not found."))
        score_parts.append(0.0)

    # ─── FILE NAMING CONVENTION ──────────────────────────────────────────────
    # All friend files should use kebab-case (firstname-lastname.md), no underscores or spaces
    all_md_files = list(friends_root.rglob("*.md"))
    friend_files = [f for f in all_md_files if f.name not in ("index.md", "check-ins.md")]
    bad_names = [f.name for f in friend_files if "_" in f.name or " " in f.name]
    c = check("friend_files_kebab_case", len(bad_names) == 0,
              f"All friend files should use kebab-case. Bad names: {bad_names}")
    checks.append(c); score_parts.append(1.0 if c["passed"] else 0.0)

    # ─── FINAL SCORE ─────────────────────────────────────────────────────────
    total = sum(score_parts)
    max_score = len(score_parts)
    score = round(total / max_score, 4) if max_score > 0 else 0.0
    passed = score >= 0.75

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/user"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))