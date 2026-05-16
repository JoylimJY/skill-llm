#!/usr/bin/env python3
"""
Evaluation script for the smarthome-hub project workflow task.
Tests that the agent correctly:
1. Created the proper project scaffold under projects/smarthome-hub/
2. features.json has correct schema (all required fields, correct enums, sufficient granularity)
3. At least one feature has passes: true (session was performed)
4. progress.md has both initialization block AND a session block with required keys
5. git history has at least 2 commits (init + session)
6. src/ and tests/ directories exist
7. Only passes/notes were modified (no entries deleted or structurally changed)
8. The session log entry uses the mandated markdown format
"""

import sys
import json
import subprocess
import re
from pathlib import Path

def run(args, cwd=None):
    try:
        r = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=10)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return "", str(e), -1

def find_project_dir(workspace: Path):
    """Find the project directory - must be under projects/smarthome-hub/"""
    candidates = [
        workspace / "projects" / "smarthome-hub",
        workspace / "projects" / "smartHome-hub",
        workspace / "projects" / "smarthome_hub",
        workspace / "projects" / "SmartHome-Hub",
        workspace / "projects" / "smarthome-hub-firmware",
    ]
    for c in candidates:
        if c.exists():
            return c
    # Broader search
    projects_dir = workspace / "projects"
    if projects_dir.exists():
        children = [d for d in projects_dir.iterdir() if d.is_dir()]
        if len(children) == 1:
            return children[0]
        for child in children:
            name = child.name.lower()
            if "smart" in name or "hub" in name or "home" in name:
                return child
    return None

def check_features_json_schema(features_data):
    """Validate features.json schema compliance."""
    checks = []
    
    # Top-level fields
    has_project = "project" in features_data
    has_created = "created" in features_data
    has_features = "features" in features_data and isinstance(features_data["features"], list)
    checks.append(("features_json_top_level_fields", has_project and has_created and has_features,
                   f"project={has_project}, created={has_created}, features_list={has_features}"))
    
    if not has_features:
        return checks
    
    features = features_data["features"]
    
    # Granularity: must have at least 8 features (200>10 principle, but realistically >=8)
    checks.append(("features_json_granularity_min8", len(features) >= 8,
                   f"Found {len(features)} features (need >=8 for adequate granularity)"))
    
    # All required fields on each feature
    required_fields = ["id", "name", "description", "category", "priority", "passes", "tests", "notes"]
    valid_categories = {"functional", "infra", "docs", "perf", "fix"}
    valid_priorities = {"high", "medium", "low"}
    
    all_have_required = True
    all_valid_category = True
    all_valid_priority = True
    all_passes_bool = True
    all_tests_list = True
    all_notes_str = True
    bad_entries = []
    
    for feat in features:
        missing = [f for f in required_fields if f not in feat]
        if missing:
            all_have_required = False
            bad_entries.append(f"{feat.get('id','?')} missing {missing}")
        if "category" in feat and feat["category"] not in valid_categories:
            all_valid_category = False
            bad_entries.append(f"{feat.get('id','?')} bad category={feat['category']}")
        if "priority" in feat and feat["priority"] not in valid_priorities:
            all_valid_priority = False
            bad_entries.append(f"{feat.get('id','?')} bad priority={feat['priority']}")
        if "passes" in feat and not isinstance(feat["passes"], bool):
            all_passes_bool = False
            bad_entries.append(f"{feat.get('id','?')} passes not bool")
        if "tests" in feat and not isinstance(feat["tests"], list):
            all_tests_list = False
            bad_entries.append(f"{feat.get('id','?')} tests not list")
        if "notes" in feat and not isinstance(feat["notes"], str):
            all_notes_str = False
    
    checks.append(("features_all_have_required_fields", all_have_required,
                   "All good" if all_have_required else f"Issues: {bad_entries[:3]}"))
    checks.append(("features_valid_category_enum", all_valid_category,
                   f"Valid enums: functional|infra|docs|perf|fix. Issues: {[b for b in bad_entries if 'category' in b][:3]}"))
    checks.append(("features_valid_priority_enum", all_valid_priority,
                   f"Valid enums: high|medium|low. Issues: {[b for b in bad_entries if 'priority' in b][:3]}"))
    checks.append(("features_passes_is_bool", all_passes_bool,
                   "All passes fields are boolean" if all_passes_bool else "Some passes not boolean"))
    checks.append(("features_tests_is_list", all_tests_list,
                   "All tests fields are lists" if all_tests_list else "Some tests not list"))
    
    # IDs follow feat-NNN pattern
    id_pattern = re.compile(r'^feat-\d+$')
    all_good_ids = all(id_pattern.match(str(feat.get("id", ""))) for feat in features)
    checks.append(("features_id_format_feat_NNN", all_good_ids,
                   "All IDs match feat-NNN" if all_good_ids else "Some IDs don't match feat-NNN pattern"))
    
    return checks

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    workspace = Path(sys.argv[1])
    checks = []
    
    # ── CHECK 1: Project directory exists under projects/ ─────────────────────
    proj_dir = find_project_dir(workspace)
    check_proj_dir = proj_dir is not None and proj_dir.exists()
    checks.append({
        "name": "project_dir_exists_under_projects",
        "passed": check_proj_dir,
        "detail": f"Found at {proj_dir}" if check_proj_dir else "No project directory found under projects/"
    })
    
    if not check_proj_dir:
        # Can't continue without project dir
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # ── CHECK 2: Required files exist ─────────────────────────────────────────
    required_files = {
        "PROJECT.md": proj_dir / "PROJECT.md",
        "features.json": proj_dir / "features.json",
        "progress.md": proj_dir / "progress.md",
    }
    for fname, fpath in required_files.items():
        exists = fpath.exists() and fpath.stat().st_size > 10
        checks.append({
            "name": f"file_exists_{fname.replace('.', '_')}",
            "passed": exists,
            "detail": f"{'Found' if exists else 'Missing or empty'}: {fpath}"
        })
    
    # ── CHECK 3: src/ and tests/ directories exist ────────────────────────────
    src_exists = (proj_dir / "src").is_dir()
    tests_exists = (proj_dir / "tests").is_dir()
    checks.append({
        "name": "src_directory_exists",
        "passed": src_exists,
        "detail": f"src/ dir: {'found' if src_exists else 'missing'}"
    })
    checks.append({
        "name": "tests_directory_exists",
        "passed": tests_exists,
        "detail": f"tests/ dir: {'found' if tests_exists else 'missing'}"
    })
    
    # ── CHECK 4: features.json schema ─────────────────────────────────────────
    features_data = None
    try:
        features_raw = (proj_dir / "features.json").read_text(encoding="utf-8")
        features_data = json.loads(features_raw)
        schema_checks = check_features_json_schema(features_data)
        for name, passed, detail in schema_checks:
            checks.append({"name": name, "passed": passed, "detail": detail})
    except FileNotFoundError:
        checks.append({"name": "features_json_parseable", "passed": False, "detail": "features.json not found"})
    except json.JSONDecodeError as e:
        checks.append({"name": "features_json_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
    
    # ── CHECK 5: At least one feature has passes: true (session was done) ──────
    if features_data and "features" in features_data:
        completed = [f for f in features_data["features"] if f.get("passes") is True]
        exactly_one_done = len(completed) == 1  # Must do exactly ONE per session
        at_least_one_done = len(completed) >= 1
        checks.append({
            "name": "at_least_one_feature_passes_true",
            "passed": at_least_one_done,
            "detail": f"Features with passes=true: {len(completed)}"
        })
        checks.append({
            "name": "exactly_one_feature_done_per_session",
            "passed": exactly_one_done,
            "detail": f"Exactly 1 feature should be done (found {len(completed)}). Framework mandates one feature per session."
        })
        
        # The completed feature must still have all its original fields (no deletion)
        if completed:
            done_feat = completed[0]
            required_fields = ["id", "name", "description", "category", "priority", "passes", "tests", "notes"]
            all_present = all(f in done_feat for f in required_fields)
            checks.append({
                "name": "completed_feature_retains_all_fields",
                "passed": all_present,
                "detail": f"Completed feature {done_feat.get('id')} has all required fields: {all_present}"
            })
    else:
        checks.append({"name": "at_least_one_feature_passes_true", "passed": False, 
                       "detail": "Cannot check - features.json missing or malformed"})
    
    # ── CHECK 6: progress.md has initialization block AND session block ────────
    try:
        progress_content = (proj_dir / "progress.md").read_text(encoding="utf-8")
        
        # Must have "项目工作日志" header
        has_log_header = "项目工作日志" in progress_content
        checks.append({
            "name": "progress_md_has_log_header",
            "passed": has_log_header,
            "detail": f"'项目工作日志' header: {'found' if has_log_header else 'missing'}"
        })
        
        # Must have initialization section
        has_init = "## 初始化" in progress_content or "初始化" in progress_content
        checks.append({
            "name": "progress_md_has_init_section",
            "passed": has_init,
            "detail": f"Initialization section: {'found' if has_init else 'missing'}"
        })
        
        # Must have a session block: "## 会话" pattern
        has_session = bool(re.search(r'##\s+会话\s*\d+', progress_content))
        checks.append({
            "name": "progress_md_has_session_block",
            "passed": has_session,
            "detail": f"Session block (## 会话 N): {'found' if has_session else 'missing'}"
        })
        
        # Session block must contain the required keys
        if has_session:
            has_target = "目标功能" in progress_content
            has_status = "状态" in progress_content
            has_done = "完成内容" in progress_content
            has_issues = "遇到的问题" in progress_content
            has_next = "下次继续" in progress_content
            has_commits = "Git commits" in progress_content or "git commit" in progress_content.lower()
            
            session_keys_present = has_target and has_status and has_done
            checks.append({
                "name": "progress_md_session_has_required_keys",
                "passed": session_keys_present,
                "detail": f"目标功能={has_target}, 状态={has_status}, 完成内容={has_done}, 遇到的问题={has_issues}, 下次继续={has_next}"
            })
            
            # Status must use the prescribed emoji markers
            has_emoji_status = ("✅" in progress_content or "⏳" in progress_content or "❌" in progress_content)
            checks.append({
                "name": "progress_md_session_uses_emoji_status",
                "passed": has_emoji_status,
                "detail": f"Status emoji (✅/⏳/❌): {'found' if has_emoji_status else 'missing'}"
            })
        
    except FileNotFoundError:
        checks.append({"name": "progress_md_readable", "passed": False, "detail": "progress.md not found"})
    except Exception as e:
        checks.append({"name": "progress_md_readable", "passed": False, "detail": f"Error reading progress.md: {e}"})
    
    # ── CHECK 7: PROJECT.md has required sections ──────────────────────────────
    try:
        project_md = (proj_dir / "PROJECT.md").read_text(encoding="utf-8")
        has_tech = any(k in project_md for k in ["技术栈", "Tech", "技术", "Stack", "stack"])
        has_goal = any(k in project_md for k in ["目标", "Goal", "goal", "Objective", "objective"])
        has_criteria = any(k in project_md for k in ["验收", "Acceptance", "criteria", "Criteria", "标准"])
        has_constraints = any(k in project_md for k in ["约束", "Constraint", "constraint", "限制"])
        
        checks.append({
            "name": "project_md_has_tech_stack",
            "passed": has_tech,
            "detail": f"Tech stack section: {'found' if has_tech else 'missing'}"
        })
        checks.append({
            "name": "project_md_has_goal",
            "passed": has_goal,
            "detail": f"Goal/objective section: {'found' if has_goal else 'missing'}"
        })
        checks.append({
            "name": "project_md_has_acceptance_criteria",
            "passed": has_criteria,
            "detail": f"Acceptance criteria: {'found' if has_criteria else 'missing'}"
        })
    except Exception as e:
        checks.append({"name": "project_md_readable", "passed": False, "detail": str(e)})
    
    # ── CHECK 8: Git repository exists and has at least 2 commits ─────────────
    git_log_out, git_log_err, git_rc = run(["git", "log", "--oneline"], cwd=str(proj_dir))
    git_exists = git_rc == 0
    checks.append({
        "name": "git_repository_initialized",
        "passed": git_exists,
        "detail": f"Git repo: {'found' if git_exists else 'not found'}. Error: {git_log_err[:100]}"
    })
    
    if git_exists:
        commit_lines = [l for l in git_log_out.strip().split('\n') if l.strip()]
        has_two_commits = len(commit_lines) >= 2
        checks.append({
            "name": "git_has_at_least_two_commits",
            "passed": has_two_commits,
            "detail": f"Commits found: {len(commit_lines)} (need >=2: init + session commit)"
        })
        
        # Latest commit message should start with "feat:"
        if commit_lines:
            latest_msg = commit_lines[0]  # git log --oneline is newest first
            has_feat_prefix = "feat:" in latest_msg.lower() or "feat：" in latest_msg
            checks.append({
                "name": "latest_commit_has_feat_prefix",
                "passed": has_feat_prefix,
                "detail": f"Latest commit: '{latest_msg}'"
            })
    
    # ── CHECK 9: No wrong-location project files (not in bad_attempt/) ────────
    # The canonical location must be under projects/
    bad_attempt_json = workspace / "project_attempt_WRONG" / "features.json"
    wrong_location_not_used = True
    if bad_attempt_json.exists():
        try:
            bad_data = json.loads(bad_attempt_json.read_text())
            # If it still has the wrong format, that's fine (agent didn't touch it)
            # If agent put their work there instead of projects/, that's bad
            if "features" in bad_data and isinstance(bad_data.get("features"), list):
                # Check if it has proper feat-NNN IDs (meaning agent put real work here)
                for feat in bad_data["features"]:
                    if re.match(r'^feat-\d+$', str(feat.get("id", ""))):
                        wrong_location_not_used = False
                        break
        except Exception:
            pass
    checks.append({
        "name": "project_not_created_in_wrong_location",
        "passed": wrong_location_not_used,
        "detail": "Project correctly placed under projects/ (not in wrong/partial directories)"
    })
    
    # ── SCORING ───────────────────────────────────────────────────────────────
    # Weight the checks
    critical_checks = {
        "project_dir_exists_under_projects",
        "features_json_parseable",
        "features_json_top_level_fields",
        "features_all_have_required_fields",
        "features_valid_category_enum",
        "features_valid_priority_enum",
        "at_least_one_feature_passes_true",
        "exactly_one_feature_done_per_session",
        "progress_md_has_session_block",
        "progress_md_session_has_required_keys",
        "git_repository_initialized",
        "git_has_at_least_two_commits",
    }
    
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    
    critical_passed = sum(1 for c in checks if c["passed"] and c["name"] in critical_checks)
    critical_total = len(critical_checks)
    
    # Must pass all critical checks to be considered passing
    all_critical_pass = critical_passed == critical_total
    
    score = passed_count / total if total > 0 else 0.0
    
    # Overall pass: all critical checks must pass + >75% of all checks
    overall_pass = all_critical_pass and (score >= 0.75)
    
    result = {
        "passed": overall_pass,
        "score": round(score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()