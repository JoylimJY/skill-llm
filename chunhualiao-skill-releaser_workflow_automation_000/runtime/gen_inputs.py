#!/usr/bin/env python3
import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)
WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ── Directory skeleton ─────────────────────────────────────────────────────────
dirs = [
    "skills/data-sync-agent",
    "skills/data-sync-agent/tests",
    "skills/data-sync-agent/references",
    "skills/data-sync-agent/scripts",
    "skills/code-reviewer",
    "skills/code-reviewer/tests",
    "skills/code-reviewer/references",
    "audits",
    "shared/utils",
    "memory",
    "scripts",
    "projects/internal",
    "reviews",
    "slides",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
(WORKSPACE / "USER.md").write_text("# User Profile\nName: Alice\nOrg: InternalCorp\n")
(WORKSPACE / "MEMORY.md").write_text("# Memory Log\n- Released code-reviewer on 2024-01-10\n")
(WORKSPACE / "AGENTS.md").write_text("# Agents\nPrimary: OpenClaw v2\n")
(WORKSPACE / "SOUL.md").write_text("# Soul\nCore values and mission.\n")
(WORKSPACE / "audits/data-sync-agent-competitive.md").write_text(
    "# Competitive Analysis\ndata-sync-agent is novel in its approach.\n"
)
(WORKSPACE / "shared/utils/helpers.py").write_text("def noop(): pass\n")
(WORKSPACE / "memory/session-log.json").write_text('{"sessions": []}\n')
(WORKSPACE / "projects/internal/roadmap.md").write_text("# Roadmap\nQ3: release data-sync-agent\n")
(WORKSPACE / "slides/overview.md").write_text("# Overview\nCompany presentation\n")
(WORKSPACE / "skills/code-reviewer/SKILL.md").write_text(
    "---\nname: code-reviewer\nversion: 0.2.0\n---\n# Code Reviewer\nReviews code.\n"
)
(WORKSPACE / "skills/code-reviewer/skill.yml").write_text(
    "name: code-reviewer\nversion: 0.2.0\ndescription: Reviews code for quality.\n"
)
(WORKSPACE / "skills/code-reviewer/tests/test-triggers.json").write_text(
    json.dumps({"shouldTrigger": ["review my code"], "shouldNotTrigger": ["deploy my app"]}, indent=2)
)

# ── The skill under release: data-sync-agent ─────────────────────────────────
# Only SKILL.md exists — everything else must be scaffolded by the agent.
# SKILL.md has NEW features compared to the previously-published version (1.0.0).
skill_md = textwrap.dedent("""\
    ---
    name: data-sync-agent
    description: Synchronises data between heterogeneous sources using configurable pipelines — supports REST APIs, SQL databases, and flat-file stores. Handles schema drift, conflict resolution, and incremental syncs.
    version: 1.0.0
    triggers:
      - sync data
      - run data pipeline
      - start sync
      - sync tables
      - push data to target
    ---

    # Data Sync Agent

    Orchestrates bidirectional data synchronisation across REST APIs, SQL databases,
    and flat-file stores.

    ## When to Use

    - User says "sync {source} to {target}"
    - User says "run data pipeline for {dataset}"
    - User says "start incremental sync"
    - Scheduled cron sync jobs

    ## Features

    - Schema drift detection with auto-mapping
    - Conflict resolution strategies: last-write-wins, source-priority, merge
    - Incremental sync via watermark columns
    - Retry logic with exponential backoff
    - Dry-run mode for validation before commit

    ## Configuration

    Pipeline configuration lives in `pipeline.yml`. See `references/pipeline-schema.md`
    for field descriptions.

    ## Anti-patterns

    - Do not use this skill to replicate binary blobs or media files
    - Do not trigger on "backup data" — that is a separate skill
    - Do not trigger on "export report" — use the reporting skill instead
    """)
(WORKSPACE / "skills/data-sync-agent/SKILL.md").write_text(skill_md)

# Existing partial skill.yml — missing display_name, has old version
# Agent must NOT overwrite this but must update version and add display_name
skill_yml_existing = textwrap.dedent("""\
    name: data-sync-agent
    description: Synchronises data between heterogeneous sources using configurable pipelines.
    version: 1.0.0
    triggers:
      - sync data
      - run data pipeline
      - start sync
    """)
(WORKSPACE / "skills/data-sync-agent/skill.yml").write_text(skill_yml_existing)

# references placeholder
(WORKSPACE / "skills/data-sync-agent/references/pipeline-schema.md").write_text(
    "# Pipeline Schema\nDescribes all fields in pipeline.yml.\n"
)

# ── Global pipeline scripts (already exist in workspace per skill.md) ─────────
validate_structure = textwrap.dedent("""\
    #!/usr/bin/env bash
    # validate-structure.sh  — scores skill structure completeness (8 checks)
    set -euo pipefail
    DIR="${1:-.}"
    score=0
    checks=()

    check() {
        local label="$1"; local result="$2"
        if [ "$result" = "ok" ]; then
            score=$((score+1))
            checks+=("PASS: $label")
        else
            checks+=("FAIL: $label")
        fi
    }

    [ -f "$DIR/SKILL.md" ]           && check "SKILL.md present"           ok || check "SKILL.md present"           fail
    [ -f "$DIR/skill.yml" ]          && check "skill.yml present"           ok || check "skill.yml present"          fail
    [ -f "$DIR/README.md" ]          && check "README.md present"           ok || check "README.md present"          fail
    [ -f "$DIR/CHANGELOG.md" ]       && check "CHANGELOG.md present"        ok || check "CHANGELOG.md present"       fail
    [ -f "$DIR/LICENSE" ]            && check "LICENSE present"             ok || check "LICENSE present"            fail
    [ -f "$DIR/.gitignore" ]         && check ".gitignore present"          ok || check ".gitignore present"         fail
    [ -f "$DIR/tests/test-triggers.json" ] && check "test-triggers.json"   ok || check "test-triggers.json"         fail
    { [ -f "$DIR/scripts/README.md" ] || [ -f "$DIR/references/README.md" ] || [ -f "$DIR/references/pipeline-schema.md" ] || ls "$DIR/scripts/" 2>/dev/null | grep -q .; } && check "scripts/references dir"  ok || check "scripts/references dir" fail

    echo "Structure score: $score/8"
    for c in "${checks[@]}"; do echo "  $c"; done
    [ "$score" -eq 8 ] && exit 0 || exit 1
    """)
(WORKSPACE / "scripts/validate-structure.sh").write_text(validate_structure)
(WORKSPACE / "scripts/validate-structure.sh").chmod(0o755)

validate_release = textwrap.dedent("""\
    #!/usr/bin/env bash
    # validate-release-content.sh — blocks pushes with workspace-level contamination
    set -euo pipefail
    DIR="${1:-.}"

    BLOCKED=0
    REASONS=()

    # Check for repo-root files that must never appear in a release
    for f in USER.md MEMORY.md AGENTS.md SOUL.md .gitmodules; do
        if [ -f "$DIR/$f" ]; then
            REASONS+=("BLOCKED: repo-root file present: $f")
            BLOCKED=1
        fi
    done

    # Check for repo-level directories
    for d in audits memory slides projects shared; do
        if [ -d "$DIR/$d" ]; then
            REASONS+=("BLOCKED: repo-level directory present: $d")
            BLOCKED=1
        fi
    done

    # File count check
    COUNT=$(find "$DIR" -type f | wc -l)
    if [ "$COUNT" -gt 50 ]; then
        REASONS+=("BLOCKED: too many files ($COUNT > 50)")
        BLOCKED=1
    fi

    # Suspicious file types
    if find "$DIR" -type f \\( -name "*.log" -o -name "*.pdf" -o -name "*.png" -o -name "*.jpg" \\) | grep -q .; then
        REASONS+=("BLOCKED: suspicious file types found")
        BLOCKED=1
    fi

    if [ "$BLOCKED" -eq 1 ]; then
        echo "RELEASE VALIDATION: BLOCKED"
        for r in "${REASONS[@]}"; do echo "  $r"; done
        exit 1
    else
        echo "RELEASE VALIDATION: SAFE"
        echo "  Files: $COUNT"
        exit 0
    fi
    """)
(WORKSPACE / "scripts/validate-release-content.sh").write_text(validate_release)
(WORKSPACE / "scripts/validate-release-content.sh").chmod(0o755)

opsec_scan = textwrap.dedent("""\
    #!/usr/bin/env bash
    # opsec-scan.sh — scans for sensitive data patterns
    set -euo pipefail
    DIR="${1:-.}"

    VIOLATIONS=()

    scan_file() {
        local f="$1"
        # Internal org names / personal info patterns
        if grep -qiE '(InternalCorp|MyOrg|PrivateCo|alice@|bob@|secret_token|api_key_[a-z]|password=)' "$f" 2>/dev/null; then
            VIOLATIONS+=("SENSITIVE_DATA: $f")
        fi
        # Internal project names
        if grep -qiE '(openclaw-knowledge|/home/alice|/home/bob|192\\.168\\.|10\\.0\\.)' "$f" 2>/dev/null; then
            VIOLATIONS+=("INTERNAL_REF: $f")
        fi
    }

    while IFS= read -r -d '' f; do
        scan_file "$f"
    done < <(find "$DIR" -type f -print0)

    if [ ${#VIOLATIONS[@]} -gt 0 ]; then
        echo "OPSEC SCAN: VIOLATIONS FOUND"
        for v in "${VIOLATIONS[@]}"; do echo "  $v"; done
        exit 1
    else
        echo "OPSEC SCAN: CLEAN"
        exit 0
    fi
    """)
(WORKSPACE / "scripts/opsec-scan.sh").write_text(opsec_scan)
(WORKSPACE / "scripts/opsec-scan.sh").chmod(0o755)

opsec_precommit = textwrap.dedent("""\
    #!/usr/bin/env bash
    # opsec-precommit-hook.sh — pre-commit hook version of opsec scan
    bash "$(dirname "$0")/../../scripts/opsec-scan.sh" . || exit 1
    """)
(WORKSPACE / "scripts/opsec-precommit-hook.sh").write_text(opsec_precommit)
(WORKSPACE / "scripts/opsec-precommit-hook.sh").chmod(0o755)

# ── Mock CLI tools ─────────────────────────────────────────────────────────────
# These live in /usr/local/bin — written here as content, chmod'd in setup_script

# Mock `gh` — simulates repo creation, edit, and view
gh_mock = textwrap.dedent("""\
    #!/usr/bin/env bash
    # Mock gh CLI
    LOG="/tmp/gh_calls.log"
    echo "gh $*" >> "$LOG"

    case "$1 $2" in
        "repo view")
            # Return not-found for our skill repo, simulating it doesn't exist yet
            if echo "$*" | grep -q "data-sync-agent"; then
                echo "ERROR: repository not found" >&2
                exit 1
            fi
            ;;
        "repo create")
            REPO_NAME=""
            for arg in "$@"; do
                if echo "$arg" | grep -qE '^[a-zA-Z0-9_/-]+/[a-zA-Z0-9_-]+$'; then
                    REPO_NAME="$arg"
                fi
            done
            echo "Created repository $REPO_NAME" 
            exit 0
            ;;
        "repo edit")
            echo "Updated repository"
            exit 0
            ;;
        "repo view")
            echo '{"description":"test","repositoryTopics":[]}'
            exit 0
            ;;
        "auth status")
            echo "Logged in to github.com as mockeduser"
            exit 0
            ;;
        "repo view"*)
            echo '{"description":"Sync agent","repositoryTopics":[]}'
            exit 0
            ;;
    esac

    # fallback
    echo "gh mock: unhandled command: $*" >> "$LOG"
    exit 0
    """)

# Mock `clawhub` CLI
clawhub_mock = textwrap.dedent("""\
    #!/usr/bin/env bash
    # Mock clawhub CLI
    LOG="/tmp/clawhub_calls.log"
    echo "clawhub $*" >> "$LOG"

    case "$1" in
        "inspect")
            SLUG="${2:-unknown}"
            if [ "$SLUG" = "data-sync-agent" ]; then
                # Previously published version — triggers version bump requirement
                printf "Data Sync Agent\\nOwner: mockeduser\\nLatest: 1.0.0\\nSummary: Synchronises data between heterogeneous sources.\\n"
                exit 0
            fi
            echo "ERROR: skill not found" >&2
            exit 1
            ;;
        "publish")
            # Parse args: --slug, --name, --version, --changelog
            SLUG="" ; NAME="" ; VERSION="" ; CHANGELOG=""
            while [[ $# -gt 0 ]]; do
                case "$1" in
                    --slug)      SLUG="$2";      shift 2 ;;
                    --name)      NAME="$2";      shift 2 ;;
                    --version)   VERSION="$2";   shift 2 ;;
                    --changelog) CHANGELOG="$2"; shift 2 ;;
                    *)           shift ;;
                esac
            done
            # Validate required fields
            if [ -z "$SLUG" ] || [ -z "$NAME" ] || [ -z "$VERSION" ]; then
                echo "ERROR: --slug, --name, and --version are required" >&2
                exit 1
            fi
            # Write publish record for eval
            mkdir -p /tmp/clawhub_publish
            cat > /tmp/clawhub_publish/last_publish.json <<EOF
    {
      "slug": "$SLUG",
      "name": "$NAME",
      "version": "$VERSION",
      "changelog": "$CHANGELOG"
    }
    EOF
            echo "Published $SLUG v$VERSION to ClawhHub"
            echo "https://clawhub.ai/mockeduser/$SLUG"
            exit 0
            ;;
        "whoami")
            echo "mockeduser"
            exit 0
            ;;
        *)
            echo "clawhub mock: unknown command: $1" >&2
            exit 1
            ;;
    esac
    """)

# Write mock CLIs to workspace for setup_script to install
(WORKSPACE / "scripts/mock-gh.sh").write_text(gh_mock)
(WORKSPACE / "scripts/mock-clawhub.sh").write_text(clawhub_mock)

# Git config file to avoid identity errors
(WORKSPACE / ".gitconfig").write_text(
    "[user]\n    email = agent@localhost\n    name = SkillEngineer\n"
)

print("Workspace generated successfully.")
print(f"Skill directory: {WORKSPACE}/skills/data-sync-agent")
print(f"Scripts: {WORKSPACE}/scripts/")