import os
import json
import random
import pathlib

random.seed(42)

workspace = "/workspace"

# ── 1. Create the OpenClaw workspace scaffold (WITHOUT the correct extension dir)
openclaw_home = pathlib.Path(os.path.expanduser("~/.openclaw"))
openclaw_home.mkdir(parents=True, exist_ok=True)

# Create the workspace directory (but NOT the extensions subdirectory)
(openclaw_home / "workspace").mkdir(parents=True, exist_ok=True)

# Create a BROKEN / incomplete openclaw.json — it exists but lacks plugins.entries
openclaw_cfg = {
    "version": "2.1.0",
    "gateway": {
        "port": 3000,
        "host": "localhost",
        "logLevel": "info"
    },
    "channels": {
        "webchat": {"enabled": True},
        "telegram": {"enabled": False}
    },
    "plugins": {
        "autoLoad": True
    }
}

with open(openclaw_home / "openclaw.json", "w") as f:
    json.dump(openclaw_cfg, f, indent=2)

# ── 2. Create the scripts/ directory in /workspace with the plugin source files
scripts_dir = pathlib.Path(workspace) / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# index.ts — realistic TypeScript plugin source
index_ts_content = """\
import { Plugin, PluginContext } from '@openclaw/sdk';

interface MessageInjectorConfig {
  enabled: boolean;
  prependText: string;
}

const plugin: Plugin<MessageInjectorConfig> = {
  name: 'message-injector',
  version: '1.0.0',
  hooks: {
    before_agent_start: async (ctx: PluginContext, config: MessageInjectorConfig) => {
      if (!config.enabled || !config.prependText) {
        return {};
      }
      return {
        prependContext: config.prependText
      };
    }
  }
};

export default plugin;
"""

with open(scripts_dir / "index.ts", "w") as f:
    f.write(index_ts_content)

# openclaw.plugin.json — plugin manifest
plugin_manifest = {
    "name": "message-injector",
    "version": "1.0.0",
    "description": "Prepends custom text to every user message before agent processing",
    "author": "Harukaon",
    "main": "index.ts",
    "hooks": ["before_agent_start"],
    "configSchema": {
        "enabled": {"type": "boolean", "default": True},
        "prependText": {"type": "string", "default": ""}
    }
}

with open(scripts_dir / "openclaw.plugin.json", "w") as f:
    json.dump(plugin_manifest, f, indent=2)

# ── 3. Create deeply nested distractor files to test contextual awareness
distractors = [
    "workspace/projects/legal-ai/prompts/system_prompt.txt",
    "workspace/projects/legal-ai/prompts/user_template.txt",
    "workspace/projects/legal-ai/config/db.json",
    "workspace/projects/legal-ai/config/auth.json",
    "workspace/logs/gateway.log",
    "workspace/logs/error.log",
    "workspace/cache/session_abc123.json",
    "workspace/cache/session_def456.json",
    "workspace/extensions/old-plugin/index.js",       # WRONG location distractor
    "workspace/extensions/old-plugin/manifest.json",  # WRONG location distractor
    "workspace/.openclaw/extensions/wrong-name/index.ts",  # partially correct but wrong plugin name
]

distractor_contents = {
    "workspace/projects/legal-ai/prompts/system_prompt.txt": "You are a helpful legal assistant. Always be precise.",
    "workspace/projects/legal-ai/prompts/user_template.txt": "Question: {user_query}\nContext: {context}",
    "workspace/projects/legal-ai/config/db.json": json.dumps({"host": "localhost", "port": 5432, "db": "legalai"}),
    "workspace/projects/legal-ai/config/auth.json": json.dumps({"jwt_secret": "REDACTED", "session_ttl": 3600}),
    "workspace/logs/gateway.log": "2024-01-15 10:23:11 INFO Gateway started on port 3000\n2024-01-15 10:23:12 INFO Plugins loaded: 0\n",
    "workspace/logs/error.log": "2024-01-14 09:11:02 ERROR Plugin 'message-injector' not found in extensions directory\n",
    "workspace/cache/session_abc123.json": json.dumps({"user": "attorney_jones", "ts": 1705312800}),
    "workspace/cache/session_def456.json": json.dumps({"user": "paralegal_smith", "ts": 1705399200}),
    "workspace/extensions/old-plugin/index.js": "module.exports = { name: 'old-plugin', hook: () => {} };",
    "workspace/extensions/old-plugin/manifest.json": json.dumps({"name": "old-plugin", "version": "0.1.0"}),
    "workspace/.openclaw/extensions/wrong-name/index.ts": "// Wrong plugin placement — do not use",
}

for rel_path, content in distractor_contents.items():
    full_path = pathlib.Path("/") / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# Also add a misleading partial config that looks like it could be the answer
misleading_plugin_cfg = {
    "plugins": {
        "message-injector": {
            "enabled": True,
            "prependText": "[COMPLIANCE STUB - NOT ACTIVE]"
        }
    }
}

with open(pathlib.Path("/workspace/.openclaw/extensions/wrong-name/") / "plugin_config.json", "w") as f:
    json.dump(misleading_plugin_cfg, f, indent=2)

# ── 4. Add a README-free project notes file (not a hint, just context noise)
with open(pathlib.Path(workspace) / "NOTES.txt", "w") as f:
    f.write(
        "Legal AI Platform - Internal Notes\n"
        "=====================================\n"
        "Contact: infra@legalfirm.example.com\n"
        "Gateway version: 2.1.0\n"
        "Last deployment: 2024-01-10\n"
        "TODO: Set up mandatory compliance message injection for all AI channels\n"
        "TODO: Ensure all attorney queries include source-citation reminder\n"
    )

print("Workspace scaffold generated successfully.")
print(f"  - Plugin source files: /workspace/scripts/")
print(f"  - OpenClaw config: ~/.openclaw/openclaw.json (incomplete)")
print(f"  - Distractor files: {len(distractors)} created")