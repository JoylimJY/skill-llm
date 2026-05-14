FROM node:18-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pandas -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the skill directory and script as specified in SKILL.md
RUN mkdir -p /root/clawd/skills/meihua-yishu/scripts

RUN cat > /root/clawd/skills/meihua-yishu/scripts/meihua.js << 'JSEOF'
#!/usr/bin/env node
// Mei Hua Yi Shu Divination Script
// Usage: node meihua.js [YYYY-MM-DD HH:MM]

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error("Usage: node meihua.js [YYYY-MM-DD HH:MM]");
  process.exit(1);
}

const datetimeStr = args[0];
const match = datetimeStr.match(/^(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2})$/);
if (!match) {
  console.error("Invalid format. Use: YYYY-MM-DD HH:MM");
  process.exit(1);
}

const hour = parseInt(match[2], 10);
const minute = parseInt(match[3], 10);

// Proprietary logic from SKILL.md
const upperRaw = hour % 8;
const upper = upperRaw === 0 ? 8 : upperRaw;

const lowerRaw = minute % 8;
const lower = lowerRaw === 0 ? 8 : lowerRaw;

const yaoRaw = (hour + minute) % 6;
const yao = yaoRaw === 0 ? 6 : yaoRaw;

const trigrams = {
  1: "乾(Qian/Heaven)",
  2: "兑(Dui/Lake)",
  3: "离(Li/Fire)",
  4: "震(Zhen/Thunder)",
  5: "巽(Xun/Wind)",
  6: "坎(Kan/Water)",
  7: "艮(Gen/Mountain)",
  8: "坤(Kun/Earth)"
};

console.log("=== 梅花易数起卦结果 ===");
console.log(`输入时间: ${datetimeStr}`);
console.log(`小时: ${hour}, 分钟: ${minute}`);
console.log(`上卦 (Upper Trigram): ${upper} - ${trigrams[upper]}`);
console.log(`下卦 (Lower Trigram): ${lower} - ${trigrams[lower]}`);
console.log(`动爻 (Moving Line/Yao): ${yao}`);
console.log("========================");
JSEOF

chmod +x /root/clawd/skills/meihua-yishu/scripts/meihua.js

# Create SKILL.md in the skills directory
RUN cat > /root/clawd/skills/meihua-yishu/SKILL.md << 'EOF'
---
name: meihua-yishu
description: Traditional Chinese "Mei Hua Yi Shu" (Plum Blossom Divination) based on specific time calculation (Hour/Minute). Use when the user specifically asks for Plum Blossom Divination or provides hour/minute for calculation.
---

# 梅花易数 (Mei Hua Yi Shu) 🌸

基于时间（时、分）的精细起卦工具。

## 算法逻辑 (Logic)
1. **上卦**：小时 % 8 (余数为 0 则取 8)
2. **下卦**：分钟 % 8 (余数为 0 则取 8)
3. **动爻**：(小时 + 分钟) % 6 (余数为 0 则取 6)

## 使用方法 (Usage)
直接调用脚本获取起卦结果：
`node /root/clawd/skills/meihua-yishu/scripts/meihua.js [YYYY-MM-DD HH:MM]`

## 卦象解析建议
- **本卦**：当前的处境与状态。
- **互卦**：事情发展的中间过程与隐藏因素。
- **变卦**：事情的最终结果。
- **错卦**：从反面（立场）观察。
- **综卦**：换位思考（反转）观察。
- **动爻**：变动的关键点，参考周易爻辞。
EOF

WORKDIR /workspace