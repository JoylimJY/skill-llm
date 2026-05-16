import sys
import json
import re
from pathlib import Path

def find_spec_file(workspace: Path):
    """Find the CLI spec file. Accepts .md or .txt files with genpipe in the name."""
    candidates = list(workspace.rglob("genpipe_cli_spec*"))
    if not candidates:
        # Also look for any file explicitly named as a spec
        candidates = list(workspace.rglob("genpipe*spec*"))
    if not candidates:
        candidates = list(workspace.rglob("cli_spec*"))
    return candidates

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    
    # ── Find the spec file
    candidates = find_spec_file(workspace)
    # Exclude legacy/distractor files
    candidates = [c for c in candidates if "legacy" not in str(c) and "v0_draft" not in str(c)]
    
    if not candidates:
        checks.append(check("spec_file_exists", False, "No genpipe CLI spec file found. Expected a file like genpipe_cli_spec.md"))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    spec_file = candidates[0]
    checks.append(check("spec_file_exists", True, f"Found spec at {spec_file.relative_to(workspace)}"))
    
    try:
        content = spec_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append(check("spec_file_readable", False, str(e)))
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append(check("spec_file_readable", True, f"File is {len(content)} chars"))
    
    content_lower = content.lower()
    
    # ══════════════════════════════════════════
    # SECTION 1: COMMAND TREE & SUBCOMMANDS
    # ══════════════════════════════════════════
    
    # Must have deploy subcommand
    has_deploy = bool(re.search(r'\bdeploy\b', content_lower))
    checks.append(check("subcommand_deploy", has_deploy,
        "Spec must include a 'deploy' subcommand" if not has_deploy else "deploy subcommand present"))
    
    # Must have destroy subcommand
    has_destroy = bool(re.search(r'\bdestroy\b', content_lower))
    checks.append(check("subcommand_destroy", has_destroy,
        "Spec must include a 'destroy' subcommand" if not has_destroy else "destroy subcommand present"))
    
    # Must have a completion/shell-completion subcommand or section
    has_completion = bool(re.search(r'\bcompletion\b', content_lower))
    checks.append(check("subcommand_completion", has_completion,
        "Spec must include a 'completion' subcommand for shell completion" if not has_completion else "completion subcommand present"))
    
    # ══════════════════════════════════════════
    # SECTION 2: HELP & VERSION FLAGS
    # ══════════════════════════════════════════
    
    # -h/--help must be present
    has_help = bool(re.search(r'(?:^|\s)-h[,/\s]|--help', content))
    checks.append(check("flag_help", has_help,
        "Spec must include -h/--help flag" if not has_help else "-h/--help present"))
    
    # --help ignores other args (proprietary: help always wins)
    help_ignores = bool(re.search(r'(?:help.*ignor|ignor.*other.*arg|always.*win|win.*over|overrid.*all|regardless.*other)', content_lower))
    checks.append(check("help_ignores_other_args", help_ignores,
        "Spec must state that -h/--help ignores all other arguments (always wins)" if not help_ignores else "help ignores-other-args behavior documented"))
    
    # --version
    has_version = bool(re.search(r'--version', content))
    checks.append(check("flag_version", has_version,
        "Spec must include --version flag" if not has_version else "--version present"))
    
    # ══════════════════════════════════════════
    # SECTION 3: OUTPUT CONTRACT (stdout/stderr)
    # ══════════════════════════════════════════
    
    # stdout for primary data
    has_stdout = bool(re.search(r'stdout', content_lower))
    checks.append(check("output_stdout_defined", has_stdout,
        "Spec must define stdout as primary data stream" if not has_stdout else "stdout defined"))
    
    # stderr for errors/diagnostics
    has_stderr = bool(re.search(r'stderr', content_lower))
    checks.append(check("output_stderr_defined", has_stderr,
        "Spec must define stderr for errors/diagnostics" if not has_stderr else "stderr defined"))
    
    # --json flag
    has_json_flag = bool(re.search(r'--json', content))
    checks.append(check("flag_json", has_json_flag,
        "Spec must include --json flag for machine-readable output" if not has_json_flag else "--json flag present"))
    
    # --plain flag
    has_plain_flag = bool(re.search(r'--plain', content))
    checks.append(check("flag_plain", has_plain_flag,
        "Spec must include --plain flag for stable line-oriented text" if not has_plain_flag else "--plain flag present"))
    
    # --quiet/-q
    has_quiet = bool(re.search(r'(?:^|\s)-q[,\s]|--quiet', content))
    checks.append(check("flag_quiet", has_quiet,
        "Spec must include -q/--quiet flag" if not has_quiet else "-q/--quiet present"))
    
    # --verbose/-v
    has_verbose = bool(re.search(r'(?:^|\s)-v[,\s]|--verbose', content))
    checks.append(check("flag_verbose", has_verbose,
        "Spec must include -v/--verbose flag" if not has_verbose else "-v/--verbose present"))
    
    # ══════════════════════════════════════════
    # SECTION 4: EXIT CODES (proprietary trap)
    # ══════════════════════════════════════════
    
    # Exit code 0
    has_exit_0 = bool(re.search(r'(?:exit\s*(?:code\s*)?|code\s*)0\b.*success|success.*\b0\b', content_lower))
    if not has_exit_0:
        has_exit_0 = bool(re.search(r'\b0\b.*success|success.*\b0\b', content_lower))
    checks.append(check("exit_code_0_success", has_exit_0,
        "Exit code 0 = success must be defined" if not has_exit_0 else "exit code 0=success defined"))
    
    # Exit code 1 = generic/runtime failure
    has_exit_1 = bool(re.search(r'\b1\b.{0,80}(?:generic|runtime|failure|error)', content_lower))
    if not has_exit_1:
        has_exit_1 = bool(re.search(r'(?:generic|runtime).{0,40}\b1\b', content_lower))
    checks.append(check("exit_code_1_generic_failure", has_exit_1,
        "Exit code 1 = generic runtime failure must be defined" if not has_exit_1 else "exit code 1=generic failure defined"))
    
    # Exit code 2 = invalid usage / bad args / validation (PROPRIETARY TRAP)
    has_exit_2 = bool(re.search(r'\b2\b.{0,120}(?:invalid\s+usage|bad\s+arg|unknown\s+flag|validation|missing\s+required|parse)', content_lower))
    if not has_exit_2:
        has_exit_2 = bool(re.search(r'(?:invalid\s+usage|bad\s+arg|argument|validation|parse\s+error).{0,80}\b2\b', content_lower))
    checks.append(check("exit_code_2_invalid_usage", has_exit_2,
        "Exit code 2 = invalid usage (bad args/flags/validation) MUST be defined separately from exit 1. This is a proprietary convention from the guidelines." if not has_exit_2 else "exit code 2=invalid usage defined"))
    
    # ══════════════════════════════════════════
    # SECTION 5: INTERACTIVITY & --no-input (PROPRIETARY TRAP)
    # ══════════════════════════════════════════
    
    # Must use --no-input (NOT --non-interactive, --batch, --headless)
    has_no_input = bool(re.search(r'--no-input', content))
    has_wrong_noninteractive = bool(re.search(r'--non-interactive|--batch\b|--headless', content))
    
    if has_no_input:
        checks.append(check("flag_no_input_correct", True, "--no-input flag correctly used"))
    elif has_wrong_noninteractive:
        checks.append(check("flag_no_input_correct", False,
            "Used --non-interactive/--batch/--headless instead of the required --no-input flag"))
    else:
        checks.append(check("flag_no_input_correct", False,
            "--no-input flag missing. This disables ALL prompts; fail with exit 2 if required info is missing."))
    
    # TTY detection for prompts
    has_tty = bool(re.search(r'\bisatty\b|\btty\b|\bterminal\b', content_lower))
    checks.append(check("tty_detection", has_tty,
        "Spec must mention TTY detection for conditional prompts" if not has_tty else "TTY detection mentioned"))
    
    # ══════════════════════════════════════════
    # SECTION 6: SAFETY FLAGS
    # ══════════════════════════════════════════
    
    # --dry-run
    has_dry_run = bool(re.search(r'--dry-run|--dry\b', content))
    if re.search(r'--dry\b', content) and not re.search(r'--dry-run', content):
        # Old spec used --dry (legacy abbreviation); guidelines require --dry-run
        has_dry_run = False
        checks.append(check("flag_dry_run", False,
            "Must use --dry-run (not --dry). The guidelines prescribe --dry-run as the canonical flag name."))
    else:
        checks.append(check("flag_dry_run", has_dry_run,
            "Spec must include --dry-run flag" if not has_dry_run else "--dry-run present"))
    
    # --force flag
    has_force = bool(re.search(r'--force', content))
    checks.append(check("flag_force", has_force,
        "Spec must include --force flag for non-interactive destructive ops" if not has_force else "--force flag present"))
    
    # dry-run wins over force (chaining rule)
    dry_wins = bool(re.search(r'dry.{0,30}win|dry.{0,30}over.{0,30}force|force.{0,30}dry.{0,30}no|always.*dry', content_lower))
    checks.append(check("dry_run_wins_over_force", dry_wins,
        "Spec must state --dry-run always wins over --force (never destructive)" if not dry_wins else "dry-run > force chaining rule documented"))
    
    # Destroy must show summary BEFORE confirmation
    destroy_summary = bool(re.search(r'destroy.{0,200}(?:summary|list|show|display|before|preview).{0,200}(?:confirm|delete|destroy)',
                                      content_lower, re.DOTALL))
    if not destroy_summary:
        destroy_summary = bool(re.search(r'(?:summary|list|show|display).{0,100}(?:before|prior).{0,100}confirm',
                                          content_lower, re.DOTALL))
    checks.append(check("destroy_shows_summary_before_confirmation", destroy_summary,
        "For destroy: spec must display a summary of what will be deleted BEFORE asking for confirmation" if not destroy_summary else "destroy pre-confirmation summary documented"))
    
    # ══════════════════════════════════════════
    # SECTION 7: CONFIG / ENV PRECEDENCE (PROPRIETARY TRAP)
    # ══════════════════════════════════════════
    
    # Must have 5-level precedence: flags > env > project config > user config > system
    # Check for the split between project and user config (most agents miss this)
    has_project_config = bool(re.search(r'project.{0,30}config|\.genpipe\.yml|repo.{0,30}config|working.{0,30}dir', content_lower))
    has_user_config = bool(re.search(r'user.{0,30}config|~\/\.config|home.{0,30}dir|per.{0,30}user', content_lower))
    has_system_config = bool(re.search(r'system.{0,30}config|\/etc\/|system.{0,30}level', content_lower))
    
    checks.append(check("config_project_level", has_project_config,
        "Spec must include project-level config file (e.g., .genpipe.yml in working dir)" if not has_project_config else "project-level config defined"))
    checks.append(check("config_user_level", has_user_config,
        "Spec must include user-level config file (e.g., ~/.config/genpipe/config.yml)" if not has_user_config else "user-level config defined"))
    checks.append(check("config_system_level", has_system_config,
        "Spec must include system-level config file (e.g., /etc/genpipe/config.yml)" if not has_system_config else "system-level config defined"))
    
    # Precedence order: flags > env > project > user > system
    # Check that flags are listed as highest priority
    flags_highest = bool(re.search(r'flag.{0,50}(?:highest|first|1\.|overrid|win)|(?:1\.|highest).{0,50}flag', content_lower))
    checks.append(check("config_flags_highest_priority", flags_highest,
        "Spec must state CLI flags have highest priority in config precedence" if not flags_highest else "flags=highest priority in precedence"))
    
    # Env var naming convention: SCREAMING_SNAKE_CASE with tool prefix
    env_naming = bool(re.search(r'GENPIPE_[A-Z_]+|SCREAMING_SNAKE|[A-Z_]+_[A-Z_]+\s+(?:env|environment)', content))
    if not env_naming:
        env_naming = bool(re.search(r'genpipe_cluster_url|genpipe_token|toolname_flag|env.*prefix|prefix.*env', content_lower))
    checks.append(check("env_var_naming_convention", env_naming,
        "Spec must define env var naming: TOOLNAME_FLAG_NAME in SCREAMING_SNAKE_CASE (e.g., GENPIPE_CLUSTER_URL)" if not env_naming else "env var naming convention defined"))
    
    # ══════════════════════════════════════════
    # SECTION 8: SECURITY (no secrets via flags)
    # ══════════════════════════════════════════
    
    no_secrets_in_flags = bool(re.search(r'secret|credential|token|password|auth.{0,30}(?:flag|arg|never|not|env)', content_lower))
    checks.append(check("no_secrets_in_flags", no_secrets_in_flags,
        "Spec must explicitly state credentials/tokens must NOT be passed via flags" if not no_secrets_in_flags else "credential security rule present"))
    
    # ══════════════════════════════════════════
    # SECTION 9: COLOR HANDLING (triple mechanism, PROPRIETARY TRAP)
    # ══════════════════════════════════════════
    
    # NO_COLOR env var
    has_no_color_env = bool(re.search(r'NO_COLOR', content))
    checks.append(check("color_NO_COLOR_env", has_no_color_env,
        "Spec must respect NO_COLOR environment variable" if not has_no_color_env else "NO_COLOR env var respected"))
    
    # TERM=dumb
    has_term_dumb = bool(re.search(r'TERM=dumb|TERM\s*=\s*dumb', content))
    checks.append(check("color_TERM_dumb", has_term_dumb,
        "Spec must respect TERM=dumb (disable colors/interactive elements)" if not has_term_dumb else "TERM=dumb respected"))
    
    # --no-color flag
    has_no_color_flag = bool(re.search(r'--no-color', content))
    checks.append(check("color_no_color_flag", has_no_color_flag,
        "Spec must include --no-color flag" if not has_no_color_flag else "--no-color flag present"))
    
    # ══════════════════════════════════════════
    # SECTION 10: EXAMPLES
    # ══════════════════════════════════════════
    
    # Must have at least 5 examples
    example_lines = [l for l in content.split('\n') if re.search(r'genpipe\s+\w+', l) and not l.strip().startswith('#')]
    has_enough_examples = len(example_lines) >= 5
    checks.append(check("examples_at_least_5", has_enough_examples,
        f"Spec must contain at least 5 example invocations (found ~{len(example_lines)})" if not has_enough_examples else f"Found {len(example_lines)} example invocations"))
    
    # Must have a piped/stdin example
    has_pipe_example = bool(re.search(r'\|.*genpipe|genpipe.*\||\bstdin\b|< .*\.', content))
    checks.append(check("examples_include_pipe_or_stdin", has_pipe_example,
        "Spec must include at least one piped/stdin example invocation" if not has_pipe_example else "piped/stdin example present"))
    
    # ══════════════════════════════════════════
    # SCORING
    # ══════════════════════════════════════════
    
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = score >= 0.80  # Need 80%+ to pass
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))