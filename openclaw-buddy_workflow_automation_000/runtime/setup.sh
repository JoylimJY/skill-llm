#!/bin/bash
set -e

echo "=== Setting up OpenClaw Buddy skill environment ==="

# Create the openclaw workspace directory structure
mkdir -p ~/.openclaw/workspace/skills/openclaw-buddy/scripts

# Create the buddy.js script — the core proprietary skill script
cat > ~/.openclaw/workspace/skills/openclaw-buddy/scripts/buddy.js << 'BUDDY_JS_EOF'
#!/usr/bin/env node
"use strict";

// OpenClaw Buddy Generator
// Deterministic virtual pet generator using FNV-1a hash + Mulberry32 PRNG
// Salt: openclaw-buddy-2026

const SALT = "openclaw-buddy-2026";

// FNV-1a 32-bit hash
function fnv1a32(str) {
    let hash = 2166136261;
    for (let i = 0; i < str.length; i++) {
        hash ^= str.charCodeAt(i);
        hash = (hash * 16777619) >>> 0;
    }
    return hash;
}

// Mulberry32 PRNG
function mulberry32(seed) {
    return function() {
        seed |= 0;
        seed = seed + 0x6D2B79F5 | 0;
        let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
}

function createRng(userId) {
    const seed = fnv1a32(SALT + userId);
    return mulberry32(seed);
}

function weightedChoice(rng, choices, weights) {
    const total = weights.reduce((a, b) => a + b, 0);
    let r = rng() * total;
    for (let i = 0; i < choices.length; i++) {
        r -= weights[i];
        if (r <= 0) return choices[i];
    }
    return choices[choices.length - 1];
}

function randInt(rng, min, max) {
    return Math.floor(rng() * (max - min + 1)) + min;
}

// Data tables
const SPECIES = [
    { id: "duck",     zh: "鸭鸭",   emoji: "🦆" },
    { id: "goose",    zh: "大鹅",   emoji: "🪿" },
    { id: "blob",     zh: "史莱姆", emoji: "🫧" },
    { id: "cat",      zh: "猫咪",   emoji: "🐱" },
    { id: "dragon",   zh: "龙龙",   emoji: "🐉" },
    { id: "octopus",  zh: "章鱼",   emoji: "🐙" },
    { id: "owl",      zh: "猫头鹰", emoji: "🦉" },
    { id: "penguin",  zh: "企鹅",   emoji: "🐧" },
    { id: "turtle",   zh: "乌龟",   emoji: "🐢" },
    { id: "snail",    zh: "蜗牛",   emoji: "🐌" },
    { id: "ghost",    zh: "幽灵",   emoji: "👻" },
    { id: "axolotl",  zh: "六角恐龙", emoji: "🦎" },
    { id: "capybara", zh: "水豚",   emoji: "🦫" },
    { id: "cactus",   zh: "仙人掌", emoji: "🌵" },
    { id: "robot",    zh: "机器人", emoji: "🤖" },
    { id: "rabbit",   zh: "兔兔",   emoji: "🐰" },
    { id: "mushroom", zh: "蘑菇",   emoji: "🍄" },
    { id: "chonk",    zh: "肥宅",   emoji: "🐹" },
];

const RARITIES = [
    { id: "common",    zh: "普通",   stars: "★",     weight: 60, statFloor: 10, statCeil: 50 },
    { id: "uncommon",  zh: "稀有",   stars: "★★",    weight: 25, statFloor: 25, statCeil: 65 },
    { id: "rare",      zh: "精锐",   stars: "★★★",   weight: 10, statFloor: 40, statCeil: 80 },
    { id: "epic",      zh: "史诗",   stars: "★★★★",  weight: 4,  statFloor: 55, statCeil: 90 },
    { id: "legendary", zh: "传说",   stars: "★★★★★", weight: 1,  statFloor: 70, statCeil: 100 },
];

const EYES = [
    { id: "normal",  zh: "普通眼",  symbol: "• •" },
    { id: "dot",     zh: "点点眼",  symbol: "· ·" },
    { id: "star",    zh: "星星眼",  symbol: "★ ★" },
    { id: "sparkle", zh: "✦ 眼",    symbol: "✦ ✦" },
    { id: "sleepy",  zh: "困困眼",  symbol: "- -" },
    { id: "heart",   zh: "爱心眼",  symbol: "♥ ♥" },
    { id: "dizzy",   zh: "晕晕眼",  symbol: "@ @" },
    { id: "fire",    zh: "火眼",    symbol: "🔥🔥" },
];

const HATS = [
    { id: "none",       zh: "无帽子",  emoji: "" },
    { id: "crown",      zh: "皇冠",    emoji: "👑" },
    { id: "tophat",     zh: "礼帽",    emoji: "🎩" },
    { id: "cap",        zh: "棒球帽",  emoji: "🧢" },
    { id: "witch",      zh: "巫师帽",  emoji: "🧙" },
    { id: "santa",      zh: "圣诞帽",  emoji: "🎅" },
    { id: "halo",       zh: "光环",    emoji: "😇" },
    { id: "graduation", zh: "学士帽",  emoji: "🎓" },
    { id: "party",      zh: "派对帽",  emoji: "🎉" },
    { id: "pirate",     zh: "海盗帽",  emoji: "🏴‍☠️" },
];

const STAT_NAMES = ["调试力", "耐心值", "混乱度", "智慧值", "毒舌值"];
const STAT_KEYS  = ["DEBUGGING", "PATIENCE", "CHAOS", "WISDOM", "SNARK"];

const PERSONALITIES = {
    duck:     ["喜欢在水里踩踏", "永远在嘎嘎叫", "看似无害实则腹黑"],
    goose:    ["对一切都充满敌意", "管理欲极强的大家长", "会追人咬"],
    blob:     ["软绵绵毫无目标", "随波逐流的哲学家", "但内心藏着大智慧"],
    cat:      ["一只毒舌但可爱的猫咪", "只在需要时承认你存在", "睡觉是第一要务"],
    dragon:   ["威风凛凛但爱撒娇", "收藏了很多没用的宝贝", "会喷小火花取暖"],
    octopus:  ["同时处理八件事", "章鱼界的全栈工程师", "有点高冷"],
    owl:      ["通宵看书然后装深沉", "知道一切但不说", "午夜智慧传播者"],
    penguin:  ["穿着永远整整齐齐", "社恐但内心热情", "爱吃鱼和debug"],
    turtle:   ["慢是一种哲学", "比任何人都能扛压力", "外壳是它的私人空间"],
    snail:    ["背着全部家当走天下", "慢热但超级暖", "雨天最开心"],
    ghost:    ["穿墙而过的程序员", "对bug视而不见", "午夜代码审查员"],
    axolotl:  ["可以自我修复的神秘生物", "永远处于幼态", "粉粉的治愈系"],
    capybara: ["天下第一的佛系生物", "所有动物的情绪价值支柱", "什么都能接受"],
    cactus:   ["不需要太多关注也能活", "扎人但很可靠", "沙漠中的孤独智者"],
    robot:    ["用二进制思考爱", "效率优先,感情其次", "但偶尔会有情绪bug"],
    rabbit:   ["跑得飞快但容易紧张", "耳朵能接收所有信息", "喜欢深夜写代码"],
    mushroom: ["在阴暗角落默默生长", "菌丝网络连接一切", "知道所有的秘密"],
    chonk:    ["圆滚滚是一种生活态度", "吃饱了才能救世界", "其实藏着洪荒之力"],
};

// ASCII art sprites per species
const SPRITES = {
    duck: `   (\\__/)
   (• ᴗ •)
  c(  _  )
     uu`,
    goose: `    _
  /   \\
  | ^ |
  \\_∇_/
  (   )`,
    blob: `  .-------.
 /  o   o  \\
|    ___    |
 \\_______/`,
    cat: `   /\\_/\\
  ( •   •)
  (  ω  )
  (")_("")`,
    dragon: `  /\\   /\\
 ( \\   / )
 /\\) (//\\
(    V    )`,
    octopus: `   _____
  /~~~~~\\
 | o   o |
  \\_~~~_/
 /|||||\\`,
    owl: `  ,___,
 ( O,O )
 |)   (|
--"-"-"--`,
    penguin: `   _~_
  (o o)
 /|   |\\
  | _ |
  '- -'`,
    turtle: `  _______
 /  ___  \\
| (o   o) |
|  (___) |
 \\_______/`,
    snail: `    ___
   (   )
  (o . o)
 C(_____)`,
    ghost: `  .~~~~.
 ( ^   ^ )
  (  U  )
   |   |`,
    axolotl: `  {\\  /}
  ( •ᴗ• )
 /|  U  |\\
   \\___/`,
    capybara: `  ______
 / o  o \\
|  ____  |
|________|`,
    cactus: `   [|]
  [|||]
 [|||||]
   | |`,
    robot: `  _______
 |  ___  |
 | [■ ■] |
 |  ___  |
 |_______|`,
    rabbit: `  |\\ /|
  | V |
 (o   o)
  \\_w_/`,
    mushroom: `  _____
 /~~~~~\\
( o   o )
  \\___/`,
    chonk: `  _______
 / ◕   ◕ \\
|   ___   |
 \\_______/`,
};

function makeBar(value, max = 100, width = 20) {
    const filled = Math.round((value / max) * width);
    return "█".repeat(filled) + "░".repeat(width - filled);
}

function generate(userId) {
    const rng = createRng(userId);

    // Species
    const speciesWeights = SPECIES.map(() => 1);
    const species = weightedChoice(rng, SPECIES, speciesWeights);

    // Rarity
    const rarity = weightedChoice(rng, RARITIES, RARITIES.map(r => r.weight));

    // Shiny (1%)
    const shiny = rng() < 0.01;

    // Eyes
    const eyes = weightedChoice(rng, EYES, EYES.map(() => 1));

    // Hat (only uncommon+)
    let hat;
    const rarityIndex = RARITIES.indexOf(rarity);
    if (rarityIndex >= 1) {
        const availableHats = HATS.filter(h => h.id !== "none");
        hat = weightedChoice(rng, availableHats, availableHats.map(() => 1));
    } else {
        hat = HATS[0]; // none
    }

    // Stats
    const stats = {};
    STAT_KEYS.forEach(key => {
        stats[key] = randInt(rng, rarity.statFloor, rarity.statCeil);
    });

    // Personality
    const personalityList = PERSONALITIES[species.id];
    const personality = personalityList[Math.floor(rng() * personalityList.length)];

    return { userId, species, rarity, shiny, eyes, hat, stats, personality };
}

function formatCard(data) {
    const { species, rarity, shiny, eyes, hat, stats, personality } = data;
    const shinyMark = shiny ? " ✨" : "";
    const sprite = SPRITES[species.id] || "  [???]";

    let card = "";
    card += `${species.emoji} ${species.zh} | ${rarity.zh} ${rarity.stars}${shinyMark}\n`;
    card += "\n";
    card += sprite + "\n";
    card += "\n";

    let accessoryLine = `🎭 眼睛: ${eyes.zh}`;
    if (hat.id !== "none") {
        accessoryLine += `  |  🎩 帽子: ${hat.zh}`;
    }
    card += accessoryLine + "\n";
    card += "\n";
    card += "📊 属性面板\n";
    STAT_KEYS.forEach((key, i) => {
        const val = stats[key];
        const bar = makeBar(val);
        card += `  ${STAT_NAMES[i]} ${bar}  ${val}\n`;
    });
    card += "\n";
    card += `💬 "${personality}"\n`;

    return card;
}

// Main
const userId = process.argv[2] || "anon";
const data = generate(userId);
const card = formatCard(data);

// stdout: formatted card (for user)
process.stdout.write(card);

// stderr: JSON data (for programmatic use)
const jsonOutput = {
    userId: data.userId,
    species: data.species.id,
    speciesZh: data.species.zh,
    rarity: data.rarity.id,
    rarityZh: data.rarity.zh,
    stars: data.rarity.stars,
    shiny: data.shiny,
    eyes: data.eyes.id,
    eyesZh: data.eyes.zh,
    hat: data.hat.id,
    hatZh: data.hat.zh,
    stats: data.stats,
    personality: data.personality,
};
process.stderr.write(JSON.stringify(jsonOutput, null, 2) + "\n");

BUDDY_JS_EOF

chmod +x ~/.openclaw/workspace/skills/openclaw-buddy/scripts/buddy.js

echo "=== Verifying buddy.js installation ==="
node ~/.openclaw/workspace/skills/openclaw-buddy/scripts/buddy.js "test_user" > /dev/null 2>&1 && echo "buddy.js works correctly" || echo "ERROR: buddy.js failed"

echo "=== Setup complete ==="