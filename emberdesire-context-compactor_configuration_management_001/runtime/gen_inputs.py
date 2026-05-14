import os
import json
import random

random.seed(42)

# --- Create a realistic, deeply nested workspace ---

dirs = [
    "workspace",
    "workspace/.openclaw",
    "workspace/.openclaw/extensions",
    "workspace/.openclaw/extensions/context-compactor",
    "workspace/.openclaw/logs",
    "workspace/.openclaw/sessions",
    "workspace/projects",
    "workspace/projects/mfg-docs",
    "workspace/projects/mfg-docs/jigs",
    "workspace/projects/mfg-docs/assembly",
    "workspace/projects/mfg-docs/qa",
    "workspace/scripts",
    "workspace/scripts/maintenance",
    "workspace/configs",
    "workspace/configs/backups",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---

# Old, broken openclaw.json backup (wrong structure — no plugins key, old format)
old_config_broken = {
    "model": "mlx-community/Qwen2.5-1.5B-Instruct-4bit",
    "gateway": {
        "port": 7777
    },
    "extensions": {
        "context-compactor": {
            "active": True,
            "max_tokens": 4096
        }
    }
}
with open("workspace/configs/backups/openclaw.json.bak", "w") as f:
    json.dump(old_config_broken, f, indent=2)

# Another distractor: a half-filled config with wrong nesting
wrong_nesting = {
    "plugins": {
        "context-compactor": {
            "enabled": True,
            "maxTokens": 8000
        }
    }
}
with open("workspace/configs/backups/openclaw_draft.json", "w") as f:
    json.dump(wrong_nesting, f, indent=2)

# The actual openclaw.json that currently exists — misconfigured with bad defaults for a 4K CJK model
# It has the right top-level structure but wrong values and missing keys
current_openclaw_config = {
    "model": "mlx-community/japanese-stablelm-base-4k",
    "gateway": {
        "port": 7777,
        "host": "127.0.0.1"
    },
    "plugins": {
        "entries": {
            "context-compactor": {
                "enabled": False,
                "config": {
                    "maxTokens": 8000,
                    "keepRecentTokens": 2000,
                    "charsPerToken": 4
                }
            }
        }
    }
}
with open("workspace/.openclaw/openclaw.json", "w") as f:
    json.dump(current_openclaw_config, f, indent=2)

# Distractor: plugin index file (not the config)
plugin_index = {
    "plugins": ["context-compactor", "token-counter", "session-logger"],
    "version": "0.3.8"
}
with open("workspace/.openclaw/extensions/context-compactor/plugin.json", "w") as f:
    json.dump(plugin_index, f, indent=2)

# Distractor: session files (realistic-looking)
for i in range(3):
    session = {
        "id": f"session-{1000+i}",
        "model": "mlx-community/japanese-stablelm-base-4k",
        "messages": [
            {"role": "user", "content": "製造ラインの品質管理手順を説明してください。" * random.randint(1, 5)},
            {"role": "assistant", "content": "品質管理手順は以下の通りです。" * random.randint(1, 5)}
        ]
    }
    with open(f"workspace/.openclaw/sessions/session-{1000+i}.json", "w") as f:
        json.dump(session, f, indent=2)

# Distractor: log file
with open("workspace/.openclaw/logs/gateway.log", "w") as f:
    f.write("[2024-01-15 09:00:01] Gateway started on port 7777\n")
    f.write("[2024-01-15 09:00:02] Model loaded: mlx-community/japanese-stablelm-base-4k\n")
    f.write("[2024-01-15 09:05:33] [context-compactor] Current context: ~3800 tokens\n")
    f.write("[2024-01-15 09:05:33] WARNING: Context nearing limit, truncation may occur\n")
    f.write("[2024-01-15 09:10:11] Session session-1000 started\n")

# Distractor: project files (CJK manufacturing docs)
jig_doc = """治具仕様書
型番: JIG-2024-A3
材質: アルミニウム合金 A6061
精度: ±0.05mm
用途: エンジンブロック組立工程
"""
with open("workspace/projects/mfg-docs/jigs/jig_spec_A3.txt", "w", encoding="utf-8") as f:
    f.write(jig_doc)

assembly_doc = """組立手順書 Rev.4
1. 部品確認
2. 洗浄工程
3. 組立
4. 検査
"""
with open("workspace/projects/mfg-docs/assembly/assembly_rev4.txt", "w", encoding="utf-8") as f:
    f.write(assembly_doc)

qa_doc = """品質保証チェックリスト
□ 寸法検査
□ 表面粗さ測定
□ 硬度試験
"""
with open("workspace/projects/mfg-docs/qa/qa_checklist.txt", "w", encoding="utf-8") as f:
    f.write(qa_doc)

# Distractor: maintenance scripts (red herrings)
with open("workspace/scripts/maintenance/clear_sessions.sh", "w") as f:
    f.write("#!/bin/bash\nrm -f ~/.openclaw/sessions/*.json\necho 'Sessions cleared'\n")

with open("workspace/scripts/maintenance/restart_gateway.sh", "w") as f:
    f.write("#!/bin/bash\nopenclaw gateway restart\necho 'Gateway restarted'\n")

# Distractor: a README about the project (not the tool)
with open("workspace/projects/mfg-docs/PROJECT_NOTES.md", "w") as f:
    f.write("# Manufacturing Documentation AI Assistant\n\nThis project uses a local AI model to process Japanese manufacturing documents.\nDo not share with external parties.\n")

# Distractor: another configs file that could mislead
with open("workspace/configs/model_profiles.json", "w") as f:
    json.dump({
        "profiles": {
            "4k_japanese": {
                "model": "mlx-community/japanese-stablelm-base-4k",
                "context_window": 4096,
                "language": "ja",
                "notes": "CJK-heavy content, small context"
            },
            "8k_english": {
                "model": "mlx-community/Qwen2.5-7B-4bit",
                "context_window": 8192,
                "language": "en"
            }
        }
    }, f, indent=2)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("workspace"):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")