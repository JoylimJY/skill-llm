#!/usr/bin/env bash
set -euo pipefail

# ── Install the mock git-auto CLI ────────────────────────────────────────────
cat > /usr/local/bin/git-auto << 'GITAUTO_EOF'
#!/usr/bin/env bash
# git-auto v1.0.0 — Git Workspace Automation

set -euo pipefail

CONVENTIONAL_PREFIXES="feat fix refactor docs chore test"

# ── helpers ──────────────────────────────────────────────────────────────────
die()  { echo "git-auto error: $*" >&2; exit 1; }
info() { echo "[git-auto] $*"; }

require_git_repo() {
    git rev-parse --git-dir > /dev/null 2>&1 || die "Not a git repository. Run inside a .git directory."
}

validate_conventional_commit() {
    local msg="$1"
    # Must match: <type>[optional scope]: <description>
    # type must be one of the known prefixes
    if echo "$msg" | grep -qE '^(feat|fix|refactor|docs|chore|test)(\([^)]+\))?: .+'; then
        return 0
    else
        return 1
    fi
}

# ── subcommands ───────────────────────────────────────────────────────────────

cmd_status() {
    require_git_repo
    local all_flag=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --all) all_flag=1; shift ;;
            *) shift ;;
        esac
    done

    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    info "Branch: $BRANCH"

    # Ahead/behind
    UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")
    if [[ -n "$UPSTREAM" ]]; then
        AHEAD=$(git rev-list --count "$UPSTREAM"..HEAD 2>/dev/null || echo 0)
        BEHIND=$(git rev-list --count HEAD.."$UPSTREAM" 2>/dev/null || echo 0)
        info "Ahead: $AHEAD  Behind: $BEHIND"
    else
        info "No upstream configured"
    fi

    echo ""
    echo "=== Staged Changes ==="
    git diff --cached --name-status || true

    echo ""
    echo "=== Unstaged Changes ==="
    git diff --name-status || true

    echo ""
    echo "=== Untracked Files ==="
    git ls-files --others --exclude-standard || true

    if [[ $all_flag -eq 1 ]]; then
        info "Multi-repo scan: checking subdirectory git repos..."
        find . -name ".git" -not -path "./.git" -type d 2>/dev/null | while read gitdir; do
            subrepo=$(dirname "$gitdir")
            echo "  Subrepo: $subrepo"
            (cd "$subrepo" && git status --short 2>/dev/null) || true
        done
    fi
}

cmd_commit() {
    require_git_repo
    local message=""
    local files=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -m|--message)
                message="$2"
                shift 2
                ;;
            -f|--files)
                files="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done

    # Stage specific files if -f provided
    if [[ -n "$files" ]]; then
        info "Staging specified files: $files"
        IFS=',' read -ra FILE_LIST <<< "$files"
        for f in "${FILE_LIST[@]}"; do
            f=$(echo "$f" | xargs)  # trim whitespace
            git add -- "$f" || die "Could not stage file: $f"
        done
    fi

    # Check something is staged
    if git diff --cached --quiet; then
        die "No staged changes. Stage files first or use -f to specify files."
    fi

    # Auto-generate message from diff if not provided
    if [[ -z "$message" ]]; then
        DIFF_SUMMARY=$(git diff --cached --stat | head -5)
        CHANGED_FILES=$(git diff --cached --name-only | head -3 | tr '\n' ' ')
        message="chore: update ${CHANGED_FILES}"
        info "Auto-generated message: $message"
    fi

    # Validate conventional commit format
    if ! validate_conventional_commit "$message"; then
        die "Commit message does not follow Conventional Commits format.
Expected: <type>[optional scope]: <description>
Valid types: feat, fix, refactor, docs, chore, test
Example: fix(auth): patch token validation vulnerability
Got: $message"
    fi

    # Perform commit
    COMMIT_HASH=$(git commit -m "$message" | grep -oP '(?<=\[)[^\]]+' | head -1 || true)
    info "Committed successfully"
    info "Message: $message"
    git log --oneline -1
}

cmd_push() {
    require_git_repo
    local force=0

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force) force=1; shift ;;
            *) shift ;;
        esac
    done

    BRANCH=$(git rev-parse --abbrev-ref HEAD)

    if [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]]; then
        if [[ $force -eq 0 ]]; then
            info "WARNING: You are pushing directly to protected branch '$BRANCH'."
            info "Use --force to override this warning and push anyway."
            exit 1
        fi
    fi

    REMOTE=$(git remote | head -1 || echo "")
    if [[ -z "$REMOTE" ]]; then
        die "No remote configured. Add a remote with: git remote add origin <url>"
    fi

    git push "$REMOTE" "$BRANCH" 2>&1 || die "Push failed. Check for upstream conflicts or auth issues."
    info "Pushed $BRANCH to $REMOTE successfully."
}

cmd_log() {
    require_git_repo
    local count=10
    local author=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -n|--number)
                count="$2"
                shift 2
                ;;
            --author)
                author="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done

    echo "=== git-auto log (last $count commits) ==="
    if [[ -n "$author" ]]; then
        git log --oneline --decorate -n "$count" --author="$author"
    else
        git log --oneline --decorate -n "$count"
    fi
    echo "=== end of log ==="
}

cmd_diff() {
    require_git_repo
    local mode="staged"
    local range=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --unstaged) mode="unstaged"; shift ;;
            --staged)   mode="staged";   shift ;;
            *)
                # could be a branch range like main..feature
                if echo "$1" | grep -q '\.\.'; then
                    range="$1"
                    mode="range"
                fi
                shift
                ;;
        esac
    done

    case "$mode" in
        staged)
            echo "=== Staged Changes (diff) ==="
            git diff --cached
            ;;
        unstaged)
            echo "=== Unstaged Changes (diff) ==="
            git diff
            ;;
        range)
            echo "=== Diff: $range ==="
            git diff "$range"
            ;;
    esac
}

# ── dispatch ──────────────────────────────────────────────────────────────────
SUBCOMMAND="${1:-help}"
shift || true

case "$SUBCOMMAND" in
    status) cmd_status "$@" ;;
    commit) cmd_commit "$@" ;;
    push)   cmd_push   "$@" ;;
    log)    cmd_log    "$@" ;;
    diff)   cmd_diff   "$@" ;;
    help|--help|-h)
        cat << 'HELP'
git-auto v1.0.0 — Git Workspace Automation

Commands:
  status [--all]                  Show workspace status
  commit [-m "msg"] [-f "files"]  Commit staged or specified files
  push [--force]                  Push with safety checks
  log [-n N] [--author name]      View formatted commit log
  diff [--unstaged] [branch..br]  Show diffs

Commit message must follow Conventional Commits format:
  feat|fix|refactor|docs|chore|test[optional scope]: description
HELP
        ;;
    *)
        die "Unknown command: $SUBCOMMAND. Run 'git-auto help' for usage."
        ;;
esac
GITAUTO_EOF

chmod +x /usr/local/bin/git-auto

echo "git-auto CLI installed at /usr/local/bin/git-auto"
git-auto --help