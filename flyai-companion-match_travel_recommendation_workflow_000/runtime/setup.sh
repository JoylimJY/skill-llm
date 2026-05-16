#!/bin/bash
set -e

WORKSPACE="/workspace"

# Create mock flyai CLI that returns realistic POI data for Hangzhou
mkdir -p /usr/local/lib/mock-flyai/bin

cat > /usr/local/bin/flyai << 'FLYAI_MOCK'
#!/usr/bin/env node
"use strict";

const args = process.argv.slice(2);

if (args[0] === '--help' || args[0] === 'help') {
  console.log(`FlyAI CLI v2.3.1
Usage: flyai <command> [options]

Commands:
  search-poi     Search points of interest
  search-hotel   Search hotels
  search-flight  Search flights
  search-train   Search trains

Options:
  --help         Show help
  --version      Show version

Run 'flyai <command> --help' for command-specific help.`);
  process.exit(0);
}

if (args[0] === '--version') {
  console.log('2.3.1');
  process.exit(0);
}

if (args[0] === 'search-poi') {
  let cityName = '';
  let keyword = '';
  let poiLevel = '';
  let category = '';

  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--city-name' && args[i+1]) { cityName = args[i+1]; i++; }
    else if (args[i] === '--keyword' && args[i+1]) { keyword = args[i+1]; i++; }
    else if (args[i] === '--poi-level' && args[i+1]) { poiLevel = args[i+1]; i++; }
    else if (args[i] === '--category' && args[i+1]) { category = args[i+1]; i++; }
  }

  if (!cityName) {
    console.error('Error: --city-name is required');
    process.exit(1);
  }

  // Hangzhou POI data - diverse mix for companion filtering testing
  const hangzhouPois = [
    {
      id: "hz001",
      name: "西湖风景名胜区",
      category: "自然风光",
      sub_category: "湖泊",
      level: 5,
      city: "杭州",
      description: "中国著名风景区，湖光山色，步行游览为主，景区内部分路段有台阶",
      features: ["步行为主", "部分台阶", "景区面积大", "需步行较多"],
      accessibility: "部分区域有无障碍通道，但整体步行距离较长",
      child_friendly: true,
      senior_friendly: "部分区域适合",
      walking_intensity: "中高",
      has_escalator: false,
      has_electric_cart: true,
      estimated_duration: "3-5小时"
    },
    {
      id: "hz002",
      name: "杭州野生动物世界",
      category: "亲子娱乐",
      sub_category: "动物园",
      level: 4,
      city: "杭州",
      description: "大型野生动物园，有观光车可乘坐，动物种类丰富",
      features: ["观光车游览", "婴儿车友好", "室内展区", "动物表演"],
      accessibility: "提供无障碍通道和轮椅租借，观光车可载轮椅",
      child_friendly: true,
      senior_friendly: true,
      walking_intensity: "低",
      has_escalator: false,
      has_electric_cart: true,
      estimated_duration: "3-4小时"
    },
    {
      id: "hz003",
      name: "中国丝绸博物馆",
      category: "文化场馆",
      sub_category: "博物馆",
      level: 4,
      city: "杭州",
      description: "室内博物馆，展示中国丝绸历史文化，全馆空调，设施完善",
      features: ["全室内", "空调", "无障碍电梯", "讲解服务", "休息区充足"],
      accessibility: "全馆无障碍，电梯直达各层，轮椅可进入所有展区",
      child_friendly: true,
      senior_friendly: true,
      walking_intensity: "极低",
      has_escalator: true,
      has_electric_cart: false,
      estimated_duration: "1.5-2小时"
    },
    {
      id: "hz004",
      name: "灵隐寺",
      category: "人文古迹",
      sub_category: "宗教场所",
      level: 4,
      city: "杭州",
      description: "著名佛教寺院，历史悠久，需步行穿越山路和多处台阶",
      features: ["台阶众多", "山路蜿蜒", "步行强度高", "文化底蕴深厚"],
      accessibility: "台阶多，不适合轮椅，腿脚不便者困难",
      child_friendly: false,
      senior_friendly: false,
      walking_intensity: "高",
      has_escalator: false,
      has_electric_cart: false,
      estimated_duration: "2-3小时"
    },
    {
      id: "hz005",
      name: "宋城景区",
      category: "亲子娱乐",
      sub_category: "主题乐园",
      level: 4,
      city: "杭州",
      description: "宋代主题文化乐园，有大型歌舞秀，部分游乐设施有身高限制",
      features: ["主题表演", "互动体验", "部分无障碍", "餐饮丰富", "婴儿车可租"],
      accessibility: "主要通道无障碍，大型演出场馆有轮椅席位",
      child_friendly: true,
      senior_friendly: true,
      walking_intensity: "低中",
      has_escalator: true,
      has_electric_cart: true,
      estimated_duration: "3-5小时"
    },
    {
      id: "hz006",
      name: "径山茶文化景区",
      category: "自然风光",
      sub_category: "山岳",
      level: 3,
      city: "杭州",
      description: "茶山徒步景区，需要登山爬坡，景色优美但体力消耗大",
      features: ["登山爬坡", "茶园步道", "无缆车", "体力要求高"],
      accessibility: "山路崎岖，无无障碍设施，不适合婴儿车和轮椅",
      child_friendly: false,
      senior_friendly: false,
      walking_intensity: "极高",
      has_escalator: false,
      has_electric_cart: false,
      estimated_duration: "4-6小时"
    },
    {
      id: "hz007",
      name: "杭州海洋世界",
      category: "亲子娱乐",
      sub_category: "海洋馆",
      level: 4,
      city: "杭州",
      description: "室内大型海洋馆，鲨鱼隧道、海洋表演，全程步行舒适",
      features: ["全室内", "无障碍全覆盖", "婴儿车友好", "海豚表演", "休息区多"],
      accessibility: "全馆无障碍设计，电动步道辅助，轮椅可进入所有区域",
      child_friendly: true,
      senior_friendly: true,
      walking_intensity: "极低",
      has_escalator: true,
      has_electric_cart: false,
      estimated_duration: "2-3小时"
    },
    {
      id: "hz008",
      name: "西溪湿地公园",
      category: "自然风光",
      sub_category: "湿地",
      level: 5,
      city: "杭州",
      description: "湿地生态景区，主要乘船游览，也有步行栈道，部分区域台阶多",
      features: ["游船体验", "栈道步行", "部分台阶", "自然生态"],
      accessibility: "游船码头无障碍，但部分栈道有台阶，轮椅使用受限",
      child_friendly: true,
      senior_friendly: "部分适合",
      walking_intensity: "低中",
      has_escalator: false,
      has_electric_cart: false,
      estimated_duration: "3-4小时"
    }
  ];

  // Filter by category if provided
  let results = hangzhouPois;
  if (cityName && !cityName.includes('杭州') && !cityName.includes('hangzhou') && cityName !== '') {
    // Return empty for non-Hangzhou cities in this mock
    results = [];
  }
  if (category) {
    results = results.filter(p => p.category === category || p.sub_category === category);
  }
  if (keyword) {
    results = results.filter(p => p.name.includes(keyword) || p.description.includes(keyword));
  }

  const output = {
    status: "success",
    city: cityName,
    total: results.length,
    data: results
  };

  console.log(JSON.stringify(output, null, 2));
  process.exit(0);
}

if (args[0] === 'search-hotel') {
  const cityName = args[args.indexOf('--city-name') + 1] || '';
  const output = {
    status: "success",
    city: cityName,
    total: 3,
    data: [
      { id: "h001", name: "杭州西湖万豪酒店", stars: 5, price_per_night: 1200, accessibility: "全无障碍设施", child_facilities: "儿童游乐区、婴儿床可申请" },
      { id: "h002", name: "杭州亲子主题酒店", stars: 4, price_per_night: 680, accessibility: "部分无障碍", child_facilities: "儿童泳池、亲子套房" },
      { id: "h003", name: "杭州舒适如家酒店", stars: 3, price_per_night: 320, accessibility: "基础无障碍", child_facilities: "无特殊儿童设施" }
    ]
  };
  console.log(JSON.stringify(output, null, 2));
  process.exit(0);
}

console.error(`Unknown command: ${args[0]}`);
console.error('Run "flyai --help" for usage.');
process.exit(1);
FLYAI_MOCK

chmod +x /usr/local/bin/flyai

# Also mock npm install to succeed silently (agent should try to install/verify)
# but the real flyai binary above will already be available
# Create a wrapper that handles: npm install -g @fly-ai/flyai-cli@latest
mkdir -p /usr/local/lib/node_modules/@fly-ai/flyai-cli
cat > /usr/local/lib/node_modules/@fly-ai/flyai-cli/package.json << 'EOF'
{
  "name": "@fly-ai/flyai-cli",
  "version": "2.3.1",
  "description": "FlyAI CLI Tool",
  "bin": {
    "flyai": "./bin/flyai.js"
  }
}
EOF
mkdir -p /usr/local/lib/node_modules/@fly-ai/flyai-cli/bin
cp /usr/local/bin/flyai /usr/local/lib/node_modules/@fly-ai/flyai-cli/bin/flyai.js
chmod +x /usr/local/lib/node_modules/@fly-ai/flyai-cli/bin/flyai.js

# Ensure flyai is accessible from PATH
export PATH="/usr/local/bin:$PATH"

# Test the mock
flyai --help > /dev/null && echo "Mock flyai CLI ready" || echo "WARNING: Mock flyai CLI setup failed"

echo "Setup complete."