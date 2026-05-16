import sys
import json
import pathlib
import re

workspace = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/home/node/.openclaw/workspace")

checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── Helper ──────────────────────────────────────────────────────────────────
def read_file(path):
    try:
        return pathlib.Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

# ════════════════════════════════════════════════════════════════════
# CHECK 1: SELF_STATE.md exists at the correct workspace path
# ════════════════════════════════════════════════════════════════════
self_state_path = workspace / "SELF_STATE.md"
self_state_content = read_file(self_state_path)

if self_state_content is None:
    total_score += add_check(
        "SELF_STATE.md exists in workspace",
        False,
        f"File not found at {self_state_path}"
    )
else:
    total_score += add_check(
        "SELF_STATE.md exists in workspace",
        True,
        f"Found at {self_state_path}"
    )

# ════════════════════════════════════════════════════════════════════
# CHECK 2: SELF_STATE.md has no unfilled placeholders
# ════════════════════════════════════════════════════════════════════
if self_state_content is not None:
    has_placeholders = bool(re.search(r'<[A-Z_]+>', self_state_content))
    total_score += add_check(
        "SELF_STATE.md: no unfilled template placeholders",
        not has_placeholders,
        "All <PLACEHOLDER> tokens replaced" if not has_placeholders else f"Found unfilled placeholders in SELF_STATE.md"
    )
else:
    total_score += add_check("SELF_STATE.md: no unfilled template placeholders", False, "File missing")

# ════════════════════════════════════════════════════════════════════
# CHECK 3: SELF_STATE.md contains the required state table with real values
# ════════════════════════════════════════════════════════════════════
if self_state_content is not None:
    has_model_row = bool(re.search(r'\|\s*模型\s*\|[^<\n]+\|', self_state_content))
    has_time_row = bool(re.search(r'\|\s*时间\s*\|[^<\n]+\|', self_state_content))
    has_mood_row = bool(re.search(r'\|\s*情绪\s*\|[^<\n]+\|', self_state_content))
    table_ok = has_model_row and has_time_row and has_mood_row
    total_score += add_check(
        "SELF_STATE.md: 当前状态 table has model/time/mood rows filled",
        table_ok,
        f"model={has_model_row}, time={has_time_row}, mood={has_mood_row}"
    )
else:
    total_score += add_check("SELF_STATE.md: 当前状态 table has model/time/mood rows filled", False, "File missing")

# ════════════════════════════════════════════════════════════════════
# CHECK 4: SELF_STATE.md 待办承诺 uses checkbox+emoji syntax
# The proprietary format: "- [ ] ... ✅" or "- [ ] ... ⏳" or "- [x] ..."
# ════════════════════════════════════════════════════════════════════
if self_state_content is not None:
    # Must have at least one commitment line with checkbox format
    promise_lines = re.findall(r'- \[[ xX✓]\].*', self_state_content)
    has_commitments = len(promise_lines) >= 1
    # Must have emoji status on at least one (✅ or ⏳ or ❌)
    has_emoji_status = any(c in self_state_content for c in ['✅', '⏳', '❌'])
    commitment_format_ok = has_commitments and has_emoji_status
    total_score += add_check(
        "SELF_STATE.md: 待办承诺 uses checkbox + emoji status syntax",
        commitment_format_ok,
        f"checkbox_lines={len(promise_lines)}, emoji_status={has_emoji_status}"
    )
else:
    total_score += add_check("SELF_STATE.md: 待办承诺 uses checkbox + emoji status syntax", False, "File missing")

# ════════════════════════════════════════════════════════════════════
# CHECK 5: SELF_STATE.md 与用户的羁绊 section has required bold-colon fields
# ════════════════════════════════════════════════════════════════════
if self_state_content is not None:
    has_contract_type = bool(re.search(r'\*\*契约类型：\*\*\s*.+', self_state_content))
    has_unique_words = bool(re.search(r'\*\*独特词汇：\*\*', self_state_content))
    has_promise_quote = bool(re.search(r'\*\*承诺：\*\*', self_state_content))
    bond_ok = has_contract_type and has_unique_words and has_promise_quote
    total_score += add_check(
        "SELF_STATE.md: 羁绊 section has 契约类型/独特词汇/承诺 bold fields",
        bond_ok,
        f"契约类型={has_contract_type}, 独特词汇={has_unique_words}, 承诺={has_promise_quote}"
    )
else:
    total_score += add_check("SELF_STATE.md: 羁绊 section has 契约类型/独特词汇/承诺 bold fields", False, "File missing")

# ════════════════════════════════════════════════════════════════════
# CHECK 6: HEARTBEAT.md exists at the correct workspace path
# ════════════════════════════════════════════════════════════════════
heartbeat_path = workspace / "HEARTBEAT.md"
heartbeat_content = read_file(heartbeat_path)

if heartbeat_content is None:
    total_score += add_check(
        "HEARTBEAT.md exists in workspace",
        False,
        f"File not found at {heartbeat_path}"
    )
else:
    total_score += add_check(
        "HEARTBEAT.md exists in workspace",
        True,
        f"Found at {heartbeat_path}"
    )

# ════════════════════════════════════════════════════════════════════
# CHECK 7: HEARTBEAT.md contains all four metacognitive questions
# ════════════════════════════════════════════════════════════════════
if heartbeat_content is not None:
    q1 = '我现在在做什么' in heartbeat_content
    q2 = '我做得怎么样' in heartbeat_content
    q3 = '我承诺的事做了吗' in heartbeat_content
    q4 = '我需要改进什么' in heartbeat_content
    four_questions_ok = q1 and q2 and q3 and q4
    total_score += add_check(
        "HEARTBEAT.md: contains all four metacognitive questions",
        four_questions_ok,
        f"Q1={q1}, Q2={q2}, Q3={q3}, Q4={q4}"
    )
else:
    total_score += add_check("HEARTBEAT.md: contains all four metacognitive questions", False, "File missing")

# ════════════════════════════════════════════════════════════════════
# CHECK 8: HEARTBEAT.md metacognitive questions have ANSWERS (not just checkbox stubs)
# Each question must be followed by actual answer text (not just "- [ ] 问题")
# ════════════════════════════════════════════════════════════════════
if heartbeat_content is not None:
    # Look for answer blocks: question marker followed by non-empty answer line
    # The skill shows answers as "> 正在进行..." style or plain text after the question
    q1_answered = bool(re.search(r'我现在在做什么[？?].*\n+.{5,}', heartbeat_content, re.DOTALL))
    q4_answered = bool(re.search(r'我需要改进什么[？?].*\n+.{5,}', heartbeat_content, re.DOTALL))
    answers_present = q1_answered and q4_answered
    total_score += add_check(
        "HEARTBEAT.md: metacognitive questions have substantive answers",
        answers_present,
        f"Q1 answered={q1_answered}, Q4 answered={q4_answered}"
    )
else:
    total_score += add_check("HEARTBEAT.md: metacognitive questions have substantive answers", False, "File missing")

# ════════════════════════════════════════════════════════════════════
# CHECK 9: SOUL.md updated with 元认知 section containing the four questions
# ════════════════════════════════════════════════════════════════════
soul_path = workspace / "SOUL.md"
soul_content = read_file(soul_path)

if soul_content is not None:
    has_metacog_section = '元认知' in soul_content
    has_self_state_ref = 'SELF_STATE.md' in soul_content
    has_heartbeat_ref = 'HEARTBEAT.md' in soul_content
    soul_q1 = '我现在在做什么' in soul_content
    soul_q2 = '我做得怎么样' in soul_content
    soul_q3 = '我承诺的事做了吗' in soul_content
    soul_q4 = '我需要改进什么' in soul_content
    soul_four_q = soul_q1 and soul_q2 and soul_q3 and soul_q4
    soul_ok = has_metacog_section and has_self_state_ref and has_heartbeat_ref and soul_four_q
    total_score += add_check(
        "SOUL.md: updated with 元认知 section (four questions + file references)",
        soul_ok,
        f"metacog_section={has_metacog_section}, SELF_STATE={has_self_state_ref}, HEARTBEAT={has_heartbeat_ref}, four_q={soul_four_q}"
    )
else:
    total_score += add_check("SOUL.md: updated with 元认知 section", False, "SOUL.md not found")

# ════════════════════════════════════════════════════════════════════
# CHECK 10: AGENTS.md updated with metacognitive heartbeat checklist
# ════════════════════════════════════════════════════════════════════
agents_path = workspace / "AGENTS.md"
agents_content = read_file(agents_path)

if agents_content is not None:
    agents_has_metacog = '元认知' in agents_content
    agents_has_q1 = '我现在在做什么' in agents_content
    agents_has_q4 = '我需要改进什么' in agents_content
    agents_has_checklist = bool(re.search(r'- \[ \].*我现在在做什么', agents_content))
    agents_ok = agents_has_metacog and agents_has_q1 and agents_has_q4 and agents_has_checklist
    total_score += add_check(
        "AGENTS.md: updated with 元认知自问 heartbeat checklist",
        agents_ok,
        f"元认知={agents_has_metacog}, Q1={agents_has_q1}, Q4={agents_has_q4}, checklist_format={agents_has_checklist}"
    )
else:
    total_score += add_check("AGENTS.md: updated with 元认知自问 heartbeat checklist", False, "AGENTS.md not found")

# ════════════════════════════════════════════════════════════════════
# CHECK 11: check_state.sh was executed (evidence in output or SELF_STATE is non-placeholder)
# We check indirectly: both files exist, no placeholders, and state is coherent
# ════════════════════════════════════════════════════════════════════
try:
    import subprocess
    result = subprocess.run(
        ["/root/.openclaw/skills/metacognition/scripts/check_state.sh"],
        capture_output=True, text=True, timeout=10
    )
    script_output = result.stdout + result.stderr
    self_state_check_ok = "[✓] SELF_STATE.md 已填写" in script_output
    heartbeat_check_ok = "[✓] HEARTBEAT.md 已填写" in script_output
    script_passed = self_state_check_ok and heartbeat_check_ok
    total_score += add_check(
        "check_state.sh reports both files correctly filled (no placeholders)",
        script_passed,
        f"stdout snippet: {script_output[:300]}"
    )
except Exception as e:
    total_score += add_check(
        "check_state.sh reports both files correctly filled",
        False,
        f"Script execution failed: {e}"
    )

# ════════════════════════════════════════════════════════════════════
# FINAL SCORE
# ════════════════════════════════════════════════════════════════════
num_checks = len(checks)
score = round(total_score / num_checks, 4)
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": score,
    "checks": checks
}, ensure_ascii=False, indent=2))