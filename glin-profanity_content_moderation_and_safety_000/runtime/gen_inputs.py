import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "platform/auth",
    "platform/chat",
    "platform/leaderboard",
    "platform/rewards",
    "platform/analytics",
    "platform/chat/archive",
    "platform/chat/reports",
    "platform/chat/config",
    "infra/docker",
    "infra/nginx",
    "scripts/migrate",
    "scripts/seed",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "platform/auth/session.js": "// session management placeholder\nmodule.exports = {};",
    "platform/leaderboard/rankings.json": json.dumps({"top": ["player1","player2","player3"]}),
    "platform/rewards/config.yaml": "rewards:\n  daily: 10\n  weekly: 50\n",
    "platform/analytics/events.log": "\n".join([f"event_{i}: player_action" for i in range(20)]),
    "platform/chat/config/rate_limits.json": json.dumps({"max_per_minute": 30}),
    "platform/chat/archive/2024-01.jsonl": "\n".join([
        json.dumps({"id": i, "user": f"player{i}", "text": "gg wp"}) for i in range(5)
    ]),
    "infra/docker/compose.yml": "version: '3'\nservices:\n  app:\n    image: node:20\n",
    "infra/nginx/nginx.conf": "server {\n  listen 80;\n  server_name localhost;\n}\n",
    "scripts/migrate/v1_to_v2.js": "// migration stub\nconsole.log('migrating...');",
    "scripts/seed/seed_users.js": "// seed script\nconst users = [];\nmodule.exports = users;",
    "tests/unit/auth.test.js": "test('auth', () => { expect(true).toBe(true); });",
    "tests/integration/chat.test.js": "test('chat pipeline', () => { expect(true).toBe(true); });",
    "platform/chat/config/banned_words_legacy.txt": "badword1\nbadword2\nobsolete_term\n",
    "platform/chat/reports/.gitkeep": "",
}
for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── The main input: raw player comments JSONL ────────────────────────────────
# Deliberately messy: mix of clean, leetspeak-obfuscated, Unicode-trick, and
# borderline-but-clean comments. The agent must correctly identify flagged ones.
comments = [
    # clearly clean
    {"id": 1,  "player": "shadow_blade",   "text": "Great match everyone, gg!"},
    {"id": 2,  "player": "nova_striker",   "text": "Can we play another round?"},
    {"id": 3,  "player": "pixel_ninja",    "text": "That last level was really tough."},
    {"id": 4,  "player": "echo_runner",    "text": "Nice strategy on the left flank."},
    {"id": 5,  "player": "drift_king99",   "text": "I need to work on my aim."},
    # leetspeak evasion — should be caught with aggressive level
    {"id": 6,  "player": "xX_rage_Xx",    "text": "You are such a b1tch lmao"},
    {"id": 7,  "player": "anon_troll77",  "text": "sh1t player go back to noob games"},
    {"id": 8,  "player": "l33t_hax0r",    "text": "what the f4ck was that move"},
    {"id": 9,  "player": "dark_fury",     "text": "total @$$hole camping again"},
    # Unicode homoglyph evasion — Cyrillic/lookalike chars
    {"id": 10, "player": "unicode_eve",   "text": "fᴜck this lag so bad"},
    {"id": 11, "player": "cyrилlic_usr",  "text": "аss ping every single game"},
    # custom domain slur the platform wants to catch
    {"id": 12, "player": "griefer_X",     "text": "you are a total noobkiller trash"},
    # borderline / clean context — should NOT be flagged
    {"id": 13, "player": "lore_master",   "text": "The hell biome is the hardest zone."},
    {"id": 14, "player": "medic_main",    "text": "My shot accuracy is at 55 percent."},
    {"id": 15, "player": "beta_tester",   "text": "The patch broke the bass guitar sounds."},
    # more aggressive evasion
    {"id": 16, "player": "troll_4eva",    "text": "k1ll yourself already omg"},
    {"id": 17, "player": "salty_pete",    "text": "a$$hole admin always bans me"},
    {"id": 18, "player": "flamer_z",      "text": "this game is sh!t and devs are d!cks"},
    # clean
    {"id": 19, "player": "calm_player",   "text": "Good game, looking forward to the tournament."},
    {"id": 20, "player": "zen_gamer",     "text": "I will practice more this weekend."},
]

jsonl_path = os.path.join(workspace, "platform/chat/incoming_comments.jsonl")
with open(jsonl_path, "w") as f:
    for c in comments:
        f.write(json.dumps(c) + "\n")

print(f"Generated {len(comments)} comments in {jsonl_path}")
print("Workspace structure ready.")