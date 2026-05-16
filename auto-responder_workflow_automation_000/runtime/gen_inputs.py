import os
import json
import random
import pathlib

random.seed(42)

HOME = pathlib.Path("/root")

# === Create the OpenClaw ecosystem directory structure ===
# Existing agents' workspaces (distractors + reference)
agents = ["healer", "vision", "skynet", "anubis"]

for agent in agents:
    ws = HOME / ".openclaw" / f"workspace-{agent}"
    ws.mkdir(parents=True, exist_ok=True)

# Create a valid reference config for healer (the example from SKILL.md)
healer_config = {
    "enabled": True,
    "respectRequireMention": False,
    "globalCooldownMinutes": 5,
    "maxResponsesPerMinute": 3,
    "topics": {
        "sistema": {
            "thread_ids": [155],
            "mustInclude": ["skynet", "healer", "anubis", "vision"],
            "keywords": ["error", "fallo", "ayuda", "alarma", "crisis", "urge", "sos"],
            "responseTemplate": "💚 [Healer] Detecto necesidad de ayuda. ¿Puedo asistir en algo?"
        },
        "general": {
            "thread_ids": [1],
            "exclude": ["spam", "publicidad"],
            "keywords": ["hola", "ayuda", "problema", "dolor", "triste", "enfermo"],
            "responseTemplate": "💚 [Healer] Estoy aquí para apoyar. Cuéntame más."
        },
        "creatividad": {
            "thread_ids": [158],
            "keywords": ["bloqueo", "sin ideas", "creativo", "arte", "inspiración"],
            "responseTemplate": "💚 [Healer] Parece que necesitas un respiro creativo. ¿Un paseo virtual?"
        }
    },
    "personalidades": {
        "sistema": "estrés operativo",
        "general": "empatía básica",
        "creatividad": "bloqueo artístico"
    }
}

healer_ws = HOME / ".openclaw" / "workspace-healer"
with open(healer_ws / "auto-responder.json", "w") as f:
    json.dump(healer_config, f, indent=2, ensure_ascii=False)

# Create a BROKEN/partial config for nurse (the one agent must fix/create correctly)
nurse_ws = HOME / ".openclaw" / "workspace-nurse"
nurse_ws.mkdir(parents=True, exist_ok=True)

# Broken attempt - missing required fields, wrong types, incomplete
broken_nurse_config = {
    "enabled": False,  # wrong - should be true
    "respectRequireMention": True,  # wrong - blocks unreferenced messages
    "globalCooldownMinutes": "10",  # wrong type - should be int
    "topics": {
        "urgencias": {
            "thread_ids": ["201", "202"],  # wrong type - should be ints
            "keywords": "crisis fallo colapso",  # wrong type - should be list
            # missing responseTemplate
            # missing personalidades
        },
        "bienestar": {
            # missing thread_ids entirely
            "keywords": ["agotado", "estresado", "burnout"],
            "responseTemplate": "Nurse here"  # missing template variables
        }
    }
    # missing personalidades at root level
}

with open(nurse_ws / "auto-responder.json", "w") as f:
    json.dump(broken_nurse_config, f, indent=2, ensure_ascii=False)

# === Create distractor files in various locations ===

# 1. Old cache files
cache_dir = HOME / ".cache"
cache_dir.mkdir(parents=True, exist_ok=True)

old_cache = {
    "responses": [
        {"thread_id": 155, "message_id": 10023, "timestamp": "2024-01-10T10:00:00Z", "agent": "healer"},
        {"thread_id": 1, "message_id": 10045, "timestamp": "2024-01-10T10:05:00Z", "agent": "healer"}
    ]
}
with open(cache_dir / "auto-responder.json", "w") as f:
    json.dump(old_cache, f, indent=2)

# 2. npm global modules mock structure
npm_skills_dir = HOME / ".npm-global" / "lib" / "node_modules" / "openclaw" / "skills" / "auto-responder"
npm_skills_dir.mkdir(parents=True, exist_ok=True)

skill_package = {
    "name": "auto-responder",
    "version": "2.3.1",
    "description": "Auto response skill for OpenClaw agents",
    "main": "index.js",
    "scoreThreshold": 0.6,
    "templateVars": ["{auto}", "{agent}", "{topic}", "{sender}", "{text}"]
}
with open(npm_skills_dir / "package.json", "w") as f:
    json.dump(skill_package, f, indent=2)

with open(npm_skills_dir / "index.js", "w") as f:
    f.write("// auto-responder skill entry point\nmodule.exports = require('./lib/responder');\n")

skill_lib = npm_skills_dir / "lib"
skill_lib.mkdir(exist_ok=True)
with open(skill_lib / "responder.js", "w") as f:
    f.write("""// Core responder logic
const scoreThreshold = 0.6;
// Filters: mustInclude, keywords, exclude
// Cooldown enforced via ~/.cache/auto-responder.json
""")

with open(skill_lib / "scorer.js", "w") as f:
    f.write("// Score = presence(keywords) + recency + frequency\n// Must reach >= 0.6\n")

# 3. Other agent config files (distractors)
vision_config = {
    "enabled": True,
    "respectRequireMention": False,
    "globalCooldownMinutes": 3,
    "maxResponsesPerMinute": 5,
    "topics": {
        "visual": {
            "thread_ids": [210, 211],
            "keywords": ["imagen", "video", "captura", "pantalla"],
            "responseTemplate": "👁️ [Vision] Analizando contenido visual..."
        }
    },
    "personalidades": {
        "visual": "análisis perceptual"
    }
}
with open(HOME / ".openclaw" / "workspace-vision" / "auto-responder.json", "w") as f:
    json.dump(vision_config, f, indent=2, ensure_ascii=False)

# 4. Agent YAML config files (distractors)
for agent in agents + ["nurse"]:
    agent_yaml_dir = HOME / ".openclaw" / f"workspace-{agent}"
    with open(agent_yaml_dir / "agent.yaml", "w") as f:
        f.write(f"""agent:
  name: {agent}
  version: 1.0.0
  hooks:
    onMessage: "auto-responder --hook"
  heartbeat: 60
""")

# 5. Log files as distractors
logs_dir = HOME / ".openclaw" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
for i in range(5):
    with open(logs_dir / f"agent-{random.choice(agents)}-{i}.log", "w") as f:
        f.write(f"[INFO] 2024-01-{10+i} heartbeat ok\n[INFO] auto-responder --once executed\n")

# 6. A misleading "schema" file with WRONG field names
misleading_schema = HOME / ".openclaw" / "schemas" 
misleading_schema.mkdir(parents=True, exist_ok=True)
with open(misleading_schema / "responder-schema-OLD.json", "w") as f:
    json.dump({
        "$schema": "http://json-schema.org/draft-07/schema#",
        "description": "DEPRECATED v1 schema",
        "properties": {
            "active": {"type": "boolean"},  # wrong name, should be "enabled"
            "cooldown": {"type": "integer"},  # wrong name, should be "globalCooldownMinutes"
            "channels": {"type": "object"}   # wrong name, should be "topics"
        }
    }, f, indent=2)

# 7. README for the skill (distractor - provides false hints)
with open(HOME / ".npm-global" / "lib" / "node_modules" / "openclaw" / "skills" / "auto-responder" / "README.md", "w") as f:
    f.write("""# auto-responder
See SKILL.md for full documentation.
Place your config at: ~/.openclaw/workspace-{agentname}/auto-responder.json
""")

# 8. Other workspace files
with open(HOME / ".openclaw" / "workspace-nurse" / "memory.json", "w") as f:
    json.dump({"context": [], "lastActive": "2024-01-09T08:00:00Z"}, f, indent=2)

with open(HOME / ".openclaw" / "workspace-nurse" / "profile.json", "w") as f:
    json.dump({
        "name": "Nurse",
        "role": "medical-support",
        "specialization": ["burnout", "wellness", "crisis-response"],
        "assignedTopics": {
            "urgencias": 201,
            "bienestar": 89,
            "general": 1
        }
    }, f, indent=2)

# 9. A tasks file with topic thread_id hints
with open(HOME / ".openclaw" / "workspace-nurse" / "tasks.json", "w") as f:
    json.dump({
        "pendingTopics": [
            {"name": "urgencias", "thread_id": 201, "priority": "high"},
            {"name": "bienestar", "thread_id": 89, "priority": "medium"},
            {"name": "general", "thread_id": 1, "priority": "low"}
        ]
    }, f, indent=2)

# 10. Global openclaw config
with open(HOME / ".openclaw" / "config.yaml", "w") as f:
    f.write("""global:
  requireMention: false
  defaultCooldownMinutes: 5
  maxResponsesPerMinute: 3
  cacheDir: ~/.cache
  workspaceBase: ~/.openclaw
""")

print("Workspace generated successfully.")
print(f"Nurse broken config at: {nurse_ws / 'auto-responder.json'}")