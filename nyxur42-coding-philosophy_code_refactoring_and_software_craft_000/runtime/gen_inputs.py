import os
import random

random.seed(42)

BASE = "/workspace"

# Create directory structure
dirs = [
    "game/src",
    "game/src/systems",
    "game/src/ui",
    "game/assets/sprites",
    "game/assets/audio",
    "game/dist",
    "game/docs",
    "game/tests",
    "tools/build",
    "tools/lint",
    "notes",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# Distractor files
distractor_files = {
    "game/src/ui/hud.js": "// HUD rendering placeholder\nconst HUD = { draw() {} };",
    "game/src/ui/menu.js": "// Menu system\nconst Menu = { open() {}, close() {} };",
    "game/src/systems/audio.js": "// Audio system stub\nconst Audio = { play(id) {} };",
    "game/assets/sprites/creature.svg": "<svg></svg>",
    "game/assets/audio/ambient.txt": "ambient_loop.ogg",
    "game/dist/bundle.js": "// auto-generated, do not edit",
    "game/docs/design.md": "# Design Notes\n\nEssence v4 design document placeholder.",
    "game/tests/test_state.js": "// State tests placeholder",
    "tools/build/webpack.config.js": "module.exports = {};",
    "tools/lint/.eslintrc.json": '{"rules": {}}',
    "notes/session_log.txt": "Session 1: prototyped core loop\nSession 2: added creatures\nSession 3: added upgrades",
    "notes/todo.txt": "- Fix hybrid rendering\n- Add petal count to flowers\n- Optimize hot path",
}

for path, content in distractor_files.items():
    full = os.path.join(BASE, path)
    with open(full, "w") as f:
        f.write(content)

# THE MAIN MESSY GAME FILE - this is what the agent must refactor
# It contains:
# 1. A repeated pattern (getUpgradeById) used 4 times inline → must be extracted
# 2. A hot-path array removal using splice → must become swap-and-pop
# 3. Data interleaved with logic → data must move to top
# 4. Dead/unused variable (abandonedFeature)
# 5. Parts-based rendering pipeline with a MISSING parts pass in save/load restoration
# 6. The agent must use Comment-Before-Delete workflow for the splice→swap-and-pop change

messy_game_js = r"""// game.js — Essence v4 prototype (messy iteration 7)
// Built by feeling, needs structure pass

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// === GAME STATE ===
let State = {
    essence: { light: 0, dark: 0, life: 100 },
    creatures: [],
    upgrades: [],
    tick: 0
};

// some dialogue i was testing
let testDialogue = "hello world this is a test";
let abandonedFeature = { enabled: false, data: [] }; // never used

// upgrade data scattered near usage
let UPGRADES = [
    { id: 'shard', name: 'Light Shard', cost: 50, effect: 'light+1' },
    { id: 'veil', name: 'Dark Veil', cost: 75, effect: 'dark+1' },
    { id: 'bloom', name: 'Bloom Core', cost: 120, effect: 'life+10' },
    { id: 'root', name: 'Root System', cost: 200, effect: 'light+5' },
    { id: 'spine', name: 'Spine Crystal', cost: 300, effect: 'dark+5' }
];

// creature visual config also scattered
const CREATURE_PARTS = {
    lobster: { head: '#c0392b', body: '#e74c3c', legs: '#c0392b' },
    beetle: { head: '#27ae60', body: '#2ecc71', legs: '#27ae60' },
    wisp: { head: '#8e44ad', body: '#9b59b6', legs: '#8e44ad' }
};

const DEFAULT_PARTS = { head: 'lobster', body: 'lobster', legs: 'lobster' };

// === PARTICLES ===
let particles = [];

function spawnParticle(x, y, color) {
    particles.push({ x, y, color, life: 1.0, vx: (Math.random()-0.5)*2, vy: -Math.random()*2 });
}

function updateParticles() {
    for (let i = particles.length - 1; i >= 0; i--) {
        particles[i].life -= 0.02;
        particles[i].x += particles[i].vx;
        particles[i].y += particles[i].vy;
        if (particles[i].life <= 0) {
            particles.splice(i, 1);
        }
    }
}

// === CREATURES ===
let creatures = [];

function addCreature(id, parts) {
    creatures.push({ id, x: Math.random()*400, y: Math.random()*300, parts: parts || DEFAULT_PARTS });
}

function updateCreatures() {
    for (let i = creatures.length - 1; i >= 0; i--) {
        if (creatures[i].life <= 0) {
            creatures.splice(i, 1);
        }
    }
}

// === PROJECTILES ===
let projectiles = [];

function fireProjectile(x, y, tx, ty) {
    projectiles.push({ x, y, tx, ty, speed: 5, life: 1.0 });
}

function updateProjectiles() {
    for (let i = projectiles.length - 1; i >= 0; i--) {
        projectiles[i].x += (projectiles[i].tx - projectiles[i].x) * 0.1;
        projectiles[i].y += (projectiles[i].ty - projectiles[i].y) * 0.1;
        projectiles[i].life -= 0.01;
        if (projectiles[i].life <= 0) {
            projectiles.splice(i, 1);
        }
    }
}

// === DEBRIS ===
let debris = [];

function spawnDebris(x, y) {
    debris.push({ x, y, rot: 0, life: 2.0 });
}

function updateDebris() {
    for (let i = debris.length - 1; i >= 0; i--) {
        debris[i].life -= 0.01;
        debris[i].rot += 0.05;
        if (debris[i].life <= 0) {
            debris.splice(i, 1);
        }
    }
}

// === UPGRADES ===
function applyUpgrade(upgradeId) {
    // inline search — runs on click
    let upgrade = UPGRADES.find(u => u.id === upgradeId);
    if (!upgrade) return;
    State.upgrades.push(upgradeId);
    console.log('Applied:', upgrade.name);
}

function getUpgradeCost(upgradeId) {
    // inline search
    let upgrade = UPGRADES.find(u => u.id === upgradeId);
    return upgrade ? upgrade.cost : 0;
}

function isUpgradeOwned(upgradeId) {
    return State.upgrades.includes(upgradeId);
}

function renderUpgradePanel() {
    UPGRADES.forEach(u => {
        // inline search — runs in render loop
        let upgrade = UPGRADES.find(u2 => u2.id === u.id);
        let owned = isUpgradeOwned(u.id);
        console.log(upgrade.name, owned ? '(owned)' : `cost: ${upgrade.cost}`);
    });
}

function describeUpgrade(upgradeId) {
    // inline search — fourth occurrence
    let upgrade = UPGRADES.find(u => u.id === upgradeId);
    return upgrade ? `${upgrade.name}: ${upgrade.effect}` : 'Unknown upgrade';
}

// === RENDERING ===
function drawCreature(creature) {
    let colors = CREATURE_PARTS[creature.parts.body] || CREATURE_PARTS.lobster;
    ctx.fillStyle = colors.body;
    ctx.fillRect(creature.x, creature.y, 20, 20);
}

function drawParticle(p) {
    ctx.globalAlpha = p.life;
    ctx.fillStyle = p.color;
    ctx.fillRect(p.x, p.y, 3, 3);
    ctx.globalAlpha = 1;
}

function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    creatures.forEach(c => drawCreature(c));
    particles.forEach(p => drawParticle(p));
    projectiles.forEach(p => {
        ctx.fillStyle = '#fff';
        ctx.fillRect(p.x, p.y, 4, 4);
    });
    renderUpgradePanel();
}

// === SAVE / LOAD ===
function saveGame() {
    let data = {
        state: State,
        creatures: State.creatures.map(c => ({ id: c.id, parts: c.parts }))
    };
    localStorage.setItem('essenceV4', JSON.stringify(data));
}

function loadGame() {
    let raw = localStorage.getItem('essenceV4');
    if (!raw) return;
    let data = JSON.parse(raw);
    State = data.state;
    // restore visual creatures from saved state — BUG: parts not passed!
    State.creatures.forEach(c => {
        addCreature(c.id);
    });
}

// === GAME LOOP ===
function tick() {
    State.tick++;
    updateParticles();
    updateCreatures();
    updateProjectiles();
    updateDebris();
    render();
    requestAnimationFrame(tick);
}

// init
tick();
"""

with open(os.path.join(BASE, "game/src/game.js"), "w") as f:
    f.write(messy_game_js)

# Create a refactoring notes file that sets context without giving answers
refactoring_brief = """# Refactoring Brief — game.js

This file was written in creative/exploration mode across ~7 sessions. 
It needs a structure pass before we hand it to another developer.

We have an internal coding philosophy document (SKILL.md) that defines exactly 
how this refactoring should be done. Please follow it precisely.

Target file to refactor: game/src/game.js
Output: game/src/game_refactored.js
"""

with open(os.path.join(BASE, "notes/refactoring_brief.txt"), "w") as f:
    f.write(refactoring_brief)

print("Workspace generated successfully.")
print(f"Main file: {os.path.join(BASE, 'game/src/game.js')}")