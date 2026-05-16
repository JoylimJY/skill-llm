---
name: matrix-mentions-patch
description: Use when a user reports Matrix @mentions not working, notifications not triggering, asks to fix/update the mentions patch, or asks to install/apply the patch. This skill should only be used when explicitly requested.
---

# Matrix Mentions Patch

Patches OpenClaw's Matrix plugin to attach `m.mentions` to outbound messages so clients like Element properly notify mentioned users.

## When to Use

- User reports @mentions not triggering notifications
- User asks to "fix Matrix mentions" or "update the mentions patch"
- User asks to "install" or "apply" the mentions patch

**Only apply when requested.** Do not auto-apply.

## Patch Status Check

Before applying, check if already patched:

```bash
grep -l "extractMentionsFromText" ~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/extensions/matrix/src/matrix/send/formatting.ts
```

- **Already patched**: Output will show the file. No action needed — just use correct @mention format.
- **Not patched**: No output. Proceed to apply the patch.

## How to Apply (First-time Setup)

### Step 1: Run the patch script

```bash
node ~/.openclaw/workspace/skills/matrix-mentions-patch/patch-matrix-mentions.mjs
```

The script will:
1. Locate `auth-profiles-*.js` in OpenClaw's dist/
2. Create a `.bak` backup automatically
3. Patch in-place

### Step 2: Restart the gateway

```bash
openclaw gateway restart
```

### Step 3: Verify

Send a message with a full Matrix ID mention:
```
@username:matrix.biochao.cc
```
The mentioned user should see a notification.

## Routine Use (After Patched)

Once patched, no further action needed. Just ensure correct @mention format:

**正确格式：**
```
@username:matrix.biochao.cc
```

**错误格式：**
- Markdown link: `[](https://matrix.to/#/@user)`
- HTML span: `<span>@user</span>`
- 任何包装格式

直接发送纯文本 Matrix ID，客户端即可正确识别并通知。

## Re-applying After Updates

Every `openclaw update` may overwrite the patch. Re-apply by running:

```bash
node ~/.openclaw/workspace/skills/matrix-mentions-patch/patch-matrix-mentions.mjs
openclaw gateway restart
```

## Undoing the Patch

Restore from backup:
```bash
cp ~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/dist/auth-profiles-*.js.bak \
 ~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/dist/auth-profiles-*.js
openclaw gateway restart
```

## Target File

```
~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/dist/auth-profiles-*.js
```

## Requirements

- OpenClaw core
- Matrix plugin configured and working
- Node.js runtime