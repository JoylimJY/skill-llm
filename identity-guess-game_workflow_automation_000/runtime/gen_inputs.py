import os
import json
import random
import textwrap

random.seed(42)

workspace = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts/data/games",
    "scripts/data/rankings",
    "messages",
    "logs",
    "config",
    "docs/rules",
    "docs/archive",
    "assets/icons",
    "assets/sounds",
    "tmp",
    "backup/2024",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "config/server.json": json.dumps({"host": "localhost", "port": 3000, "debug": False}, indent=2),
    "config/identities_pool.json": json.dumps(["魔术师", "气象学家", "考古学家", "调酒师", "宇航员",
                                                "驯兽师", "外交官", "密码学家", "潜水员", "园艺师"], indent=2),
    "docs/rules/scoring.md": "## 旧版计分规则\n猜对 +8 分，伪装 +3 分（已废弃）",
    "docs/rules/faq.md": "## FAQ\nQ: 可以在群里说自己的身份吗？\nA: 不可以！",
    "docs/archive/game_20240101.json": json.dumps({"groupId": "old-group-1", "status": "settled", "players": []}),
    "docs/archive/game_20240215.json": json.dumps({"groupId": "old-group-2", "status": "settled", "players": []}),
    "assets/icons/trophy.txt": "🏆",
    "assets/sounds/fanfare.txt": "🎺🎺🎺",
    "logs/server.log": "2024-01-01 00:00:00 INFO Server started\n2024-01-01 00:01:00 INFO Game created\n",
    "tmp/scratch.txt": "temporary notes — delete me",
    "backup/2024/snapshot.json": json.dumps({"backup_date": "2024-12-31", "games": 42}),
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# ── package.json for the scripts module ─────────────────────────────────────
pkg = {"name": "identity-guess-game", "version": "1.0.0", "type": "module"}
with open(os.path.join(workspace, "scripts/package.json"), "w") as f:
    json.dump(pkg, f, indent=2)

# ── game-engine.mjs ──────────────────────────────────────────────────────────
# A fully self-contained game engine implementing all commands from SKILL.md
engine_code = r"""
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const GAMES_DIR = resolve(__dirname, 'data/games');
const RANKINGS_DIR = resolve(__dirname, 'data/rankings');

const IDENTITIES = [
  "魔术师", "气象学家", "考古学家", "调酒师", "宇航员",
  "驯兽师", "外交官", "密码学家", "潜水员", "园艺师",
  "建筑师", "神经外科医生", "昆虫学家", "火焰喷射器操作员", "马戏团团长"
];

function parseArgs(args) {
  const result = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      result[key] = args[i + 1] || true;
      i++;
    }
  }
  return result;
}

function gameFile(groupId) {
  return resolve(GAMES_DIR, `${groupId}.json`);
}

function rankingFile(groupId) {
  return resolve(RANKINGS_DIR, `${groupId}.json`);
}

function loadGame(groupId) {
  const f = gameFile(groupId);
  if (!existsSync(f)) {
    console.error(JSON.stringify({ error: `Game not found for group: ${groupId}` }));
    process.exit(1);
  }
  return JSON.parse(readFileSync(f, 'utf8'));
}

function saveGame(groupId, game) {
  writeFileSync(gameFile(groupId), JSON.stringify(game, null, 2));
}

function shuffle(arr) {
  // Seeded-ish shuffle using splice
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

const [,, command, ...rest] = process.argv;
const args = parseArgs(rest);

if (command === 'help') {
  console.log(JSON.stringify({
    commands: ['create', 'get_identity', 'status', 'clue', 'guess', 'settle', 'ranking', 'help']
  }));

} else if (command === 'create') {
  const groupId = args['group'];
  const players = JSON.parse(args['players']);
  if (!groupId || !players || players.length < 2) {
    console.error(JSON.stringify({ error: 'Requires --group and --players (min 2)' }));
    process.exit(1);
  }
  const identities = shuffle(IDENTITIES).slice(0, players.length);
  const gamePlayers = players.map((p, i) => ({
    id: p.id,
    name: p.name,
    identity: identities[i],
    clues: [],
    guesses: {},
    score: { correct: 0, camouflage: 0, total: 0 }
  }));
  const game = {
    groupId,
    status: 'clue',
    currentRound: 1,
    totalRounds: 3,
    players: gamePlayers,
    createdAt: new Date().toISOString()
  };
  saveGame(groupId, game);
  // Return players WITHOUT identity
  const safeResult = {
    groupId,
    status: 'created',
    players: gamePlayers.map(p => ({ id: p.id, name: p.name }))
  };
  console.log(JSON.stringify(safeResult));

} else if (command === 'get_identity') {
  const groupId = args['group'];
  const playerId = args['player'];
  const game = loadGame(groupId);
  const player = game.players.find(p => p.id === playerId);
  if (!player) {
    console.error(JSON.stringify({ error: `Player not found: ${playerId}` }));
    process.exit(1);
  }
  console.log(JSON.stringify({ playerId: player.id, name: player.name, identity: player.identity }));

} else if (command === 'status') {
  const groupId = args['group'];
  const game = loadGame(groupId);
  const safeGame = {
    ...game,
    players: game.players.map(p => ({
      id: p.id,
      name: p.name,
      cluesSubmitted: p.clues.length,
      guessesSubmitted: Object.keys(p.guesses).length
    }))
  };
  console.log(JSON.stringify(safeGame));

} else if (command === 'clue') {
  const groupId = args['group'];
  const playerId = args['player'];
  const text = args['text'];
  const game = loadGame(groupId);
  if (game.status !== 'clue') {
    console.error(JSON.stringify({ error: 'Not in clue phase' }));
    process.exit(1);
  }
  const player = game.players.find(p => p.id === playerId);
  if (!player) {
    console.error(JSON.stringify({ error: `Player not found: ${playerId}` }));
    process.exit(1);
  }
  // Check if player already submitted for this round
  if (player.clues.length >= game.currentRound) {
    console.error(JSON.stringify({ error: 'Already submitted clue for this round' }));
    process.exit(1);
  }
  // Cheat detection: check if clue contains identity name
  if (text.includes(player.identity)) {
    console.error(JSON.stringify({ error: `Cheat detected: clue contains identity name "${player.identity}"` }));
    process.exit(1);
  }
  player.clues.push({ round: game.currentRound, text });
  // Check if all players submitted for this round
  const roundComplete = game.players.every(p => p.clues.length >= game.currentRound);
  let allRoundsComplete = false;
  if (roundComplete) {
    if (game.currentRound < game.totalRounds) {
      game.currentRound++;
    } else {
      game.status = 'guess';
      allRoundsComplete = true;
    }
  }
  saveGame(groupId, game);
  console.log(JSON.stringify({ success: true, playerId, round: player.clues.length, roundComplete, allRoundsComplete }));

} else if (command === 'guess') {
  const groupId = args['group'];
  const playerId = args['player'];
  const guesses = JSON.parse(args['guesses']); // { targetName: guessedIdentity }
  const game = loadGame(groupId);
  if (game.status !== 'guess') {
    console.error(JSON.stringify({ error: 'Not in guess phase' }));
    process.exit(1);
  }
  const player = game.players.find(p => p.id === playerId);
  if (!player) {
    console.error(JSON.stringify({ error: `Player not found: ${playerId}` }));
    process.exit(1);
  }
  player.guesses = guesses;
  saveGame(groupId, game);
  const allGuessed = game.players.every(p => Object.keys(p.guesses).length > 0);
  console.log(JSON.stringify({ success: true, playerId, allGuessed }));

} else if (command === 'settle') {
  const groupId = args['group'];
  const game = loadGame(groupId);
  if (game.status !== 'guess') {
    console.error(JSON.stringify({ error: 'Not ready to settle' }));
    process.exit(1);
  }
  const allGuessed = game.players.every(p => Object.keys(p.guesses).length > 0);
  if (!allGuessed) {
    console.error(JSON.stringify({ error: 'Not all players have submitted guesses' }));
    process.exit(1);
  }
  // Calculate scores
  for (const player of game.players) {
    let correct = 0;
    // Count how many correct guesses this player made
    for (const [targetName, guessedIdentity] of Object.entries(player.guesses)) {
      const target = game.players.find(p => p.name === targetName);
      if (target && target.identity === guessedIdentity) {
        correct++;
      }
    }
    player.score.correct = correct * 10;
  }
  // Camouflage: for each player, count how many others guessed them WRONG
  for (const player of game.players) {
    let wrongGuesses = 0;
    for (const other of game.players) {
      if (other.id === player.id) continue;
      if (Object.keys(other.guesses).length === 0) continue;
      const guess = other.guesses[player.name];
      if (guess !== undefined && guess !== player.identity) {
        wrongGuesses++;
      }
    }
    player.score.camouflage = wrongGuesses * 5;
    player.score.total = player.score.correct + player.score.camouflage;
  }
  game.status = 'settled';
  saveGame(groupId, game);

  // Update rankings
  const rf = rankingFile(groupId);
  let rankings = existsSync(rf) ? JSON.parse(readFileSync(rf, 'utf8')) : { groupId, players: {} };
  for (const p of game.players) {
    if (!rankings.players[p.id]) {
      rankings.players[p.id] = { id: p.id, name: p.name, totalScore: 0, gamesPlayed: 0 };
    }
    rankings.players[p.id].totalScore += p.score.total;
    rankings.players[p.id].gamesPlayed++;
  }
  writeFileSync(rf, JSON.stringify(rankings, null, 2));

  const result = {
    groupId,
    status: 'settled',
    identities: game.players.map(p => ({ id: p.id, name: p.name, identity: p.identity })),
    scores: game.players
      .sort((a, b) => b.score.total - a.score.total)
      .map(p => ({
        id: p.id,
        name: p.name,
        correctScore: p.score.correct,
        camouflageScore: p.score.camouflage,
        total: p.score.total
      }))
  };
  console.log(JSON.stringify(result));

} else if (command === 'ranking') {
  const groupId = args['group'];
  const rf = rankingFile(groupId);
  if (!existsSync(rf)) {
    console.log(JSON.stringify({ groupId, rankings: [] }));
  } else {
    const data = JSON.parse(readFileSync(rf, 'utf8'));
    const sorted = Object.values(data.players).sort((a, b) => b.totalScore - a.totalScore);
    console.log(JSON.stringify({ groupId, rankings: sorted }));
  }

} else {
  console.error(JSON.stringify({ error: `Unknown command: ${command}` }));
  process.exit(1);
}
"""
with open(os.path.join(workspace, "scripts/game-engine.mjs"), "w") as f:
    f.write(engine_code)

# ── scenario.json — the game spec the agent must execute ────────────────────
# Fixed players, fixed clues per round, fixed guesses
scenario = {
    "groupId": "team-alpha-2025",
    "players": [
        {"id": "u001", "name": "Alice"},
        {"id": "u002", "name": "Bob"},
        {"id": "u003", "name": "Carol"},
    ],
    "clues": {
        "u001": ["我每天都要研究云层的变化", "我的工作离不开气压计和温度表", "我能提前告诉你明天要不要带伞"],
        "u002": ["我用双手创造美丽的空间", "我的作品会矗立几百年", "我和结构工程师是最好的搭档"],
        "u003": ["我的实验室里住着很多六条腿的小家伙", "我对蜂巢的构造着迷", "我的研究可能帮助研发新型抗菌药物"]
    },
    "guesses": {
        "u001": {"Bob": "建筑师", "Carol": "昆虫学家"},
        "u002": {"Alice": "气象学家", "Carol": "昆虫学家"},
        "u003": {"Alice": "气象学家", "Bob": "外交官"}
    }
}
with open(os.path.join(workspace, "scenario.json"), "w") as f:
    json.dump(scenario, f, indent=2, ensure_ascii=False)

# ── mock send_dm.sh ──────────────────────────────────────────────────────────
send_dm_script = r"""#!/usr/bin/env bash
# Mock private message sender
# Usage: send_dm.sh --to <userId> --message "<text>"
TO=""
MESSAGE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --to) TO="$2"; shift 2 ;;
    --message) MESSAGE="$2"; shift 2 ;;
    *) shift ;;
  esac
done
if [[ -z "$TO" || -z "$MESSAGE" ]]; then
  echo '{"error": "Missing --to or --message"}' >&2
  exit 1
fi
mkdir -p /workspace/messages
echo "$MESSAGE" > "/workspace/messages/${TO}.txt"
echo "{\"success\": true, \"to\": \"$TO\"}"
"""
with open(os.path.join(workspace, "send_dm.sh"), "w") as f:
    f.write(send_dm_script)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")