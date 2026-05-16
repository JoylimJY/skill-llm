---
name: arh-pr-workflow
description: Expert guidance for managing Pull Requests and feature branches using Uber's arh CLI tool. Use when creating features, publishing PRs, managing stacked PRs, merging PRs, rebasing branches, running lint/tests, or navigating feature branches in Uber's web-code monorepo.
---

# arh-pr-workflow Skill

Expert guidance for arh CLI — Uber's PR and feature branch management tool.

Create Claude task list using TaskCreate for all items below. Mark tasks complete via TaskUpdate as you go.

- [ ] Parse user request (which arh operation?)
- [ ] Detect environment (Uber production repo?)
- [ ] Execute requested operation
- [ ] Verify result
- [ ] Report outcome

## Branch Naming & Commit Templates

See `references/uber-commit-template.md` for branch naming convention, commit template format, and PR metadata gathering.

## Initial Setup

```bash
arh auth
```

Opens browser for GitHub authorization. Select all needed orgs (e.g., uber-code, uber-objectconfig). GitHub username must end with _UBER suffix.

## Core Capabilities

### 1. Creating Feature Branches

**Create a new feature branch from main:**
```bash
arh feature <feature-name>
```

**Create a stacked feature (branch off current feature):**
```bash
arh feature next <feature-name>
```

**Create feature with specific parent:**
```bash
arh feature <feature-name> --parent <parent-branch>
```

### 2. Publishing Pull Requests

**Publish PR for current feature:**
```bash
arh publish
```

**Publish entire feature stack (root to leaf):**
```bash
arh publish --full-stack
```

**Publish without interactive prompts (auto-apply lint fixes):**
```bash
arh publish --no-interactive
```

**Publish as draft PR:**
```bash
arh publish --changes-planned
```

**Publish with auto-merge enabled:**
```bash
arh publish --auto-merge
```

**Publish with combined flags:**
```bash
arh publish --no-interactive --apply-fixes
arh publish --full-stack --changes-planned
```

### 3. Viewing PR Status

**View feature tree:**
```bash
arh log -p
```

**View feature tree with PR status:**
```bash
arh log -s
# or
arh -s
```

**View with commit history (ahead/behind status):**
```bash
arh log -c
# or
arh -c
```

### 4. Merging Pull Requests

**Merge current feature and all ancestors:**
```bash
arh merge
```

**How it works:**
- If on branch A (main -> C -> B -> A), merges A, B, and C
- If on branch B, merges B and C
- Requires all checks to pass (Builds, Required Approvers)
- Merges ancestors first, then current branch

### 5. Navigating Features

**Checkout existing feature:**
```bash
arh checkout <feature-name>
# or
arh co <feature-name>
```

**Checkout PR from URL (v0.0.38+):**
```bash
arh checkout https://github.com/uber-code/go-code/pull/11960
# or
arh checkout uber-code/go-code/pull/11960
# or
arh checkout 11960
# or
arh checkout username/feature-name
```

This fetches the PR branch from remote and sets up upstream tracking.

**Navigate feature stack:**
```bash
arh checkout next    # Next feature in tree
arh checkout prev    # Previous feature in tree
arh checkout first   # First feature in tree
arh checkout last    # Last feature in tree
```

### 6. Rebasing Features

**Rebase current feature tree to latest parent:**
```bash
arh rebase
```

**Pull and rebase from default branch:**
```bash
arh pull -r
```
This pulls latest changes from origin main and rebases the entire feature stack.

**Important for go-code monorepo:** After any `git pull` or `arh pull`, always run:
```bash
git-bzl refresh
```

**Rebase to new parent:**
```bash
arh rebase --parent <new-parent-branch>
```

**Rebase specific feature:**
```bash
arh rebase --feature <feature-branch-name>
```

**Rebase entire stack:**
```bash
arh rebase --base <base-branch>
```

**Rebase subtree:**
```bash
arh rebase --subtree <subtree-root>
```

**Rebase all features:**
```bash
arh rebase --all
```

### 7. Discarding Features

**Discard a feature branch:**
```bash
arh discard -f <feature-name>
```

**Important:** This deletes both local and remote branches. Any PRs open from this branch will be closed.

**Discard local only (keep remote):**
```bash
arh discard --skip-remote -f <feature-name>
```

Use `--skip-remote` when checking out someone else's PR branch that you want to discard locally.

### 8. Cleaning Up Merged Features

**Clean up merged/closed feature branches:**
```bash
arh tidy
```

**Clean up without prompts:**
```bash
arh tidy --no-interactive
```

**How it works:**
- Lists all closed/merged features
- Asks for confirmation to discard
- Updates upstream tracking for dependent branches
- Example: main -> A -> B -> C, if B is closed, tidy discards B and updates C's parent to A

### 9. Running Quality Checks

**Run linters on changed files:**
```bash
arh lint
```

**Run tests on changed files:**
```bash
arh test
```

### 10. Version Management

**Check arh version:**
```bash
arh version
# or
arh -v
```

## Common Workflows

- **New feature**: `arh feature NAME` -> commit -> `arh publish`
- **Stacked PRs**: `arh feature NAME` -> commit -> `arh feature next NAME2` -> commit -> `arh publish --full-stack`
- **Update after review**: commit fixes -> `arh publish --no-interactive`
- **Merge stack**: `arh checkout last` -> `arh merge` -> `arh tidy`
- **Rebase on main**: `arh rebase` or `arh rebase --all`, then `arh publish --no-interactive`

## Troubleshooting

**PR publish fails due to lint errors:**
```bash
arh publish --apply-fixes  # Auto-apply lint fixes
```

**Skip pre-push coverage check** (`/opt/uber/etc/custom-hooks/coverage-check.sh`):
```bash
arh publish --no-coverage             # Skip coverage via wrapper (preferred)
SKIP_COVERAGE=1 arh publish           # Skip coverage via env var
COVERAGE_THRESHOLD=70 arh publish     # Lower threshold (default: 80%)
```
The `--no-coverage` flag is handled by an `arh()` shell wrapper in `~/.aliases` that creates a marker file (`/tmp/.skip-coverage-$(id -u)`) consumed by the pre-push hook.
Aliases: `arh-nc` (no coverage), `arh-lc` (lower threshold) — also in `~/.aliases`.

**Feature tree is messy:**
```bash
arh -s              # Check status
arh tidy            # Clean up merged features
arh rebase --all    # Rebase everything
```

**Cannot merge due to failing checks:**
- Check build status: `arh -s`
- Ensure all required approvals are received
- Verify all builds are passing
- Fix issues and update PR: `arh publish`

## Tips

- Always create features with `arh feature` for proper parent tracking
- Use `arh -s` frequently to monitor PR status
- Use `--no-interactive` in automated/CI contexts
- Use `--changes-planned` for WIP/draft PRs
- Run `arh tidy` regularly to keep feature tree clean
- Use `--full-stack` for dependent changes
- **go-code monorepo:** After `git pull` or `arh pull`, MUST run `git-bzl refresh`
