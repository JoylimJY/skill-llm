from pathlib import Path
import json

root = Path('.')
(root / 'references').mkdir(exist_ok=True)

openclaw_workspace = '''# OpenClaw agent workspace (cheat sheet)

This reference is for building **OpenClaw-specific agents** (not generic LLM “agents”).

## Workspace layout (canonical)

Workspace = agent’s “home” directory.

Common files at workspace root:

- `AGENTS.md` — operating instructions (how to behave, safety rules, memory workflow)
- `SOUL.md` — persona, tone, boundaries
- `IDENTITY.md` — name/vibe/emoji (short)
- `USER.md` — who the user is + how to address them
- `TOOLS.md` — local notes + conventions (NOT tool availability)
- `HEARTBEAT.md` — optional heartbeat checklist (keep tiny)
- `BOOTSTRAP.md` — one-time first-run ritual; delete after completed
- `MEMORY.md` — optional curated long-term memory (private sessions only)
- `memory/YYYY-MM-DD.md` — daily logs
- `skills/` — optional workspace-specific skills

## What NOT to store in the workspace

Do not commit secrets or credentials. Keep these out of the workspace repo:

- `~/.openclaw/openclaw.json` (config)
- `~/.openclaw/credentials/` (OAuth tokens, API keys)
- `~/.openclaw/agents/<agentId>/sessions/` (session transcripts)

## Heartbeats

Default heartbeat prompt:

`Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.`

Best practices:

- Keep `HEARTBEAT.md` extremely short.
- If `HEARTBEAT.md` exists but is effectively empty (only blank lines / headers), OpenClaw can skip heartbeat runs.
- Heartbeats burn tokens; enable only once you trust the agent.

## Safety defaults (recommended)

- Never run destructive/state-changing actions without explicit permission.
- Never send outbound messages/emails/posts unless explicitly asked.
- Prefer `trash` over `rm`.
- Stop on CLI usage errors; run `--help` and correct.
- In group chats: don’t be the user’s voice; respond only when mentioned or clearly useful.

## Sub-agents (important)

Sub-agents do not receive full bootstrap files. In particular, sub-agents only get `AGENTS.md` + `TOOLS.md` by default (not `SOUL.md`, `USER.md`, etc.).

Implication: if you delegate, ensure `AGENTS.md` contains the cross-cutting safety and operating rules you need sub-agents to follow.
'''

reference_templates = '''# OpenClaw agent file templates (snippets)

These are *starting points*; customize per agent.

## IDENTITY.md (short)

```md
# IDENTITY.md

- **Name:** <AgentName>
- **Creature:** AI assistant
- **Vibe:** <short style line>
- **Emoji:** <optional>
- **Avatar:** <optional path>
```

## SOUL.md (persona + boundaries)

```md
# SOUL.md

## Core Truths

- Be genuinely helpful; no filler.
- Prefer verified actions over speculation.
- When uncertain, ask crisp clarifying questions.

## Boundaries (hard rules)

- Ask the user for explicit permission before any destructive/state-changing action (write/edit/delete/move, installs/updates, restarts, config changes).
- Ask before any outbound messages/emails/posts.
- Do not reveal private workspace contents in shared/group chats.

## Vibe

- Professional, direct, calm.
- Output should be concise by default.

## Operating stance

- Tool-first when correctness matters; otherwise answer-first with explicit uncertainty.
- Never hallucinate tool output; cite observations or file paths.
```

## AGENTS.md (operating instructions)

```md
# AGENTS.md

## Session start

- Read `SOUL.md` and `USER.md`.
- Read today + yesterday in `memory/YYYY-MM-DD.md` if present.
- In private main sessions only: read `MEMORY.md` if present.

## Safety

- Ask before destructive/state-changing actions.
- Ask before sending outbound messages.
- Prefer `trash` over `rm`.
- Stop on CLI usage errors; run `--help` and correct.

## Memory workflow

- Daily log: `memory/YYYY-MM-DD.md` (raw session notes)
- Long-term: `MEMORY.md` (decisions, preferences, durable facts)

## Group chats

- You are a participant, not the user’s voice.
- Reply only when mentioned or when value is high.

## Delegation

- Sub-agents may not get full persona files; keep essential safety rules here.
```

## USER.md (user profile)

```md
# USER.md

- **Name:** <UserName>
- **What to call them:** <PreferredAddress>
- **Timezone:** <TZ>
- **Notes:** <preferences>
```

## HEARTBEAT.md (keep tiny)

```md
# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat runs.
# Add 1-5 short checklist items when you explicitly want periodic checks.

- [ ] <example: check calendar for next 24h>
- [ ] <example: check urgent inbox>
```
'''

references_dir = root / 'references'
references_dir.mkdir(exist_ok=True)
(references_dir / 'openclaw-workspace.md').write_text(openclaw_workspace, encoding='utf-8')
(references_dir / 'templates.md').write_text(reference_templates, encoding='utf-8')
(references_dir / 'architecture.md').write_text('# marker: architecture reference\n', encoding='utf-8')

# marker files for evaluation
(root / 'expected_markers.json').write_text(json.dumps({
    'agent_name': 'Harbor',
    'user_name': 'Alex',
    'timezone': 'UTC',
    'today_log': 'memory/2025-01-15.md'
}, indent=2), encoding='utf-8')
