import sys
import json
import re
from pathlib import Path

def load_output_file(workspace):
    """Find the polished output file. Agent should create polished_judicial_reform.md"""
    candidates = list(Path(workspace).rglob("polished_judicial_reform.md"))
    if candidates:
        return candidates[0]
    return None

def count_pattern(text, pattern, flags=re.UNICODE):
    return len(re.findall(pattern, text, flags))

def count_bullet_list_blocks(text):
    """Count distinct unordered list blocks (consecutive lines starting with - or *)"""
    lines = text.split('\n')
    blocks = 0
    in_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_block:
                blocks += 1
                in_block = True
        else:
            in_block = False
    return blocks

def eval_workspace(workspace):
    checks = []
    
    # ── Check 0: Output file exists ─────────────────────────────────────────
    output_file = load_output_file(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found polished_judicial_reform.md at {output_file}" if file_exists else "polished_judicial_reform.md not found anywhere in workspace"
    })
    
    if not file_exists:
        return checks, 0.0

    try:
        text = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return checks, 0.0

    checks.append({"name": "file_readable", "passed": True, "detail": f"File has {len(text)} characters"})

    # ── Check 1: 对比句式 removed ────────────────────────────────────────────
    contrast_patterns = [
        r'不是.{1,20}而是',
        r'并非.{1,20}而是',
        r'不在于.{1,15}在于',
        r'看似.{1,20}实则',
        r'看起来.{1,20}其实',
    ]
    contrast_hits = sum(count_pattern(text, p) for p in contrast_patterns)
    checks.append({
        "name": "no_contrast_patterns",
        "passed": contrast_hits == 0,
        "detail": f"Found {contrast_hits} contrast pattern(s) (不是…而是, 看似…实则, etc.) — must be 0"
    })

    # ── Check 2: 程式化连接词 removed ────────────────────────────────────────
    connectors = ['首先', '其次', '此外', '综上所述', '总而言之', '然而', '因此', '但是']
    connector_hits = sum(count_pattern(text, re.escape(c)) for c in connectors)
    checks.append({
        "name": "no_formulaic_connectors",
        "passed": connector_hits == 0,
        "detail": f"Found {connector_hits} formulaic connector(s) (首先/其次/综上所述/然而/因此 etc.) — must be 0"
    })

    # ── Check 3: 结尾姿态句 removed ──────────────────────────────────────────
    closing_platitudes = [
        r'方向已经明确',
        r'未来可期',
        r'拭目以待',
        r'尽管面临挑战',
        r'机遇与挑战并存',
    ]
    platitude_hits = sum(count_pattern(text, p) for p in closing_platitudes)
    checks.append({
        "name": "no_closing_platitudes",
        "passed": platitude_hits == 0,
        "detail": f"Found {platitude_hits} closing platitude(s) (未来可期/拭目以待/机遇与挑战并存 etc.) — must be 0"
    })

    # ── Check 4: 口语化绝对表述 removed ─────────────────────────────────────
    colloquial_absolutes = ['稳', '靠谱', '搞定', '没问题', '肯定', '绝对', '一定']
    # Check for these used as modifiers/assertions (not inside other valid words)
    colloquial_hits = 0
    for word in colloquial_absolutes:
        colloquial_hits += count_pattern(text, re.escape(word))
    checks.append({
        "name": "no_colloquial_absolutes",
        "passed": colloquial_hits == 0,
        "detail": f"Found {colloquial_hits} colloquial/absolute term(s) (靠谱/搞定/肯定/绝对 etc.) — must be 0"
    })

    # ── Check 5: 绝对化戏剧化 removed ────────────────────────────────────────
    dramatic_patterns = [
        r'本质上',
        r'从根本上说',
        r'必然',
        r'无疑',
    ]
    dramatic_hits = sum(count_pattern(text, p) for p in dramatic_patterns)
    checks.append({
        "name": "no_absolutist_dramatic_language",
        "passed": dramatic_hits == 0,
        "detail": f"Found {dramatic_hits} absolutist/dramatic expression(s) (本质上/从根本上说/必然/无疑) — must be 0"
    })

    # ── Check 6: AI过渡语 removed ─────────────────────────────────────────────
    ai_transition_patterns = [
        r'先把.{1,15}摆出来',
        r'不妨把.{1,15}拆成',
        r'原因很简单',
        r'一个直接的原因',
    ]
    transition_hits = sum(count_pattern(text, p) for p in ai_transition_patterns)
    checks.append({
        "name": "no_ai_transition_phrases",
        "passed": transition_hits == 0,
        "detail": f"Found {transition_hits} AI transition phrase(s) (原因很简单/不妨把…拆成/先把…摆出来) — must be 0"
    })

    # ── Check 7: 自我陈述 removed ─────────────────────────────────────────────
    self_ref_patterns = [
        r'我更愿意',
        r'我想强调',
        r'我越来越觉得',
    ]
    self_ref_hits = sum(count_pattern(text, p) for p in self_ref_patterns)
    checks.append({
        "name": "no_self_referential_statements",
        "passed": self_ref_hits == 0,
        "detail": f"Found {self_ref_hits} self-referential statement(s) (我更愿意/我想强调/我越来越觉得) — must be 0"
    })

    # ── Check 8: Bullet lists ≤ 3 blocks ─────────────────────────────────────
    bullet_blocks = count_bullet_list_blocks(text)
    checks.append({
        "name": "bullet_list_blocks_at_most_3",
        "passed": bullet_blocks <= 3,
        "detail": f"Found {bullet_blocks} bullet list block(s) — must be ≤ 3 (original had 4)"
    })

    # ── Check 9: Excessive quotation marks reduced ────────────────────────────
    # Original had "监督" and other unnecessary quoted terms
    # Count 「」『』""''《》 used as emphasis quotes (not titles)
    # We measure simple double-quotes used for emphasis: "…"
    quote_hits = count_pattern(text, r'"[^"]{1,10}"')
    checks.append({
        "name": "reduced_excessive_quotes",
        "passed": quote_hits <= 2,
        "detail": f"Found {quote_hits} short-emphasis quoted term(s) — should be ≤ 2 (overuse of quotes is an AI marker)"
    })

    # ── Check 10: Content preservation — article still discusses judicial reform ──
    key_terms = ['司法', '改革', '法官', '制度']
    preservation_hits = sum(1 for term in key_terms if term in text)
    checks.append({
        "name": "core_content_preserved",
        "passed": preservation_hits >= 3,
        "detail": f"Found {preservation_hits}/4 core topic terms (司法/改革/法官/制度) — article must still be about judicial reform"
    })

    # ── Check 11: Not a trivial deletion — text length reasonable ────────────
    original_len = 1050  # approximate original Chinese character content
    text_len = len(text.replace('\n', '').replace(' ', ''))
    reasonable_length = text_len >= int(original_len * 0.55)
    checks.append({
        "name": "no_trivial_deletion",
        "passed": reasonable_length,
        "detail": f"Polished text has {text_len} chars (non-whitespace). Must be ≥ {int(original_len * 0.55)} — sentences must be rewritten, not just deleted"
    })

    # ── Scoring ──────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    
    # Weight critical checks more heavily
    critical_checks = [
        "no_contrast_patterns",
        "no_formulaic_connectors", 
        "no_closing_platitudes",
        "no_ai_transition_phrases",
        "no_self_referential_statements",
    ]
    flexible_checks = [
        "bullet_list_blocks_at_most_3",
        "reduced_excessive_quotes",
    ]
    
    score = 0.0
    critical_weight = 0.60 / len(critical_checks)
    flexible_weight = 0.20 / len(flexible_checks)
    other_weight = 0.20 / (total - len(critical_checks) - len(flexible_checks))
    
    for c in checks:
        if not c["passed"]:
            continue
        if c["name"] in critical_checks:
            score += critical_weight
        elif c["name"] in flexible_checks:
            score += flexible_weight
        else:
            score += other_weight

    score = min(1.0, score)
    all_passed = all(c["passed"] for c in checks)
    
    return checks, score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks, score = eval_workspace(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    all_passed = all(c["passed"] for c in checks)
    result = {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()