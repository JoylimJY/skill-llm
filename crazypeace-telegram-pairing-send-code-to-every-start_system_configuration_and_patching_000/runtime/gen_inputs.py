import os
import random

random.seed(42)

# ---------------------------------------------------------------------------
# Build the realistic OpenClaw module tree under /usr/lib/node_modules/openclaw
# ---------------------------------------------------------------------------

base = "/usr/lib/node_modules/openclaw"

# ── Distractor files ────────────────────────────────────────────────────────
distractors = {
    "package.json": """\
{
  "name": "openclaw",
  "version": "3.7.2",
  "description": "OpenClaw IoT Gateway",
  "main": "lib/index.js",
  "license": "MIT"
}
""",
    "README.md": """\
# OpenClaw Gateway
OpenClaw is a modular IoT device pairing gateway.
See docs/ for full documentation.
""",
    "lib/index.js": """\
'use strict';
const gateway = require('./gateway');
const pairing = require('./pairing/manager');
module.exports = { gateway, pairing };
""",
    "lib/gateway.js": """\
'use strict';
// Gateway lifecycle management
async function start() { console.log('Gateway started'); }
async function stop()  { console.log('Gateway stopped'); }
async function restart() { await stop(); await start(); }
module.exports = { start, stop, restart };
""",
    "lib/config.js": """\
'use strict';
const DEFAULT_PORT = 8443;
const DEFAULT_TIMEOUT = 30000;
module.exports = { DEFAULT_PORT, DEFAULT_TIMEOUT };
""",
    "lib/logger.js": """\
'use strict';
function info(msg)  { process.stdout.write('[INFO]  ' + msg + '\\n'); }
function warn(msg)  { process.stdout.write('[WARN]  ' + msg + '\\n'); }
function error(msg) { process.stdout.write('[ERROR] ' + msg + '\\n'); }
module.exports = { info, warn, error };
""",
    "lib/pairing/manager.js": """\
'use strict';
// High-level pairing manager — delegates to channel handlers
const telegram = require('./channels/telegram');
const discord  = require('./channels/discord');
module.exports = { telegram, discord };
""",
    "lib/pairing/channels/discord.js": """\
'use strict';
// Discord pairing channel (not relevant to this task)
async function handleStart(ctx) {
  const { code, created } = await ctx.upsertPairingRequest({ id: ctx.senderId, meta: ctx.meta });
  if (!created) return { created: false };
  await ctx.sendPairingReply('Your Discord pairing code: ' + code);
  return { created: true, code };
}
module.exports = { handleStart };
""",
    "lib/pairing/store.js": """\
'use strict';
const store = new Map();
async function upsertPairingRequest({ id, meta }) {
  if (store.has(id)) {
    return { code: store.get(id).code, created: false };
  }
  const code = Math.random().toString(36).slice(2, 8).toUpperCase();
  store.set(id, { code, meta, createdAt: Date.now() });
  return { code, created: true };
}
module.exports = { upsertPairingRequest };
""",
    "lib/pairing/reply.js": """\
'use strict';
function buildPairingReply({ channel, idLine, code }) {
  return `[${channel}] Pairing code for ${idLine}: ${code}`;
}
module.exports = { buildPairingReply };
""",
    "lib/utils/crypto.js": """\
'use strict';
const crypto = require('crypto');
function generateToken(len = 32) {
  return crypto.randomBytes(len).toString('hex');
}
module.exports = { generateToken };
""",
    "lib/utils/retry.js": """\
'use strict';
async function withRetry(fn, times = 3) {
  for (let i = 0; i < times; i++) {
    try { return await fn(); } catch (e) { if (i === times - 1) throw e; }
  }
}
module.exports = { withRetry };
""",
    "lib/transport/http.js": """\
'use strict';
const http = require('http');
function createServer(handler) { return http.createServer(handler); }
module.exports = { createServer };
""",
    "lib/transport/ws.js": """\
'use strict';
// WebSocket transport placeholder
module.exports = {};
""",
    "docs/api.md": """\
# OpenClaw API Reference
Refer to lib/index.js for exported symbols.
""",
    "docs/pairing-flow.md": """\
# Pairing Flow
1. User sends /start via a messaging channel.
2. Gateway issues a pairing challenge.
3. Admin approves the pairing request.
""",
    "tests/gateway.test.js": """\
'use strict';
const { gateway } = require('../lib/index');
test('gateway starts', async () => { await expect(gateway.start()).resolves.toBeUndefined(); });
""",
    "tests/pairing.test.js": """\
'use strict';
// Placeholder tests for pairing logic
test('todo', () => { expect(true).toBe(true); });
""",
}

# ── The TARGET file containing issuePairingChallenge ────────────────────────
# Placed deep enough to require a search, but findable via grep
target_file = "lib/pairing/channels/telegram.js"

target_content = """\
'use strict';
const { buildPairingReply } = require('../reply');

/**
 * Telegram channel pairing handler.
 * Handles /start messages from unapproved users.
 */

async function issuePairingChallenge(params) {
  const { code, created } = await params.upsertPairingRequest({
    id: params.senderId,
    meta: params.meta
  });
  if (!created) return { created: false };
  params.onCreated?.({ code });
  const replyText = params.buildReplyText?.({
    code,
    senderIdLine: params.senderIdLine
  }) ?? buildPairingReply({
    channel: params.channel,
    idLine: params.senderIdLine,
    code
  });
  try {
    await params.sendPairingReply(replyText);
  } catch (err) {
    params.onReplyError?.(err);
  }
  return {
    created: true,
    code
  };
}

async function handleStart(ctx) {
  return issuePairingChallenge({
    senderId:        ctx.senderId,
    meta:            ctx.meta,
    channel:         'telegram',
    senderIdLine:    ctx.senderIdLine,
    upsertPairingRequest: ctx.upsertPairingRequest,
    sendPairingReply:     ctx.sendPairingReply,
  });
}

module.exports = { issuePairingChallenge, handleStart };
"""

distractors[target_file] = target_content

# ── Write all files ──────────────────────────────────────────────────────────
for rel_path, content in distractors.items():
    full_path = os.path.join(base, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print(f"[gen_inputs] Created {len(distractors)} files under {base}")
print(f"[gen_inputs] Target file: {os.path.join(base, target_file)}")

# ---------------------------------------------------------------------------
# Workspace dir for the agent (empty — agent must operate on /usr/lib/...)
# ---------------------------------------------------------------------------
os.makedirs("/workspace", exist_ok=True)
print("[gen_inputs] Workspace ready at /workspace")