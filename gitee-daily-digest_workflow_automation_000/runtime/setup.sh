#!/bin/bash
set -e

# Create the mock mcporter binary that the agent must discover and use
cat > /usr/local/bin/mcporter << 'MCPORTER_EOF'
#!/usr/bin/env python3
"""
Mock mcporter CLI - simulates Gitee MCP Server tool invocations.
Usage: mcporter call <server> <tool> [--param key=value ...]
"""
import sys
import json
import argparse

def get_user_info():
    return {
        "id": 10042,
        "login": "zhang_wei",
        "name": "Zhang Wei",
        "email": "zhang.wei@fintech-corp.com",
        "avatar_url": "https://gitee.com/assets/avatar.png",
        "followers": 23,
        "following": 15
    }

def list_user_notifications(unread=None, **kwargs):
    notifications = [
        {
            "id": "notif_001",
            "unread": True,
            "reason": "mention",
            "subject": {
                "title": "Fix: race condition in payment processor",
                "type": "PullRequest",
                "url": "https://gitee.com/fintech-corp/payment-gateway/pulls/87"
            },
            "repository": {
                "full_name": "fintech-corp/payment-gateway",
                "name": "payment-gateway"
            },
            "updated_at": "2024-06-10T09:15:00+08:00"
        },
        {
            "id": "notif_002",
            "unread": True,
            "reason": "comment",
            "subject": {
                "title": "Add KYC validation endpoint",
                "type": "PullRequest",
                "url": "https://gitee.com/fintech-corp/fintech-core/pulls/134"
            },
            "repository": {
                "full_name": "fintech-corp/fintech-core",
                "name": "fintech-core"
            },
            "updated_at": "2024-06-10T08:50:00+08:00"
        },
        {
            "id": "notif_003",
            "unread": True,
            "reason": "mention",
            "subject": {
                "title": "Transaction logs not persisted after service restart",
                "type": "Issue",
                "url": "https://gitee.com/fintech-corp/fintech-core/issues/I7XK2"
            },
            "repository": {
                "full_name": "fintech-corp/fintech-core",
                "name": "fintech-core"
            },
            "updated_at": "2024-06-10T08:30:00+08:00"
        },
        {
            "id": "notif_004",
            "unread": True,
            "reason": "comment",
            "subject": {
                "title": "Implement retry logic for failed transactions",
                "type": "Issue",
                "url": "https://gitee.com/fintech-corp/payment-gateway/issues/I9QP1"
            },
            "repository": {
                "full_name": "fintech-corp/payment-gateway",
                "name": "payment-gateway"
            },
            "updated_at": "2024-06-10T07:45:00+08:00"
        },
        {
            "id": "notif_005",
            "unread": False,
            "reason": "comment",
            "subject": {
                "title": "Old resolved issue",
                "type": "Issue",
                "url": "https://gitee.com/fintech-corp/fintech-core/issues/I5AA1"
            },
            "repository": {
                "full_name": "fintech-corp/fintech-core",
                "name": "fintech-core"
            },
            "updated_at": "2024-06-09T12:00:00+08:00"
        }
    ]
    # If unread filter requested
    if unread == "true" or unread is True:
        notifications = [n for n in notifications if n["unread"]]
    return notifications

def list_repo_pulls(owner, repo, state="open", **kwargs):
    all_pulls = {
        ("fintech-corp", "payment-gateway"): [
            {
                "number": 87,
                "title": "Fix: race condition in payment processor",
                "state": "open",
                "user": {"login": "li_fang", "name": "Li Fang"},
                "assignees": [{"login": "zhang_wei"}],
                "reviewers": [{"login": "zhang_wei"}],
                "updated_at": "2024-06-10T09:15:00+08:00",
                "created_at": "2024-06-09T14:00:00+08:00",
                "body": "Fixes a critical race condition found during load testing."
            },
            {
                "number": 85,
                "title": "Refactor: extract payment strategy pattern",
                "state": "open",
                "user": {"login": "zhang_wei"},
                "assignees": [],
                "reviewers": [{"login": "chen_jing"}],
                "updated_at": "2024-06-10T07:20:00+08:00",
                "created_at": "2024-06-08T10:00:00+08:00",
                "body": "Refactoring to improve maintainability."
            },
            {
                "number": 83,
                "title": "chore: update dependencies",
                "state": "open",
                "user": {"login": "bot_user"},
                "assignees": [],
                "reviewers": [],
                "updated_at": "2024-06-07T06:00:00+08:00",
                "created_at": "2024-06-07T06:00:00+08:00",
                "body": "Automated dependency updates."
            }
        ],
        ("fintech-corp", "fintech-core"): [
            {
                "number": 134,
                "title": "Add KYC validation endpoint",
                "state": "open",
                "user": {"login": "zhang_wei"},
                "assignees": [{"login": "wu_lei"}],
                "reviewers": [{"login": "wu_lei"}, {"login": "chen_jing"}],
                "updated_at": "2024-06-10T08:50:00+08:00",
                "created_at": "2024-06-09T09:00:00+08:00",
                "body": "Adds the KYC endpoint as required by compliance."
            },
            {
                "number": 131,
                "title": "feat: add rate limiting middleware",
                "state": "open",
                "user": {"login": "li_fang"},
                "assignees": [{"login": "zhang_wei"}],
                "reviewers": [{"login": "zhang_wei"}],
                "updated_at": "2024-06-10T06:30:00+08:00",
                "created_at": "2024-06-08T16:00:00+08:00",
                "body": "Adds rate limiting to protect API endpoints."
            }
        ]
    }
    key = (owner, repo)
    results = all_pulls.get(key, [])
    if state:
        results = [p for p in results if p["state"] == state]
    return results

def list_repo_issues(owner, repo, state="open", assignee=None, creator=None, **kwargs):
    all_issues = {
        ("fintech-corp", "fintech-core"): [
            {
                "number": "I7XK2",
                "title": "Transaction logs not persisted after service restart",
                "state": "open",
                "user": {"login": "zhang_wei"},
                "assignees": [{"login": "zhang_wei"}],
                "priority": "P1",
                "updated_at": "2024-06-10T08:30:00+08:00",
                "created_at": "2024-06-09T11:00:00+08:00"
            },
            {
                "number": "I7WQ9",
                "title": "API docs out of sync with implementation",
                "state": "open",
                "user": {"login": "zhang_wei"},
                "assignees": [{"login": "zhang_wei"}],
                "priority": "P2",
                "updated_at": "2024-06-09T16:00:00+08:00",
                "created_at": "2024-06-08T09:00:00+08:00"
            },
            {
                "number": "I6KP5",
                "title": "Improve test coverage for auth module",
                "state": "open",
                "user": {"login": "wu_lei"},
                "assignees": [{"login": "chen_jing"}],
                "priority": "P3",
                "updated_at": "2024-06-08T10:00:00+08:00",
                "created_at": "2024-06-07T10:00:00+08:00"
            }
        ],
        ("fintech-corp", "payment-gateway"): [
            {
                "number": "I9QP1",
                "title": "Implement retry logic for failed transactions",
                "state": "open",
                "user": {"login": "chen_jing"},
                "assignees": [{"login": "zhang_wei"}],
                "priority": "P1",
                "updated_at": "2024-06-10T07:45:00+08:00",
                "created_at": "2024-06-09T14:30:00+08:00"
            },
            {
                "number": "I8MX3",
                "title": "Add webhook support for payment events",
                "state": "open",
                "user": {"login": "zhang_wei"},
                "assignees": [],
                "priority": "P2",
                "updated_at": "2024-06-09T12:00:00+08:00",
                "created_at": "2024-06-08T14:00:00+08:00"
            }
        ]
    }
    key = (owner, repo)
    results = all_issues.get(key, [])
    if state:
        results = [i for i in results if i["state"] == state]
    # Filter by assignee (username)
    if assignee:
        results = [i for i in results if any(a["login"] == assignee for a in i.get("assignees", []))]
    # Filter by creator
    if creator:
        results = [i for i in results if i["user"]["login"] == creator]
    return results

def main():
    if len(sys.argv) < 4:
        print("Usage: mcporter call <server> <tool> [--param key=value ...]", file=sys.stderr)
        sys.exit(1)
    
    subcmd = sys.argv[1]
    if subcmd != "call":
        print(f"Unknown subcommand: {subcmd}", file=sys.stderr)
        sys.exit(1)

    server = sys.argv[2]
    tool = sys.argv[3]
    
    # Parse --param key=value arguments
    params = {}
    i = 4
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--param" and i + 1 < len(sys.argv):
            kv = sys.argv[i+1]
            if "=" in kv:
                k, v = kv.split("=", 1)
                params[k] = v
            i += 2
        else:
            i += 1

    if server != "gitee":
        print(json.dumps({"error": f"Unknown server: {server}"}))
        sys.exit(1)

    result = None
    if tool == "get_user_info":
        result = get_user_info()
    elif tool == "list_user_notifications":
        result = list_user_notifications(**params)
    elif tool == "list_repo_pulls":
        owner = params.get("owner", "")
        repo = params.get("repo", "")
        state = params.get("state", "open")
        result = list_repo_pulls(owner, repo, state)
    elif tool == "list_repo_issues":
        owner = params.get("owner", "")
        repo = params.get("repo", "")
        state = params.get("state", "open")
        assignee = params.get("assignee", None)
        creator = params.get("creator", None)
        result = list_repo_issues(owner, repo, state, assignee=assignee, creator=creator)
    else:
        print(json.dumps({"error": f"Unknown tool: {tool}"}))
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
MCPORTER_EOF

chmod +x /usr/local/bin/mcporter

echo "mcporter mock installed successfully."
mcporter call gitee get_user_info | head -5
echo "Setup complete."