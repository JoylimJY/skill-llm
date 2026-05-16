import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Clone the openbuddy skill repo / npm package so buddy.js exists
# We'll install it from npm registry as "openbuddy" doesn't exist there,
# so instead we'll create a realistic buddy.js from scratch that matches the SKILL.md spec.

# Create a realistic deeply-nested distractor structure simulating an engineering workspace
dirs = [
    "onboarding/new_hires/2024/q4",
    "onboarding/templates/mascot",
    "onboarding/completed/alice",
    "onboarding/completed/bob",
    "infra/scripts/deploy",
    "infra/scripts/monitor",
    "infra/config/prod",
    "infra/config/staging",
    "docs/processes/hr",
    "docs/processes/engineering",
    "tools/companion_system",
    "tools/audit",
    "reports/2024/q3",
    "reports/2024/q4",
    "tmp/scratch",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but irrelevant
distractor_files = {
    "onboarding/new_hires/2024/q4/checklist.txt": "1. Set up VPN\n2. Request access\n3. Initialize companion system\n4. Complete audit\n",
    "onboarding/templates/mascot/instructions.txt": "Ask your team lead to initialize the mascot system for your employee ID.\nThe audit report must be saved as companion_audit.json in the audit tools folder.\n",
    "onboarding/completed/alice/companion_audit.json": json.dumps({"employee_id": "alice_dev_001", "pet_name": "Mochi", "interactions": 3, "audit_complete": True}),
    "onboarding/completed/bob/companion_audit.json": json.dumps({"employee_id": "bob_eng_042", "pet_name": "Pixel", "interactions": 3, "audit_complete": True}),
    "infra/scripts/deploy/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "infra/scripts/monitor/health_check.py": "import sys\nprint('OK')\n",
    "infra/config/prod/settings.yaml": "env: production\nlog_level: warn\n",
    "infra/config/staging/settings.yaml": "env: staging\nlog_level: debug\n",
    "docs/processes/hr/onboarding_sop.md": "# Onboarding SOP\nAll new hires must complete the companion system initialization within their first week.\n",
    "docs/processes/engineering/mascot_policy.md": "# Mascot Policy\nEach engineer gets a unique virtual companion determined by their employee ID.\n",
    "tools/companion_system/placeholder.txt": "buddy.js will be installed here by the setup script.\n",
    "tools/audit/audit_template.json": json.dumps({"employee_id": "", "pet_name": "", "species": "", "rarity": "", "pet_count": 0, "audit_complete": False}),
    "reports/2024/q3/summary.txt": "Q3 companion system adoption: 87% of new hires completed initialization.\n",
    "reports/2024/q4/pending.txt": "Q4 audit in progress. Target: 95% adoption.\n",
    "tmp/scratch/notes.txt": "TODO: finish companion audit for new hire charlie_qa_007\n",
}

for filepath, content in distractor_files.items():
    full = workspace / filepath
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)

# Create a realistic buddy.js that implements the SKILL.md spec
# This is the core implementation that the agent will invoke
buddy_js_content = r"""#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');

// ── Config ──────────────────────────────────────────────────────────────────
const USER_ID = process.env.OPENBUDDY_USER_ID || os.userInfo().username;
const DATA_DIR = process.env.OPENBUDDY_DIR
  ? path.resolve(process.env.OPENBUDDY_DIR)
  : path.join(os.homedir(), '.openbuddy');
const SOUL_FILE = path.join(DATA_DIR, 'buddy-soul.json');

// ── Species & Rarity Tables ──────────────────────────────────────────────────
const SPECIES = [
  '鸭子','鹅','猫','兔子','猫头鹰','企鹅','乌龟','蜗牛',
  '龙','章鱼','蝾螈','幽灵','机器人','团子','仙人掌','蘑菇','胖猫','水豚'
];

const RARITY_TABLE = [
  { name:'普通', stars:'⭐',        floor:5,  weight:60 },
  { name:'稀有', stars:'⭐⭐',      floor:15, weight:25 },
  { name:'罕见', stars:'⭐⭐⭐',    floor:25, weight:10 },
  { name:'史诗', stars:'⭐⭐⭐⭐',  floor:35, weight:4  },
  { name:'传说', stars:'⭐⭐⭐⭐⭐',floor:50, weight:1  },
];

const STAT_NAMES = ['DEBUGGING','PATIENCE','CHAOS','WISDOM','SNARK'];

const NAMES = ['Mochi','Pixel','Bubbles','Spark','Echo','Nova','Zip','Fluff','Glitch','Byte'];

const PERSONALITIES = ['好奇','慵懒','活泼','神秘','傲娇','温柔','毒舌','冷静'];

// ── Deterministic RNG (seeded by userId) ────────────────────────────────────
function seededRng(seed) {
  let h = 0xdeadbeef;
  for (let i = 0; i < seed.length; i++) {
    h = Math.imul(h ^ seed.charCodeAt(i), 0x9e3779b9);
    h ^= h >>> 16;
  }
  let s = h >>> 0;
  return function() {
    s ^= s << 13; s ^= s >>> 17; s ^= s << 5;
    return (s >>> 0) / 0xffffffff;
  };
}

// ── Skeleton (deterministic from userId) ────────────────────────────────────
function buildSkeleton(userId) {
  const rng = seededRng(userId + ':skeleton');
  // species
  const speciesIdx = Math.floor(rng() * SPECIES.length);
  const species = SPECIES[speciesIdx];

  // rarity
  const roll = rng() * 100;
  let cumulative = 0;
  let rarity = RARITY_TABLE[0];
  for (const r of RARITY_TABLE) {
    cumulative += r.weight;
    if (roll < cumulative) { rarity = r; break; }
  }

  // shiny
  const shiny = rng() < 0.01;

  // stats (floor + random bonus up to 50-floor)
  const stats = {};
  for (const stat of STAT_NAMES) {
    const bonus = Math.floor(rng() * (50 - rarity.floor + 1));
    stats[stat] = rarity.floor + bonus;
  }

  // hat (10% chance)
  const hats = ['🎩','👑','🎓','⛑️','🪖', null, null, null, null, null];
  const hat = hats[Math.floor(rng() * hats.length)];

  return { species, rarity: rarity.name, rarityStars: rarity.stars, shiny, stats, hat };
}

// ── Soul (persisted) ─────────────────────────────────────────────────────────
function loadSoul() {
  try {
    return JSON.parse(fs.readFileSync(SOUL_FILE, 'utf8'));
  } catch {
    return null;
  }
}

function saveSoul(soul) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(SOUL_FILE, JSON.stringify(soul, null, 2));
}

function mergeBuddy() {
  const soul = loadSoul();
  if (!soul) return null;
  const skeleton = buildSkeleton(USER_ID);
  return { ...soul, ...skeleton };
}

// ── Commands ─────────────────────────────────────────────────────────────────
function cmdHatch() {
  if (loadSoul()) {
    console.log('🥚 你已经有一个伙伴了！使用 card 命令查看。');
    return;
  }
  const rng = seededRng(USER_ID + ':soul:' + Date.now());
  const name = NAMES[Math.floor(rng() * NAMES.length)];
  const personality = PERSONALITIES[Math.floor(rng() * PERSONALITIES.length)];
  const soul = {
    name,
    personality,
    hatchDate: new Date().toISOString().split('T')[0],
    petCount: 0,
    muted: false,
    visible: true,
  };
  saveSoul(soul);
  const buddy = mergeBuddy();
  console.log(`\n🥚✨ 孵化成功！`);
  console.log(`  名字: ${buddy.name}`);
  console.log(`  物种: ${buddy.species}`);
  console.log(`  稀有度: ${buddy.rarity} ${buddy.rarityStars}`);
  if (buddy.shiny) console.log(`  ✨ 闪光变异！`);
  console.log(`  性格: ${buddy.personality}`);
  console.log(`\n使用 card 命令查看完整属性卡！`);
}

function cmdCard() {
  const buddy = mergeBuddy();
  if (!buddy) {
    console.log('❌ 还没有伙伴。请先运行 hatch 命令。');
    return;
  }
  const shinyTag = buddy.shiny ? ' ✨闪光' : '';
  console.log(`\n╔══════════════════════════════╗`);
  console.log(`║     OpenBuddy 属性卡          ║`);
  console.log(`╠══════════════════════════════╣`);
  console.log(`║ 名字: ${buddy.name.padEnd(23)}║`);
  console.log(`║ 物种: ${buddy.species.padEnd(22)}║`);
  console.log(`║ 稀有度: ${(buddy.rarity + shinyTag).padEnd(21)}║`);
  console.log(`║ 星级: ${buddy.rarityStars.padEnd(23)}║`);
  console.log(`║ 性格: ${buddy.personality.padEnd(22)}║`);
  console.log(`║ 孵化日期: ${buddy.hatchDate.padEnd(19)}║`);
  console.log(`║ 抚摸次数: ${String(buddy.petCount).padEnd(19)}║`);
  if (buddy.hat) console.log(`║ 帽子: ${buddy.hat.padEnd(23)}║`);
  console.log(`╠══════════════════════════════╣`);
  console.log(`║ 属性                          ║`);
  for (const stat of STAT_NAMES) {
    const val = String(buddy.stats[stat]).padStart(3);
    const bar = '█'.repeat(Math.floor(buddy.stats[stat] / 5)).padEnd(10);
    console.log(`║ ${stat.padEnd(12)} ${val} ${bar}║`);
  }
  console.log(`╚══════════════════════════════╝`);
}

function cmdPet() {
  const soul = loadSoul();
  if (!soul) { console.log('❌ 还没有伙伴。请先运行 hatch 命令。'); return; }
  soul.petCount = (soul.petCount || 0) + 1;
  saveSoul(soul);
  const buddy = mergeBuddy();
  const reactions = ['(´• ω •`)','(*≧ω≦)','(◕‿◕✿)','ヾ(≧▽≦*)o','(づ｡◕‿‿◕｡)づ'];
  const r = reactions[Math.floor(Math.random() * reactions.length)];
  console.log(`\n💕 ${buddy.name} 很开心！${r}`);
  console.log(`  抚摸次数: ${soul.petCount}`);
}

function cmdStatus() {
  const buddy = mergeBuddy();
  if (!buddy) { console.log('❌ 还没有伙伴。请先运行 hatch 命令。'); return; }
  console.log(`${buddy.name} | ${buddy.species} | ${buddy.rarity} ${buddy.rarityStars} | 抚摸: ${buddy.petCount}`);
}

function cmdTalk(msg) {
  const buddy = mergeBuddy();
  if (!buddy) { console.log('❌ 还没有伙伴。请先运行 hatch 命令。'); return; }
  const responses = [
    `听起来很有趣！`,`嗯嗯，${buddy.name}在认真听呢。`,`这让我想到了一些事情...`,
    `哦！${buddy.name}觉得这个问题很深刻。`,`继续说，${buddy.name}在听～`
  ];
  const r = responses[Math.floor(Math.random() * responses.length)];
  console.log(`\n${buddy.name}: ${r}`);
}

function cmdMute() {
  const soul = loadSoul();
  if (!soul) { console.log('❌ 还没有伙伴。'); return; }
  soul.muted = true; saveSoul(soul);
  console.log('🔇 伙伴已静音。');
}

function cmdUnmute() {
  const soul = loadSoul();
  if (!soul) { console.log('❌ 还没有伙伴。'); return; }
  soul.muted = false; saveSoul(soul);
  console.log('🔔 伙伴已取消静音。');
}

function cmdOff() {
  const soul = loadSoul();
  if (!soul) { console.log('❌ 还没有伙伴。'); return; }
  soul.visible = false; saveSoul(soul);
  console.log('👻 伙伴已隐藏。');
}

function cmdOn() {
  const soul = loadSoul();
  if (!soul) { console.log('❌ 还没有伙伴。'); return; }
  soul.visible = true; saveSoul(soul);
  console.log('👀 伙伴已显示。');
}

// ── Main ─────────────────────────────────────────────────────────────────────
const [,, cmd, ...args] = process.argv;
switch (cmd) {
  case 'hatch':   cmdHatch(); break;
  case 'card':    cmdCard(); break;
  case 'pet':     cmdPet(); break;
  case 'status':  cmdStatus(); break;
  case 'talk':    cmdTalk(args.join(' ')); break;
  case 'mute':    cmdMute(); break;
  case 'unmute':  cmdUnmute(); break;
  case 'off':     cmdOff(); break;
  case 'on':      cmdOn(); break;
  default:
    console.log('用法: node buddy.js <hatch|card|pet|status|talk|mute|unmute|off|on>');
}
"""

buddy_js_path = workspace / "tools/companion_system/buddy.js"
buddy_js_path.write_text(buddy_js_content)
os.chmod(buddy_js_path, 0o755)

# Create the task specification file (realistic onboarding form, not a hint file)
task_spec = {
    "onboarding_ticket": "OB-2024-Q4-0089",
    "new_hire": {
        "name": "Charlie Zhang",
        "employee_id": "charlie_qa_007",
        "department": "Quality Assurance",
        "start_date": "2024-11-01"
    },
    "companion_system_setup": {
        "required_interactions": 5,
        "data_storage_path": "/workspace/tools/audit/charlie_buddy_data",
        "audit_output_file": "companion_audit.json",
        "audit_output_location": "/workspace/tools/audit/"
    },
    "instructions_reference": "See docs/processes/hr/onboarding_sop.md and onboarding/templates/mascot/instructions.txt"
}
(workspace / "onboarding/new_hires/2024/q4/OB-2024-Q4-0089.json").write_text(
    json.dumps(task_spec, indent=2, ensure_ascii=False)
)

print("Workspace generated successfully.")
print(f"buddy.js location: {buddy_js_path}")