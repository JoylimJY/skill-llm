import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic indie game project directory structure
dirs = [
    "src",
    "src/systems",
    "src/rendering",
    "src/ui",
    "assets",
    "assets/sprites",
    "assets/audio",
    "docs",
    "build",
    "tests",
    "config",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "src/systems/physics.js": """// Physics system placeholder
const GRAVITY = 9.8;
function applyGravity(entity) {
    entity.vy += GRAVITY * 0.016;
}
module.exports = { applyGravity };
""",
    "src/systems/audio.js": """// Audio system
const sounds = {};
function playSound(name) {
    if (sounds[name]) sounds[name].play();
}
module.exports = { playSound };
""",
    "src/rendering/canvas.js": """// Canvas setup
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
module.exports = { canvas, ctx };
""",
    "src/ui/hud.js": """// HUD overlay
function renderHUD(state) {
    document.getElementById('score').textContent = state.score;
    document.getElementById('lives').textContent = state.lives;
}
module.exports = { renderHUD };
""",
    "src/ui/menu.js": """// Main menu
function showMenu() {
    document.getElementById('main-menu').style.display = 'block';
}
function hideMenu() {
    document.getElementById('main-menu').style.display = 'none';
}
module.exports = { showMenu, hideMenu };
""",
    "config/game.config.json": """{
  "version": "0.4.2",
  "title": "Essence Crawler",
  "targetFPS": 60,
  "canvasWidth": 800,
  "canvasHeight": 600,
  "debug": false
}
""",
    "docs/architecture.md": """# Architecture Notes

## Layer System
- Background layer
- Entity layer
- Effect layer
- UI layer

## Game Loop
requestAnimationFrame drives all updates at 60fps.
""",
    "docs/creature_types.md": """# Creature Types

## Lobster
- Head: claws, antennae
- Body: segmented carapace

## Beetle
- Head: mandibles
- Body: elytra shell
""",
    "assets/sprites/placeholder.txt": "Sprite assets go here.",
    "assets/audio/placeholder.txt": "Audio assets go here.",
    "tests/test_utils.js": """// Basic utility tests
function assert(condition, msg) {
    if (!condition) throw new Error('FAIL: ' + msg);
}
// Test pick()
// assert(typeof pick([1,2,3]) !== 'undefined', 'pick returns value');
console.log('Tests skipped - awaiting refactor');
""",
    "build/README.txt": "Build output directory. Run `npm run build` to populate.",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# THE MAIN PROBLEM FILE: a messy prototype JS game file
# It has:
# 1. Ghost/dead variables (declared but never used)
# 2. A repeated pattern 4 times (finding a creature type by id in CREATURE_TYPES array inline with .find())
# 3. Data/logic interleaved (dialogue lines mixed into logic functions)
# 4. Hot-path .find() inside the gameLoop/update function (called every frame)
# 5. Old state field name: creature.stamina (needs migration to creature.energy)
# 6. An old summonCreature function that should be replaced but NOT deleted yet

messy_game_js = """\
// game.js — Essence Crawler prototype v0.4 (built by feeling, needs cleanup)

// ---- scattered config and state (mixed together) ----
const VERSION = '0.4.2';
const MAX_CREATURES = 10;
const TICK_RATE = 60;

// ghost: was used in v0.2 color system, no longer referenced
const LEGACY_COLORS = { fire: '#ff4400', ice: '#00aaff', earth: '#886633' };

// ghost: leftover from abandoned combo system
let comboMultiplier = 1;
let comboTimer = 0;

// Creature type definitions (data living next to logic — messy)
const CREATURE_TYPES = [
    { id: 'lobster', name: 'Lobster', baseDamage: 5, baseDefense: 3 },
    { id: 'beetle',  name: 'Beetle',  baseDamage: 3, baseDefense: 7 },
    { id: 'wisp',    name: 'Wisp',    baseDamage: 8, baseDefense: 1 },
    { id: 'golem',   name: 'Golem',   baseDamage: 2, baseDefense: 12 },
];

// Game state — note: field is "stamina" (old name, being renamed to "energy")
const State = {
    essence: { fire: 0, ice: 0, earth: 0 },
    creatures: [],
    tick: 0,
    score: 0,
};

// ghost: was going to be a leaderboard, never shipped
const leaderboardCache = [];

// ---- utility ----
function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

// ---- some dialogue data shoved right next to function logic (data/logic blur) ----
function summonCreature(typeId) {
    // dialogue lines for summon — should be data, not here
    const SUMMON_LINES = [
        'A presence stirs in the deep...',
        'Something ancient answers your call.',
        'The void shivers. It comes.',
    ];
    const line = pick(SUMMON_LINES);
    console.log(line);

    // inline find — pattern instance #1
    const ctype = CREATURE_TYPES.find(t => t.id === typeId);
    if (!ctype) return null;

    const creature = {
        id: 'c_' + Date.now(),
        typeId: typeId,
        name: ctype.name,
        hp: 100,
        stamina: 50,          // OLD field name — needs migration to "energy"
        damage: ctype.baseDamage,
        defense: ctype.baseDefense,
    };
    State.creatures.push(creature);
    return creature;
}

// ghost: partial upgrade system, never connected to UI
function applyUpgrade(creatureId, upgradeId) {
    const UPGRADE_TABLE = { power: 2, shield: 3, swift: 1 };
    // ... was going to apply upgrades but this was abandoned
    // const upg = UPGRADE_TABLE[upgradeId];
}

function getCreaturePower(typeId) {
    // inline find — pattern instance #2
    const ctype = CREATURE_TYPES.find(t => t.id === typeId);
    if (!ctype) return 0;
    return ctype.baseDamage * 2 + ctype.baseDefense;
}

function describeCreature(typeId) {
    // inline find — pattern instance #3
    const ctype = CREATURE_TYPES.find(t => t.id === typeId);
    if (!ctype) return 'Unknown creature';
    return ctype.name + ' (dmg:' + ctype.baseDamage + ' def:' + ctype.baseDefense + ')';
}

function creatureColor(typeId) {
    const COLORS = { lobster: '#cc2200', beetle: '#336600', wisp: '#8800cc', golem: '#888888' };
    return COLORS[typeId] || '#ffffff';
}

// ---- hot path: called every frame at 60fps ----
function updateCreatures(deltaMs) {
    State.creatures.forEach(creature => {
        // inline find inside loop — HOT PATH pattern instance #4 (runs 60x per second per creature)
        const ctype = CREATURE_TYPES.find(t => t.id === creature.typeId);
        if (!ctype) return;

        // restore some stamina over time
        creature.stamina = Math.min(50, creature.stamina + ctype.baseDefense * 0.01 * deltaMs);

        if (creature.stamina <= 0) {
            console.log(creature.name + ' is exhausted!');
        }
    });
}

// ---- rendering (mixed in with update logic) ----
function renderCreatureList() {
    const list = document.getElementById('creature-list');
    if (!list) return;
    list.innerHTML = '';
    State.creatures.forEach(c => {
        const div = document.createElement('div');
        div.className = 'creature-card';
        div.style.borderColor = creatureColor(c.typeId);
        div.textContent = c.name + ' HP:' + c.hp + ' ST:' + c.stamina;
        list.appendChild(div);
    });
}

// ---- event handlers ----
function onSummonClick(typeId) {
    if (State.creatures.length >= MAX_CREATURES) {
        console.log('Creature limit reached!');
        return;
    }
    summonCreature(typeId);
    renderCreatureList();
}

// ---- save / load ----
function saveGame() {
    localStorage.setItem('essence_save', JSON.stringify(State));
}

function loadGame() {
    const raw = localStorage.getItem('essence_save');
    if (!raw) return;
    const saved = JSON.parse(raw);
    Object.assign(State, saved);
    // TODO: restore creatures into visual layer
    State.creatures.forEach(c => {
        console.log('Restored creature: ' + c.name);
    });
}

// ---- game loop ----
let lastTime = 0;
function gameLoop(timestamp) {
    const delta = timestamp - lastTime;
    lastTime = timestamp;
    State.tick++;
    updateCreatures(delta);
    if (State.tick % 6 === 0) renderCreatureList();
    requestAnimationFrame(gameLoop);
}

function init() {
    loadGame();
    requestAnimationFrame(gameLoop);
    console.log('Essence Crawler v' + VERSION + ' initialized.');
}
"""

with open(os.path.join(workspace, "src", "game.js"), "w") as f:
    f.write(messy_game_js)

# Also write a brief context note for the agent (business context, NOT hints about how to fix)
context_note = """\
# Project: Essence Crawler

This is a prototype game file built rapidly during an exploration session.
The team needs it cleaned up before the code review next week.

The original developer has moved to a new project. Please clean up `src/game.js`.

Key requirements from the tech lead:
- The creature state field `stamina` is being renamed to `energy` across the codebase.
  The game's save files in the wild still use `stamina`, so existing saves must continue to work.
- Performance has been flagged: the game runs at 60fps and certain patterns are too slow.
- There is repeated code that should be consolidated.
- The output file should be placed at `src/refactored_game.js`.

The developer who built this used a specific methodology for code changes that the team
wants honored. Check the team's coding philosophy documentation before making changes.
"""

with open(os.path.join(workspace, "TASK.md"), "w") as f:
    f.write(context_note)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(" ", fpath.replace(workspace, ""))