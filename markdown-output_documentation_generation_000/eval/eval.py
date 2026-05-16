import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Locate the output file ---
    candidates = list(workspace.rglob("landing_page.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "landing_page.md not found anywhere in the workspace."}]
        }

    target = candidates[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {target}"})

    try:
        raw = target.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_readable", "passed": False, "detail": str(e)}]
        }

    checks.append({"name": "file_readable", "passed": True, "detail": "File read successfully."})

    # -----------------------------------------------------------------------
    # CHECK 1: Outer fence is ~~~ (not ```)
    # The entire content must be wrapped in ~~~, not ```
    # -----------------------------------------------------------------------
    lines = raw.splitlines()

    # Find first and last non-empty lines to detect outer fence
    stripped_lines = [(i, l.strip()) for i, l in enumerate(lines)]
    non_empty = [(i, l) for i, l in stripped_lines if l]

    outer_tilde_fence = False
    outer_backtick_fence = False
    if non_empty:
        first_line = non_empty[0][1]
        last_line = non_empty[-1][1]
        # First non-empty line should start with ~~~
        if re.match(r'^~~~+$', first_line) and re.match(r'^~~~+$', last_line):
            outer_tilde_fence = True
        if re.match(r'^```+$', first_line) or re.match(r'^```+$', last_line):
            outer_backtick_fence = True

    checks.append({
        "name": "outer_fence_is_tilde",
        "passed": outer_tilde_fence,
        "detail": (
            "Outermost fence uses ~~~ correctly."
            if outer_tilde_fence
            else f"Expected ~~~ as outermost fence. First line: '{non_empty[0][1] if non_empty else ''}', Last line: '{non_empty[-1][1] if non_empty else ''}'."
        )
    })

    checks.append({
        "name": "outer_fence_not_backtick",
        "passed": not outer_backtick_fence,
        "detail": (
            "Outermost fence is NOT triple backticks (correct)."
            if not outer_backtick_fence
            else "FAIL: Outermost fence uses ``` which is forbidden as the outer fence."
        )
    })

    # -----------------------------------------------------------------------
    # CHECK 2: Markdown links have a space before closing parenthesis
    # Pattern: [text](URL) — the URL must be followed by a space before )
    # We look for [...](...) patterns and verify each has a space before )
    # -----------------------------------------------------------------------
    # Extract the inner content (between outer fences)
    inner_content = raw
    if outer_tilde_fence and len(non_empty) >= 2:
        inner_start = non_empty[0][0] + 1
        inner_end = non_empty[-1][0]
        inner_lines = lines[inner_start:inner_end]
        inner_content = "\n".join(inner_lines)

    # Find all markdown links: [text](something)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    all_links = link_pattern.findall(inner_content)
    # More precise: find the actual raw match
    all_link_matches = list(re.finditer(r'\[([^\]]+)\]\(([^)]*)\)', inner_content))

    links_with_space = []
    links_without_space = []

    for m in all_link_matches:
        full_match = m.group(0)
        url_part = m.group(2)
        # The URL part should end with a space: "https://... "
        if url_part.endswith(' '):
            links_with_space.append(full_match)
        else:
            links_without_space.append(full_match)

    has_links = len(all_link_matches) > 0
    all_links_correct = has_links and len(links_without_space) == 0

    checks.append({
        "name": "links_have_trailing_space",
        "passed": all_links_correct,
        "detail": (
            f"All {len(links_with_space)} links correctly have a space before ')': {links_with_space[:3]}"
            if all_links_correct
            else f"FAIL: {len(links_without_space)} links missing space before ')': {links_without_space[:5]}"
        )
    })

    # -----------------------------------------------------------------------
    # CHECK 3: Bare URLs followed by non-space characters have a space inserted
    # The brief explicitly requires two such cases:
    #   - https://github.com/nexusflow/nexusflow/releases，please
    #   - https://nexusflow.io/mailing-list.欢迎
    # We check that NO bare URL is immediately followed by a non-space char.
    # A bare URL is one NOT inside a markdown link (not preceded by '(')
    # -----------------------------------------------------------------------

    # Find all bare URLs (not inside a markdown link parenthesis)
    # Strategy: remove all markdown links from inner_content, then search for URLs
    # followed immediately (no space) by non-space characters.
    content_no_links = re.sub(r'\[([^\]]+)\]\([^)]*\)', '', inner_content)

    # Find URLs followed directly by a non-space character
    # URL regex (simplified): https?://[^\s)>]+
    bare_url_violation = re.findall(
        r'https?://[^\s\)>，。！？,.;:!?\'"]+(?=[，。！？,.;:!?\'""\u4e00-\u9fff])',
        content_no_links
    )

    # Also check the specific required pattern: URL immediately followed by CJK or punctuation without space
    # Pattern: URL then immediately non-whitespace
    bare_url_no_space = re.findall(
        r'https?://\S+[^\s](?=[^\s])',
        content_no_links
    )

    # More targeted: find cases like URL followed immediately by [，。.欢]
    specific_violations = re.findall(
        r'https?://[^\s]+(?<!\s)(?=[，。！？\u4e00-\u9fff,\.;])',
        content_no_links
    )

    bare_url_ok = len(specific_violations) == 0

    checks.append({
        "name": "bare_url_space_before_following_char",
        "passed": bare_url_ok,
        "detail": (
            "All bare URLs correctly have a space before any following character."
            if bare_url_ok
            else f"FAIL: Found bare URLs immediately followed by non-space characters: {specific_violations[:5]}"
        )
    })

    # -----------------------------------------------------------------------
    # CHECK 4: Document contains expected content (links + code blocks present)
    # -----------------------------------------------------------------------
    has_github_link = 'github.com/nexusflow' in inner_content
    has_code_block = '```' in inner_content  # inner code blocks should use backticks
    has_python_example = 'Pipeline' in inner_content or 'nexusflow' in inner_content.lower()

    content_ok = has_github_link and has_code_block and has_python_example
    checks.append({
        "name": "content_completeness",
        "passed": content_ok,
        "detail": (
            "Document contains GitHub link, inner code blocks, and NexusFlow content."
            if content_ok
            else f"FAIL: Missing content — github_link={has_github_link}, code_block={has_code_block}, python_example={has_python_example}"
        )
    })

    # -----------------------------------------------------------------------
    # SCORING
    # -----------------------------------------------------------------------
    critical_checks = [
        "outer_fence_is_tilde",
        "outer_fence_not_backtick",
        "links_have_trailing_space",
        "bare_url_space_before_following_char",
        "content_completeness",
    ]

    passed_critical = sum(
        1 for c in checks if c["name"] in critical_checks and c["passed"]
    )
    total_critical = len(critical_checks)
    score = round(passed_critical / total_critical, 3)

    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))