# Uber Commit Template

## Uber Production Repo Detection

**Uber production repos** (use arh commit template):
- `~/Uber/go-code` or path containing `go-code`
- `~/Uber/web-code` or path containing `web-code`
- Path containing `uber-one`
- Remote matching `github.com/uber-code/*` or `github.uberinternal.com/*`

**Non-production repos** (use simple commit format):
- `~/.claude`, `~/Documents`, `~/dotfiles`, personal repos
- Any repo NOT matching above patterns

## Branch Naming Convention

```
{github-username}/{JIRA-ID}-{feature-name}
```

- `{github-username}`: fetch dynamically via `mcp__github__get_me` (extract `login` field)
- `{JIRA-ID}`: optional Jira ticket ID (e.g., MIRADOR-1710)
- `{feature-name}`: descriptive kebab-case name

Examples: `panktib/first_feature`, `yatharth-saluja_UBER/MIRADOR-1710-template-render`

arh automatically extracts Jira ticket numbers from branch names when present.

## PR Metadata (Uber Production Only)

Before committing, use **AskUserQuestion** to gather (skip if already in context):
1. **T3 Ticket ID** — e.g. `T3-123456` or `CODE-1234` (for `Jira Issues:` field)
2. **User Reviewer(s)** — GitHub usernames (for `User Reviewers:` field)

Optional: Group Reviewers, Labels, Revert Plan.

## Commit Template (Uber Production)

```bash
git commit -m "$(cat <<'COMMIT_MSG_7f3a'
{Short description - becomes PR title}

Summary: {Detailed explanation of what and why}
Test Plan: {How to verify changes work}
Jira Issues: {T3-XXXXX or JIRA-XXXX}
User Reviewers: {github-username}
Group Reviewers: {team-name}
Labels: {AutoMerge, ChangesPlanned}
Revert Plan: {How to revert if needed}
API Changes: {Any API changes}
Monitoring and Alerts: {Relevant dashboards/alerts}
COMMIT_MSG_7f3a
)"
```

Only include fields with values. Minimum required: title, Summary, Test Plan, Jira Issues, User Reviewers.

## Commit Template (Non-Production)

```bash
git commit -m "$(cat <<'COMMIT_MSG_7f3a'
{Short description}

{Detailed explanation of changes.}
COMMIT_MSG_7f3a
)"
```

## One-Time Template Setup

```bash
git config --global commit.template ~/.commit_template.txt
```

`~/.commit_template.txt`:
```
Summary:
Test Plan:
Jira Issues:
User Reviewers:
Group Reviewers:
Labels:
Revert Plan:
API Changes:
Monitoring and Alerts:
```
