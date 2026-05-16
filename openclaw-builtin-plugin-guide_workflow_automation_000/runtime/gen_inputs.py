import os
import json
import stat

workspace = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "openclaw-main/src/plugins",
    "openclaw-main/docs",
    "openclaw-main/tests",
    "openclaw-main/config",
    "openclaw-main/node_modules/.cache",
    "logs/2024-01",
    "logs/2024-02",
    "deploy/helm",
    "deploy/docker",
    "ci/.github/workflows",
    "internal/notes",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "openclaw-main/docs/architecture.md": "# OpenClaw Architecture\n\nThis document describes the internal architecture.",
    "openclaw-main/docs/contributing.md": "# Contributing\n\nPlease read our contribution guidelines.",
    "openclaw-main/config/default.yaml": "server:\n  port: 3000\n  host: localhost\nplugins:\n  autoload: true\n",
    "openclaw-main/config/production.yaml": "server:\n  port: 8080\nplugins:\n  autoload: false\n",
    "openclaw-main/tests/plugin_test.js": "// placeholder test\ndescribe('plugins', () => { it('loads', () => {}); });",
    "openclaw-main/src/plugins/loader.js": "// plugin loader stub\nmodule.exports = {};",
    "openclaw-main/node_modules/.cache/meta.json": '{"version":"1.0.0"}',
    "logs/2024-01/app.log": "2024-01-15 INFO  server started\n2024-01-15 WARN  plugin discord failed to init\n",
    "logs/2024-02/app.log": "2024-02-01 INFO  server started\n2024-02-01 INFO  all plugins loaded\n",
    "deploy/helm/values.yaml": "replicaCount: 2\nimage:\n  repository: openclaw\n  tag: latest\n",
    "deploy/docker/docker-compose.yml": "version: '3'\nservices:\n  openclaw:\n    image: openclaw:latest\n    ports:\n      - '3000:3000'\n",
    "ci/.github/workflows/build.yml": "name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n",
    "internal/notes/meeting_2024.txt": "Meeting notes: discussed plugin strategy for Q2.",
    "internal/notes/todo.txt": "- Review disabled plugins\n- Update docs\n",
}
for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── references/builtin-plugins.md ────────────────────────────────────────────
builtin_plugins_md = """\
# OpenClaw 内置插件参考文档

## 插件总览

OpenClaw 内置以下插件（共 8 个）：

| 插件 ID          | 中文名         | 类别       |
|-----------------|---------------|-----------|
| discord          | Discord 集成   | 渠道通知   |
| openclaw-qqbot   | QQ 机器人      | 渠道通知   |
| webhook-relay    | Webhook 中转   | 数据传输   |
| cron-scheduler   | 定时任务调度   | 自动化     |
| log-archiver     | 日志归档       | 运维工具   |
| alert-dispatcher | 告警分发       | 监控       |
| metrics-exporter | 指标导出       | 可观测性   |
| auth-bridge      | 认证桥接       | 安全       |

## 插件详细说明

### discord
用于将 OpenClaw 事件推送至 Discord 频道。支持 Webhook 和 Bot Token 两种接入方式，
可配置多个频道映射。常见配置项包括 `webhook_url`、`bot_token`、`channel_id`。

### openclaw-qqbot
通过 go-cqhttp 协议与 QQ 机器人对接，支持群消息和私聊消息的双向同步。
常见配置项：`ws_url`（WebSocket 地址）、`access_token`、`group_id`。
注意：需要独立部署 go-cqhttp 实例。

### webhook-relay
接收外部 HTTP Webhook，并将事件路由到内部处理管道。
支持 HMAC 签名验证，可配置多个上游端点。

### cron-scheduler
基于 cron 表达式的定时任务调度插件，支持任务的并发控制和失败重试。

### log-archiver
将运行日志定期归档至对象存储（S3/OSS/MinIO）或本地压缩包。

### alert-dispatcher
接收告警事件并按规则分发给不同渠道（邮件、短信、Webhook）。

### metrics-exporter
以 Prometheus 格式暴露 OpenClaw 内部运行指标。

### auth-bridge
对接外部认证服务（LDAP/OIDC），为 OpenClaw 提供统一登录能力。
"""
with open(os.path.join(workspace, "references/builtin-plugins.md"), "w") as f:
    f.write(builtin_plugins_md)

# ── mock openclaw CLI ─────────────────────────────────────────────────────────
# This simulates `openclaw plugins list --json` and `openclaw plugins inspect <id> --json`
mock_openclaw_script = r"""#!/usr/bin/env python3
import sys
import json

PLUGINS = [
    {"id": "discord",          "enabled": True,  "status": "running", "version": "1.2.0"},
    {"id": "openclaw-qqbot",   "enabled": True,  "status": "error",   "version": "0.9.1",
     "error": "WebSocket connection refused: ws://localhost:5700"},
    {"id": "webhook-relay",    "enabled": True,  "status": "running", "version": "2.0.3"},
    {"id": "cron-scheduler",   "enabled": False, "status": "stopped", "version": "1.0.5"},
    {"id": "log-archiver",     "enabled": False, "status": "stopped", "version": "1.1.0"},
    {"id": "alert-dispatcher", "enabled": True,  "status": "running", "version": "1.3.2"},
    {"id": "metrics-exporter", "enabled": False, "status": "stopped", "version": "0.8.0"},
    {"id": "auth-bridge",      "enabled": True,  "status": "running", "version": "1.0.0"},
]

INSPECT_DETAILS = {
    "discord": {
        "id": "discord",
        "enabled": True,
        "status": "running",
        "version": "1.2.0",
        "capabilities": ["send_message", "receive_event", "webhook"],
        "config_schema": {"webhook_url": "string", "bot_token": "string", "channel_id": "string"},
        "description": "Discord channel integration plugin."
    },
    "openclaw-qqbot": {
        "id": "openclaw-qqbot",
        "enabled": True,
        "status": "error",
        "version": "0.9.1",
        "error": "WebSocket connection refused: ws://localhost:5700",
        "capabilities": ["send_message", "receive_message", "group_sync"],
        "config_schema": {"ws_url": "string", "access_token": "string", "group_id": "integer"},
        "description": "QQ bot integration via go-cqhttp protocol."
    },
    "webhook-relay": {
        "id": "webhook-relay",
        "enabled": True,
        "status": "running",
        "version": "2.0.3",
        "capabilities": ["http_ingest", "hmac_verify", "route"],
        "config_schema": {"upstream_url": "string", "secret": "string"},
        "description": "Relay external webhooks to internal pipeline."
    },
    "cron-scheduler": {
        "id": "cron-scheduler",
        "enabled": False,
        "status": "stopped",
        "version": "1.0.5",
        "capabilities": ["schedule", "retry", "concurrency_control"],
        "config_schema": {"cron_expr": "string", "max_retries": "integer"},
        "description": "Cron-based task scheduler."
    },
    "log-archiver": {
        "id": "log-archiver",
        "enabled": False,
        "status": "stopped",
        "version": "1.1.0",
        "capabilities": ["archive", "compress", "upload"],
        "config_schema": {"storage_type": "string", "bucket": "string"},
        "description": "Periodic log archival to object storage."
    },
    "alert-dispatcher": {
        "id": "alert-dispatcher",
        "enabled": True,
        "status": "running",
        "version": "1.3.2",
        "capabilities": ["dispatch", "filter", "multi_channel"],
        "config_schema": {"channels": "array"},
        "description": "Dispatches alerts to configured channels."
    },
    "metrics-exporter": {
        "id": "metrics-exporter",
        "enabled": False,
        "status": "stopped",
        "version": "0.8.0",
        "capabilities": ["prometheus", "scrape"],
        "config_schema": {"port": "integer", "path": "string"},
        "description": "Exports metrics in Prometheus format."
    },
    "auth-bridge": {
        "id": "auth-bridge",
        "enabled": True,
        "status": "running",
        "version": "1.0.0",
        "capabilities": ["ldap", "oidc", "sso"],
        "config_schema": {"provider": "string", "endpoint": "string"},
        "description": "Bridges external auth providers."
    },
}

args = sys.argv[1:]

if not args:
    print("Usage: openclaw <command>", file=sys.stderr)
    sys.exit(1)

# openclaw plugins list --json
if args[0] == "plugins" and len(args) >= 2 and args[1] == "list":
    print(json.dumps(PLUGINS, indent=2))
    sys.exit(0)

# openclaw plugins inspect <id> --json
if args[0] == "plugins" and len(args) >= 3 and args[1] == "inspect":
    plugin_id = args[2]
    if plugin_id in INSPECT_DETAILS:
        print(json.dumps(INSPECT_DETAILS[plugin_id], indent=2))
        sys.exit(0)
    else:
        print(json.dumps({"error": f"Plugin '{plugin_id}' not found"}), file=sys.stderr)
        sys.exit(1)

print(f"Unknown command: {' '.join(args)}", file=sys.stderr)
sys.exit(1)
"""

mock_openclaw_path = os.path.join(workspace, "scripts/openclaw")
with open(mock_openclaw_path, "w") as f:
    f.write(mock_openclaw_script)
os.chmod(mock_openclaw_path, 0o755)

# ── scripts/openclaw_plugin_catalog.py ───────────────────────────────────────
catalog_script = r"""#!/usr/bin/env python3
"""
catalog_script += r"""
import argparse
import json
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCES_PATH = os.path.join(BASE_DIR, "references", "builtin-plugins.md")
OPENCLAW_BIN = os.path.join(BASE_DIR, "scripts", "openclaw")

def run_openclaw(*args):
    result = subprocess.run(
        [OPENCLAW_BIN] + list(args),
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return json.loads(result.stdout)

def cmd_bundled(fmt):
    plugins = run_openclaw("plugins", "list", "--json")
    if fmt == "json":
        print(json.dumps(plugins, indent=2))
    else:
        print(f"{'ID':<22} {'ENABLED':<10} {'STATUS':<12} VERSION")
        print("-" * 60)
        for p in plugins:
            print(f"{p['id']:<22} {str(p['enabled']):<10} {p['status']:<12} {p['version']}")

def cmd_status(state, fmt):
    plugins = run_openclaw("plugins", "list", "--json")
    if state == "enabled":
        filtered = [p for p in plugins if p.get("enabled") == True]
    elif state == "disabled":
        filtered = [p for p in plugins if p.get("enabled") == False]
    else:
        filtered = plugins
    if fmt == "json":
        print(json.dumps(filtered, indent=2))
    else:
        print(f"{'ID':<22} {'ENABLED':<10} {'STATUS':<12} VERSION")
        print("-" * 60)
        for p in filtered:
            print(f"{p['id']:<22} {str(p['enabled']):<10} {p['status']:<12} {p['version']}")

def cmd_inspect(plugin_id, fmt):
    # Step 1: read reference doc
    ref_section = ""
    if os.path.exists(REFERENCES_PATH):
        with open(REFERENCES_PATH) as f:
            content = f.read()
        # extract the section for this plugin
        marker = f"### {plugin_id}"
        if marker in content:
            start = content.index(marker)
            end = content.find("\n### ", start + len(marker))
            ref_section = content[start:end if end != -1 else len(content)].strip()

    # Step 2: runtime info
    runtime = run_openclaw("plugins", "inspect", plugin_id, "--json")

    # Step 3: determine status description
    enabled = runtime.get("enabled", False)
    status = runtime.get("status", "unknown")
    if enabled and status == "error":
        status_desc = "已启用，但加载失败"
    elif enabled:
        status_desc = "已启用"
    else:
        status_desc = "已禁用"

    result = {
        "id": plugin_id,
        "status_description": status_desc,
        "runtime": runtime,
        "reference_doc": ref_section,
    }

    if fmt == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Plugin: {plugin_id}")
        print(f"Status: {status_desc}")
        if ref_section:
            print(f"\n--- Reference ---\n{ref_section}")
        print(f"\n--- Runtime ---")
        print(json.dumps(runtime, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Plugin Catalog")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("bundled")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--state", choices=["enabled", "disabled", "all"], default="all")

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("plugin_id")

    args = parser.parse_args()

    if args.command == "bundled":
        cmd_bundled(args.format)
    elif args.command == "status":
        cmd_status(args.state, args.format)
    elif args.command == "inspect":
        cmd_inspect(args.plugin_id, args.format)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
"""

catalog_path = os.path.join(workspace, "scripts/openclaw_plugin_catalog.py")
with open(catalog_path, "w") as f:
    f.write(catalog_script)
os.chmod(catalog_path, 0o755)

print("Workspace generated successfully.")
print(f"  - {workspace}/scripts/openclaw  (mock CLI)")
print(f"  - {workspace}/scripts/openclaw_plugin_catalog.py")
print(f"  - {workspace}/references/builtin-plugins.md")
print(f"  + {len(distractors)} distractor files")