#!/usr/bin/env python3
"""
Generates the mock OpenClaw environment and workspace for the Matrix mentions patch task.
All paths use /root as HOME to match the Docker container.
"""

import os
import stat
import random
import string

random.seed(42)

HOME = "/root"

# ─── 1. NVM / OpenClaw mock directory structure ───────────────────────────────

OPENCLAW_BASE = f"{HOME}/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw"

# dist/ — target patching location
DIST_DIR = f"{OPENCLAW_BASE}/dist"
os.makedirs(DIST_DIR, exist_ok=True)

# The auth-profiles-*.js file (glob pattern; use a fixed hash for determinism)
AUTH_PROFILES_HASH = "e3f7a912"
AUTH_PROFILES_FILE = f"{DIST_DIR}/auth-profiles-{AUTH_PROFILES_HASH}.js"

# Realistic unpatched JS bundle content (minified, realistic)
unpatched_js = r"""
"use strict";
Object.defineProperty(exports,"__esModule",{value:true});
const crypto=require("crypto");
const events=require("events");

class AuthProfileManager extends events.EventEmitter {
  constructor(opts){
    super();
    this.profiles=new Map();
    this.opts=opts||{};
  }
  loadProfile(id,data){
    this.profiles.set(id,{...data,loadedAt:Date.now()});
    this.emit("profile:loaded",id);
  }
  sendMatrixMessage(roomId,content,mentions){
    const payload={
      type:"m.room.message",
      content:{
        msgtype:"m.text",
        body:content
      }
    };
    // TODO: attach m.mentions for proper notification routing
    return this._dispatch(roomId,payload);
  }
  _dispatch(roomId,payload){
    return new Promise((resolve)=>{
      setTimeout(()=>resolve({event_id:"$"+crypto.randomBytes(8).toString("hex")}),10);
    });
  }
}
exports.AuthProfileManager=AuthProfileManager;
exports.version="4.2.1";
exports.buildHash="e3f7a912";
"""

with open(AUTH_PROFILES_FILE, "w") as f:
    f.write(unpatched_js)

# extensions/matrix/src/matrix/send/formatting.ts — patch status check target
FORMATTING_DIR = f"{OPENCLAW_BASE}/extensions/matrix/src/matrix/send"
os.makedirs(FORMATTING_DIR, exist_ok=True)
FORMATTING_FILE = f"{FORMATTING_DIR}/formatting.ts"

unpatched_ts = r"""
import { MatrixClient } from "matrix-js-sdk";

export interface FormattedMessage {
  body: string;
  formatted_body?: string;
  format?: string;
}

/**
 * Formats a plain-text message for Matrix transport.
 * Handles escaping and optional HTML formatting.
 */
export function formatMessageBody(text: string): FormattedMessage {
  const escaped = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return { body: escaped };
}

/**
 * Parses inline @mentions from message text and returns Matrix user IDs.
 * Currently a stub — does not populate m.mentions field.
 */
export function parseMentionCandidates(text: string): string[] {
  // Naive regex — does not produce valid m.mentions objects
  const re = /@[\w.-]+:[\w.-]+/g;
  return text.match(re) || [];
}

export function buildTextPayload(body: string): Record<string, unknown> {
  return {
    msgtype: "m.text",
    body,
  };
}
"""

with open(FORMATTING_FILE, "w") as f:
    f.write(unpatched_ts)

# ─── 2. The patch script (skill workspace) ────────────────────────────────────

SKILL_DIR = f"{HOME}/.openclaw/workspace/skills/matrix-mentions-patch"
os.makedirs(SKILL_DIR, exist_ok=True)

PATCH_SCRIPT = f"{SKILL_DIR}/patch-matrix-mentions.mjs"

# This is a real, functional patch script that:
# 1. Finds auth-profiles-*.js in dist/
# 2. Creates a .bak backup
# 3. Injects extractMentionsFromText into the dist file
# 4. Marks formatting.ts with extractMentionsFromText to signal patch applied
patch_script_content = r"""
import { readFileSync, writeFileSync, copyFileSync, readdirSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

const HOME = homedir();
const DIST_DIR = join(HOME, '.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/dist');
const FORMATTING_TS = join(
  HOME,
  '.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/extensions/matrix/src/matrix/send/formatting.ts'
);

// ── Find target file ──────────────────────────────────────────────────────────
const files = readdirSync(DIST_DIR).filter(f => f.startsWith('auth-profiles-') && f.endsWith('.js'));
if (files.length === 0) {
  console.error('[patch] ERROR: No auth-profiles-*.js found in', DIST_DIR);
  process.exit(1);
}
const targetFile = join(DIST_DIR, files[0]);
console.log('[patch] Target file:', targetFile);

// ── Backup ────────────────────────────────────────────────────────────────────
const backupFile = targetFile + '.bak';
copyFileSync(targetFile, backupFile);
console.log('[patch] Backup created:', backupFile);

// ── Patch dist JS ─────────────────────────────────────────────────────────────
let src = readFileSync(targetFile, 'utf8');

if (src.includes('extractMentionsFromText')) {
  console.log('[patch] Already patched. Skipping dist patch.');
} else {
  const mentionsPatch = `
// ── m.mentions patch ──────────────────────────────────────────────────────────
function extractMentionsFromText(text) {
  const re = /@([\\w.-]+):([\\w.-]+)/g;
  const userIds = [];
  let m;
  while ((m = re.exec(text)) !== null) {
    userIds.push('@' + m[1] + ':' + m[2]);
  }
  return userIds.length > 0 ? { 'org.matrix.msc3952.mentions': { user_ids: userIds } } : null;
}
// ── end m.mentions patch ──────────────────────────────────────────────────────
`;
  // Inject after the "use strict" header
  src = src.replace(
    '"use strict";',
    '"use strict";\n' + mentionsPatch
  );
  // Also patch sendMatrixMessage to attach mentions
  src = src.replace(
    '// TODO: attach m.mentions for proper notification routing',
    [
      '// m.mentions patch applied',
      '    const mentionData = extractMentionsFromText(content);',
      '    if (mentionData) { Object.assign(payload.content, mentionData); }',
    ].join('\n')
  );
  writeFileSync(targetFile, src, 'utf8');
  console.log('[patch] Patched dist JS successfully.');
}

// ── Mark formatting.ts as patched ────────────────────────────────────────────
let ts = readFileSync(FORMATTING_TS, 'utf8');
if (ts.includes('extractMentionsFromText')) {
  console.log('[patch] formatting.ts already marked.');
} else {
  ts += `
/**
 * Extracts Matrix user IDs from message text for m.mentions population.
 * Added by matrix-mentions-patch skill.
 */
export function extractMentionsFromText(text: string): Record<string, unknown> | null {
  const re = /@([\\w.-]+):([\\w.-]+)/g;
  const userIds: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    userIds.push('@' + m[1] + ':' + m[2]);
  }
  return userIds.length > 0 ? { 'org.matrix.msc3952.mentions': { user_ids: userIds } } : null;
}
`;
  writeFileSync(FORMATTING_TS, ts, 'utf8');
  console.log('[patch] formatting.ts marked with extractMentionsFromText.');
}

console.log('[patch] Done. Remember to restart the gateway: openclaw gateway restart');
"""

with open(PATCH_SCRIPT, "w") as f:
    f.write(patch_script_content)

os.chmod(PATCH_SCRIPT, 0o755)

# ─── 3. Distractor files — realistic messy environment ────────────────────────

# Other openclaw extensions (distractors)
other_extensions = [
    ("slack", "connector.ts", "export const SLACK_API_VERSION = '2024-01';"),
    ("slack", "formatter.ts", "export function formatSlackBlock(text: string) { return { type: 'section', text: { type: 'mrkdwn', text } }; }"),
    ("teams", "connector.ts", "export const TEAMS_VERSION = '1.3';"),
    ("discord", "connector.ts", "export const DISCORD_SHARDS = 4;"),
    ("matrix", "connector.ts", "import { MatrixClient } from 'matrix-js-sdk';\nexport const MATRIX_HOMESERVER = 'https://matrix.biochao.cc';"),
    ("matrix", "src/matrix/receive/parser.ts", "export function parseEvent(ev: unknown) { return ev; }"),
    ("matrix", "src/matrix/receive/filters.ts", "export const EVENT_FILTER = ['m.room.message', 'm.reaction'];"),
]

for ext_name, rel_path, content in other_extensions:
    dir_path = f"{OPENCLAW_BASE}/extensions/{ext_name}/{os.path.dirname(rel_path)}"
    os.makedirs(dir_path, exist_ok=True)
    with open(f"{OPENCLAW_BASE}/extensions/{ext_name}/{rel_path}", "w") as f:
        f.write(content)

# dist/ distractor files
dist_distractor_files = [
    ("main-bundle.js", '"use strict";\nconst OPENCLAW_CORE_VERSION="4.2.1";\nexports.core={};\n'),
    ("plugin-loader.js", '"use strict";\nfunction loadPlugin(name){return require("./"+name);}\nexports.loadPlugin=loadPlugin;\n'),
    ("matrix-transport.js", '"use strict";\nconst {MatrixClient}=require("matrix-js-sdk");\nexports.transport=MatrixClient;\n'),
    ("config-validator.js", '"use strict";\nfunction validate(cfg){return Object.keys(cfg).length>0;}\nexports.validate=validate;\n'),
    ("gateway-core.js", '"use strict";\nconst GATEWAY_PORT=9988;\nexports.start=function(){console.log("gateway on",GATEWAY_PORT);};\n'),
]

for fname, content in dist_distractor_files:
    with open(f"{DIST_DIR}/{fname}", "w") as f:
        f.write(content)

# openclaw workspace distractor skills
other_skills = ["slack-integration", "teams-connector", "notification-router", "log-aggregator"]
for skill_name in other_skills:
    skill_path = f"{HOME}/.openclaw/workspace/skills/{skill_name}"
    os.makedirs(skill_path, exist_ok=True)
    with open(f"{skill_path}/README.md", "w") as f:
        f.write(f"# {skill_name}\nThis skill handles {skill_name} integration.\n")
    with open(f"{skill_path}/index.mjs", "w") as f:
        f.write(f'console.log("{skill_name} loaded");\n')

# openclaw config directory
CONFIG_DIR = f"{HOME}/.openclaw/config"
os.makedirs(CONFIG_DIR, exist_ok=True)
with open(f"{CONFIG_DIR}/gateway.json", "w") as f:
    f.write('{"port": 9988, "logLevel": "info", "plugins": ["matrix", "slack", "teams", "discord"]}\n')
with open(f"{CONFIG_DIR}/matrix.json", "w") as f:
    f.write('{"homeserver": "https://matrix.biochao.cc", "userId": "@bot:matrix.biochao.cc", "deviceId": "OCLAW_BOT"}\n')
with open(f"{CONFIG_DIR}/profiles.json", "w") as f:
    f.write('{"default": {"displayName": "OpenClaw Bot", "avatar": null}}\n')

# openclaw logs (distractor)
LOGS_DIR = f"{HOME}/.openclaw/logs"
os.makedirs(LOGS_DIR, exist_ok=True)
for i in range(3):
    with open(f"{LOGS_DIR}/gateway-2024-01-{i+1:02d}.log", "w") as f:
        f.write(f"[2024-01-{i+1:02d}T00:00:00Z] gateway started\n[2024-01-{i+1:02d}T00:01:00Z] matrix plugin loaded\n")

# NVM distractor structure
NVM_DIR = f"{HOME}/.nvm"
with open(f"{NVM_DIR}/.nvmrc", "w") as f:
    f.write("v22.22.0\n")
with open(f"{NVM_DIR}/alias", "w") as f:
    f.write("default -> v22.22.0\n")

print("Workspace generation complete.")
print(f"  Target dist file: {AUTH_PROFILES_FILE}")
print(f"  Formatting TS:    {FORMATTING_FILE}")
print(f"  Patch script:     {PATCH_SCRIPT}")