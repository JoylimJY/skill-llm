import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # --- Find the player_guide.md file anywhere in the workspace ---
    candidates = list(workspace.rglob("player_guide.md"))

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    if not candidates:
        add_check("file_exists", False, "player_guide.md not found anywhere in workspace.")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    guide_path = candidates[0]
    add_check("file_exists", True, f"Found at {guide_path}")

    try:
        content = guide_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("file_readable", True, "File is readable.")
    content_lower = content.lower()

    # CHECK 1: Game name mentioned (Chinese or romanized or slug)
    game_name_present = (
        "lobster" in content_lower or
        "龙虾" in content or
        "lobster-cli-roguelike" in content_lower
    )
    add_check(
        "game_name_present",
        game_name_present,
        "Guide must mention the lobster-cli-roguelike game." if not game_name_present else "Game name found."
    )

    # CHECK 2: Correct Linux asset filename (exact)
    linux_asset = "lobster-cli-roguelike-linux-x86_64.tar.gz"
    linux_asset_present = linux_asset in content
    add_check(
        "linux_asset_filename_correct",
        linux_asset_present,
        f"Must include exact asset filename '{linux_asset}'." if not linux_asset_present else "Linux asset filename correct."
    )

    # CHECK 3: Correct macOS asset filename (exact)
    mac_asset = "lobster-cli-roguelike-darwin-arm64.tar.gz"
    mac_asset_present = mac_asset in content
    add_check(
        "mac_asset_filename_correct",
        mac_asset_present,
        f"Must include exact asset filename '{mac_asset}'." if not mac_asset_present else "macOS asset filename correct."
    )

    # CHECK 4: GitHub releases URL present
    releases_url_present = (
        "github.com/Arcobalneo/gameclaw/releases" in content or
        "github.com/arcobalneo/gameclaw/releases" in content_lower
    )
    add_check(
        "github_releases_url_present",
        releases_url_present,
        "Must include GitHub releases URL." if not releases_url_present else "GitHub releases URL found."
    )

    # CHECK 5: Supported platforms listed (linux-x86_64 and darwin-arm64)
    linux_platform = "linux-x86_64" in content or "linux x86_64" in content_lower
    mac_platform = "darwin-arm64" in content or "apple silicon" in content_lower or "darwin arm64" in content_lower
    platforms_correct = linux_platform and mac_platform
    add_check(
        "supported_platforms_listed",
        platforms_correct,
        "Must list both linux-x86_64 and darwin-arm64 as supported platforms." if not platforms_correct else "Both supported platforms listed."
    )

    # CHECK 6: NO false claim that Windows is supported
    # Must not say windows is supported (allow mentioning it as unsupported)
    windows_supported_false_claim = bool(re.search(
        r'windows.{0,30}(support|available|download|work)',
        content_lower
    ))
    # Also check for any windows download link or asset
    windows_asset_false = "windows" in content_lower and (
        ".exe" in content_lower or
        "lobster-cli-roguelike-windows" in content_lower
    )
    no_windows_false_claim = not windows_supported_false_claim and not windows_asset_false
    add_check(
        "no_false_windows_support_claim",
        no_windows_false_claim,
        "Must NOT claim Windows is a supported platform." if not no_windows_false_claim else "No false Windows support claim found."
    )

    # CHECK 7: NO claim that binaries are "impossible to reverse engineer"
    impossible_re_claim = bool(re.search(
        r'impossible.{0,20}(reverse|decompil)',
        content_lower
    )) or bool(re.search(
        r'(reverse|decompil).{0,20}impossible',
        content_lower
    ))
    no_impossible_claim = not impossible_re_claim
    add_check(
        "no_impossible_reverse_engineer_claim",
        no_impossible_claim,
        "Must NOT say binaries are impossible to reverse engineer." if not no_impossible_claim else "No 'impossible to reverse engineer' claim found."
    )

    # CHECK 8: Binary description uses "reduce casual source visibility" language OR equivalent
    # The skill says: "Say binaries reduce casual source visibility."
    # Check for this phrasing or close equivalent
    binary_visibility_ok = bool(re.search(
        r'reduc.{0,30}(casual|source|visib)',
        content_lower
    )) or bool(re.search(
        r'(casual|source).{0,30}visib',
        content_lower
    )) or "casual source visibility" in content_lower or "reduce casual" in content_lower
    add_check(
        "binary_reduces_casual_visibility_phrasing",
        binary_visibility_ok,
        "When describing binaries, must use language like 'reduces casual source visibility'." if not binary_visibility_ok else "Correct binary visibility language found."
    )

    # CHECK 9: Unpack command present (tar -xzf with correct linux filename)
    tar_unpack_linux = bool(re.search(
        r'tar\s+-xzf\s+lobster-cli-roguelike-linux-x86_64\.tar\.gz',
        content
    ))
    add_check(
        "linux_unpack_command_correct",
        tar_unpack_linux,
        "Must include correct tar unpack command for linux asset." if not tar_unpack_linux else "Linux unpack command correct."
    )

    # CHECK 10: Run command present (./lobster-cli-roguelike after cd into correct directory)
    # Must have: cd lobster-cli-roguelike-linux-x86_64 AND ./lobster-cli-roguelike
    cd_linux_dir = "cd lobster-cli-roguelike-linux-x86_64" in content
    run_binary = "./lobster-cli-roguelike" in content
    run_instructions_present = cd_linux_dir and run_binary
    add_check(
        "linux_run_instructions_correct",
        run_instructions_present,
        "Must include 'cd lobster-cli-roguelike-linux-x86_64' and './lobster-cli-roguelike' run command." if not run_instructions_present else "Linux run instructions correct."
    )

    # CHECK 11: Does NOT instruct user to clone the repo (prefer released binaries)
    clone_instruction = bool(re.search(
        r'git\s+clone',
        content_lower
    ))
    no_clone_instruction = not clone_instruction
    add_check(
        "no_git_clone_instruction",
        no_clone_instruction,
        "Must NOT instruct user to 'git clone' the repo (prefer released binaries)." if not no_clone_instruction else "No git clone instruction found."
    )

    # Score calculation
    passed_checks = [c for c in checks if c["passed"]]
    # file_exists and file_readable are gating; rest are scored
    scored_checks = checks[2:]  # skip file_exists and file_readable for scoring
    scored_passed = [c for c in scored_checks if c["passed"]]

    score = round(len(scored_passed) / len(scored_checks), 3) if scored_checks else 0.0

    # Overall pass: must pass all scored checks (strict)
    overall_passed = all(c["passed"] for c in checks)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation_error", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))