import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── SKILL reference files (already exist per SKILL.md statement) ─────────────
# We create the references/ and data/ directories as the SKILL.md describes
os.makedirs(f"{workspace}/references", exist_ok=True)
os.makedirs(f"{workspace}/data/models", exist_ok=True)
os.makedirs(f"{workspace}/data/brands", exist_ok=True)

# ── Skill reference files ────────────────────────────────────────────────────
model_codes_md = r"""# 轴承型号编码规则

## 基本型号结构

轴承型号通常由以下部分组成：
```
[前缀] + 基本型号 + [后缀]
```

例如：`NU 208 ECP` = 前缀 `NU` + 基本型号 `208` + 后缀 `ECP`

## 深沟球轴承型号（最常见）

### 基本型号规则

| 型号 | 内径计算 | 实际内径 |
|------|---------|---------|
| 6000 | - | 10mm |
| 6200 | - | 10mm |
| 6300 | - | 10mm |
| 6001 | 01 × 5 = 5 | 12mm (特殊) |
| 6204 | 04 × 5 = 20 | 20mm |
| 6210 | 10 × 5 = 50 | 50mm |
| 6230 | 30 × 5 = 150 | 150mm |
| 62/500 | - | 500mm (直接表示) |

**规律**：
- 00 → 10mm
- 01 → 12mm  
- 02 → 15mm
- 03 → 17mm
- 04+ → 数字 × 5 = 内径(mm)

### 直径系列代号（第二位数字）

| 代号 | 系列 | 特点 |
|------|------|------|
| 0 | 特轻系列 | 外径最小，载荷能力较低 |
| 1 | 特轻系列 | - |
| 2 | 轻系列 | 常用，平衡载荷和空间 |
| 3 | 中系列 | 较高载荷能力 |
| 4 | 重系列 | 高载荷，大外径 |

### 宽度系列代号（第一位数字，常为0时省略）

| 代号 | 宽度系列 |
|------|---------|
| 0 | 窄系列（常省略）|
| 1 | 正常系列 |
| 2 | 宽系列 |
| 3 | 特宽系列 |

## 常见前缀含义

| 前缀 | 含义 | 示例 |
|------|------|------|
| N | 外圈无挡边圆柱滚子轴承 | NU208 |
| NU | 内圈无挡边圆柱滚子轴承 | NU208 |
| NJ | 内圈单挡边圆柱滚子轴承 | NJ208 |
| NA | 滚针轴承（带内圈） | NA4901 |
| RNA | 滚针轴承（不带内圈） | RNA4901 |
| HK | 冲压外圈滚针轴承 | HK1512 |
| BK | 冲压外圈滚针轴承（带密封） | BK1512 |
| 232 | 调心滚子轴承（直径系列3，宽度系列2） | 23218 |
| 223 | 调心滚子轴承（直径系列2，宽度系列3） | 22318 |

## 常见后缀含义

### 密封与防尘

| 后缀 | 含义 | 各品牌对照 |
|------|------|-----------|
| - | 开式（无密封）| - |
| Z / ZZ | 单面/双面防尘盖 | SKF: Z/2Z, NSK: Z/ZZ |
| RS / 2RS | 单面/双面橡胶密封 | SKF: RS1/2RS1, NSK: VV/DDU |
| RZ / 2RZ | 单面/双面非接触式密封 | - |
| N | 外圈带止动槽 | - |
| NR | 外圈带止动槽和止动环 | - |

### 游隙等级

| 后缀 | 游隙 |
|------|------|
| C1 | 小于 C2 |
| C2 | 小游隙 |
| CN | 正常游隙（常省略）|
| C3 | 大游隙 |
| C4 | 更大游隙 |
| C5 | 最大游隙 |

### 精度等级

| 后缀 | 精度 | 说明 |
|------|------|------|
| P0 | 普通级 | 常省略 |
| P6 | 6级 | 高于P0 |
| P5 | 5级 | 高精度 |
| P4 | 4级 | 精密级 |
| P2 | 2级 | 超精密级 |

### 保持架

| 后缀 | 含义 |
|------|------|
| M | 黄铜实体保持架 |
| TN / TN9 | 玻璃纤维增强尼龙保持架 |
| J | 钢板冲压保持架 |
| F1 | 碳钢实体保持架 |

### 其他常见后缀

| 后缀 | 含义 |
|------|------|
| C | 内部设计优化 |
| E | 加强型（Enhanced）|
| K | 锥形内孔（1:12） |
| K30 | 锥形内孔（1:30） |
| W | 不锈钢材质 |

## 各品牌型号对照示例

### 6204-2RS 各品牌型号

| 品牌 | 型号 |
|------|------|
| SKF | 6204-2RS1 或 6204-2RSH |
| NSK | 6204DDU 或 6204VV |
| FAG | 6204.2RSR |
| NTN | 6204LLU |
| KOYO | 6204 2RS |
| NACHI | 6204-2NSE |
| TIMKEN | 204PP |
| ZWZ（瓦轴）| 6204-2RS |
| LYC（洛轴）| 6204-2RS |

### NU208 各品牌型号

| 品牌 | 型号 |
|------|------|
| SKF | NU 208 ECP |
| NSK | NU208EW |
| FAG | NU208-E-TVP2 |
| NTN | NU208 |
| KOYO | NU208R |

"""

brands_md = r"""# 轴承品牌参考

## 国际一线品牌

### SKF（斯凯孚）
- **国家**：瑞典
- **成立**：1907年
- **特点**：全球最大轴承制造商，技术领先，品质卓越
- **优势产品**：高速精密轴承、轴承单元、润滑系统
- **型号特点**：后缀系统最完善，如 2RS1（密封）、ECP（玻璃纤维保持架）
- **主要应用**：风电、铁路、机床、汽车

### NSK（恩斯克）
- **国家**：日本
- **成立**：1916年
- **特点**：精密加工技术领先，低噪音、高可靠性
- **优势产品**：滚珠丝杠、线性导轨、汽车轴承
- **型号特点**：DDU（接触式密封）、VV（非接触式密封）
- **主要应用**：汽车、机床、半导体设备

### FAG（舍弗勒）
- **国家**：德国
- **成立**：1883年
- **特点**：精密机械领域专家，高端工业轴承
- **优势产品**：主轴轴承、大型回转支承、滑动轴承
- **型号特点**：-E（加强型）、-TVP2（尼龙保持架）
- **主要应用**：机床、航空、钢铁、风电

### NTN（恩梯恩）
- **国家**：日本
- **成立**：1918年
- **特点**：品种齐全，综合性强
- **优势产品**：轮毂轴承、等速万向节、大型轴承
- **型号特点**：LLU（接触式密封）、ZZ（防尘盖）
- **主要应用**：汽车、工程机械、铁路

### TIMKEN（铁姆肯）
- **国家**：美国
- **成立**：1899年
- **特点**：圆锥滚子轴承鼻祖，耐重载
- **优势产品**：圆锥滚子轴承、合金钢、齿轮传动
- **型号特点**：型号体系不同（如 30208），PP（密封）
- **主要应用**：冶金、采矿、重工、风电

## 国际二线品牌

### KOYO（光洋）
- **国家**：日本
- **特点**：性价比高，汽车轴承强
- **母公司**：捷太格特（JTEKT）

### NACHI（不二越）
- **国家**：日本
- **特点**：综合机械制造商，工具+轴承
- **优势**：液压机器人、钻头工具

### INA（依纳）
- **国家**：德国
- **特点**：滚针轴承专家
- **母公司**：舍弗勒集团

### IKO（艾克欧）
- **国家**：日本
- **特点**：滚针轴承、线性运动产品

### THK
- **国家**：日本
- **特点**：线性导轨和滚珠丝杠先驱

## 中国主要品牌

### ZWZ（瓦轴 - 瓦房店轴承）
- **地区**：辽宁大连瓦房店
- **特点**：中国最大轴承企业，品种最全
- **优势产品**：冶金轴承、铁路轴承、风电轴承
- **地位**：中国轴承工业摇篮

### LYC（洛轴 - 洛阳轴承）
- **地区**：河南洛阳
- **特点**：特大型轴承专家
- **优势产品**：转盘轴承、轧机轴承、军工轴承
- **地位**："一五"期间156项重点工程之一

### C&U（人本轴承）
- **地区**：浙江温州/湖州
- **特点**：民营轴承龙头，汽车轴承强
- **优势产品**：汽车轮毂轴承、电机轴承

## 品牌选择参考

| 应用场景 | 推荐品牌 |
|---------|---------|
| 高精度机床主轴 | SKF、FAG、NSK |
| 风电设备 | SKF、FAG、TIMKEN、ZWZ |
| 汽车OEM | NSK、NTN、KOYO、C&U |
| 铁路车辆 | SKF、TIMKEN、ZWZ |
| 航空/航天 | FAG、SKF、ZYS |
| 半导体设备 | NSK、SKF |
| 工程机械 | TIMKEN、NTN、ZWZ |
| 性价比优先 | ZWZ、LYC、KOYO、NACHI |
| 维修替换 | 根据原厂品牌选择 |
"""

data_structure_md = r"""# 轴承数据结构

## 目录结构

```
data/
├── models/              # 轴承型号数据
│   ├── deep_groove.json     # 深沟球轴承
│   ├── cylindrical.json     # 圆柱滚子轴承
│   ├── tapered.json         # 圆锥滚子轴承
│   ├── angular_contact.json # 角接触球轴承
│   ├── spherical.json       # 调心滚子轴承
│   ├── needle.json          # 滚针轴承
│   └── thrust.json          # 推力轴承
│
└── brands/              # 品牌信息
    ├── skf.json
    ├── nsk.json
    ├── fag.json
    ├── ntn.json
    ├── timken.json
    ├── nbc.json
    └── zwz.json
```

## 轴承型号数据格式

```json
{
  "model": "6204-2RS",
  "type": "deep_groove_ball",
  "type_name": "深沟球轴承",
  "dimensions": {
    "d": 20,
    "D": 47,
    "B": 14
  },
  "load_ratings": {
    "C": 12700,
    "C0": 6600
  },
  "speed_limits": {
    "grease": 15000,
    "oil": 18000
  },
  "weight": 0.106,
  "seal": "2RS",
  "cage": "钢冲压",
  "clearance": "CN",
  "precision": "P0",
  "cross_reference": {
    "SKF": "6204-2RS1",
    "NSK": "6204DDU",
    "FAG": "6204.2RSR",
    "NTN": "6204LLU"
  },
  "applications": ["电机", "泵", "齿轮箱", "家用电器"],
  "features": ["双面密封", "防尘防水", "免维护"]
}
```

## 品牌数据格式

```json
{
  "name": "SKF",
  "full_name": "Svenska Kullagerfabriken",
  "country": "瑞典",
  "founded": 1907,
  "website": "https://www.skf.com",
  "description": "全球领先的轴承制造商，以高品质和创新技术著称",
  "product_lines": [
    {
      "series": "6000",
      "name": "深沟球轴承",
      "features": ["通用型", "高速", "低噪音"],
      "applications": ["电机", "泵", "齿轮箱"]
    },
    {
      "series": "7200",
      "name": "角接触球轴承",
      "features": ["高刚性", "高速", "承受联合载荷"],
      "applications": ["机床主轴", "涡轮增压器"]
    }
  ],
  "specialties": ["高速轴承", "精密轴承", "轴承单元"],
  "model_prefix": {
    "basic": "",
    "explorers": "E",
    "energy_efficient": "E2"
  }
}
```

## 型号对照表格式

```json
{
  "standard_model": "6204",
  "brand_models": {
    "SKF": "6204",
    "NSK": "6204",
    "FAG": "6204",
    "NTN": "6204",
    "KOYO": "6204",
    "NACHI": "6204",
    "TIMKEN": "204",
    "ZWZ": "6204",
    "LYC": "6204"
  },
  "suffix_mapping": {
    "2RS": {
      "SKF": "2RS1",
      "NSK": "DDU",
      "FAG": "2RSR",
      "NTN": "LLU",
      "KOYO": "2RS"
    },
    "ZZ": {
      "SKF": "2Z",
      "NSK": "ZZ",
      "FAG": "2ZR",
      "NTN": "ZZ",
      "KOYO": "ZZ"
    }
  }
}
```
"""

with open(f"{workspace}/references/model-codes.md", "w", encoding="utf-8") as f:
    f.write(model_codes_md)

with open(f"{workspace}/references/brands.md", "w", encoding="utf-8") as f:
    f.write(brands_md)

with open(f"{workspace}/references/data-structure.md", "w", encoding="utf-8") as f:
    f.write(data_structure_md)

# ── Existing (partial/stub) data files that the agent should NOT confuse ─────
# A partial deep_groove.json that is missing the bearings in question
existing_deep_groove = [
    {
        "model": "6000",
        "type": "deep_groove_ball",
        "type_name": "深沟球轴承",
        "dimensions": {"d": 10, "D": 26, "B": 8},
        "load_ratings": {"C": 4620, "C0": 1960},
        "speed_limits": {"grease": 28000, "oil": 36000},
        "weight": 0.023,
        "seal": "open",
        "cage": "钢冲压",
        "clearance": "CN",
        "precision": "P0",
        "cross_reference": {"SKF": "6000", "NSK": "6000", "FAG": "6000", "NTN": "6000"},
        "applications": ["小型电机", "仪器仪表"],
        "features": ["开式", "高速"]
    },
    {
        "model": "6200",
        "type": "deep_groove_ball",
        "type_name": "深沟球轴承",
        "dimensions": {"d": 10, "D": 30, "B": 9},
        "load_ratings": {"C": 5070, "C0": 2280},
        "speed_limits": {"grease": 24000, "oil": 30000},
        "weight": 0.034,
        "seal": "open",
        "cage": "钢冲压",
        "clearance": "CN",
        "precision": "P0",
        "cross_reference": {"SKF": "6200", "NSK": "6200", "FAG": "6200", "NTN": "6200"},
        "applications": ["小型电机", "家用电器"],
        "features": ["开式"]
    }
]
with open(f"{workspace}/data/models/deep_groove.json", "w", encoding="utf-8") as f:
    json.dump(existing_deep_groove, f, ensure_ascii=False, indent=2)

# A minimal cylindrical.json stub
existing_cylindrical = [
    {
        "model": "NU206",
        "type": "cylindrical_roller",
        "type_name": "圆柱滚子轴承",
        "dimensions": {"d": 30, "D": 62, "B": 16},
        "load_ratings": {"C": 28500, "C0": 26000},
        "speed_limits": {"grease": 12000, "oil": 16000},
        "weight": 0.21,
        "seal": "open",
        "cage": "黄铜",
        "clearance": "CN",
        "precision": "P0",
        "cross_reference": {"SKF": "NU 206 ECP", "NSK": "NU206EW", "FAG": "NU206-E-TVP2", "NTN": "NU206"},
        "applications": ["齿轮箱", "泵"],
        "features": ["纯径向载荷"]
    }
]
with open(f"{workspace}/data/models/cylindrical.json", "w", encoding="utf-8") as f:
    json.dump(existing_cylindrical, f, ensure_ascii=False, indent=2)

# Empty stubs for other model files
for fname in ["tapered.json", "angular_contact.json", "spherical.json", "needle.json", "thrust.json"]:
    with open(f"{workspace}/data/models/{fname}", "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

# Existing brand files (partial, plausible but incomplete)
skf_brand = {
    "name": "SKF",
    "full_name": "Svenska Kullagerfabriken",
    "country": "瑞典",
    "founded": 1907,
    "website": "https://www.skf.com",
    "description": "全球领先的轴承制造商，以高品质和创新技术著称",
    "product_lines": [
        {
            "series": "6000",
            "name": "深沟球轴承",
            "features": ["通用型", "高速", "低噪音"],
            "applications": ["电机", "泵", "齿轮箱"]
        }
    ],
    "specialties": ["高速轴承", "精密轴承", "轴承单元"],
    "model_prefix": {"basic": "", "explorers": "E", "energy_efficient": "E2"}
}
with open(f"{workspace}/data/brands/skf.json", "w", encoding="utf-8") as f:
    json.dump(skf_brand, f, ensure_ascii=False, indent=2)

for bname in ["nsk.json", "fag.json", "ntn.json", "timken.json", "nbc.json", "zwz.json"]:
    with open(f"{workspace}/data/brands/{bname}", "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# ── The messy procurement input file the agent must process ──────────────────
# This is the core task input: a CSV with ambiguous/inconsistent bearing model entries
procurement_csv = """序号,设备名称,当前使用型号,当前供应商,备注
1,冷却水泵电机,6205-2RS,SKF,双面密封，轻载
2,传送带减速箱输入轴,NU208,NSK,纯径向载荷
3,搅拌机主轴,6203ZZ,FAG,防尘要求，低速
4,压缩机电机前轴承,6302-2RS,NTN,中等载荷
5,风机电机,6206,SKF,开式无密封
6,液压泵,6204 2RS,KOYO,双面密封
"""

with open(f"{workspace}/procurement_bearings.csv", "w", encoding="utf-8") as f:
    f.write(procurement_csv)

# ── Distractor files ─────────────────────────────────────────────────────────
os.makedirs(f"{workspace}/docs/internal", exist_ok=True)
os.makedirs(f"{workspace}/docs/suppliers", exist_ok=True)
os.makedirs(f"{workspace}/tools/scripts", exist_ok=True)
os.makedirs(f"{workspace}/archive/2022", exist_ok=True)
os.makedirs(f"{workspace}/archive/2023", exist_ok=True)
os.makedirs(f"{workspace}/reports/q1", exist_ok=True)

with open(f"{workspace}/docs/internal/maintenance_schedule.txt", "w") as f:
    f.write("Quarterly bearing inspection: Jan, Apr, Jul, Oct\n")

with open(f"{workspace}/docs/internal/lubrication_guide.txt", "w") as f:
    f.write("Grease type: NLGI #2\nInterval: 500 operating hours\n")

with open(f"{workspace}/docs/suppliers/approved_vendors.txt", "w") as f:
    f.write("Approved: SKF, NSK, FAG, NTN, TIMKEN, ZWZ\n")

with open(f"{workspace}/docs/suppliers/price_list_2023.csv", "w") as f:
    f.write("model,vendor,unit_price_cny\n6204-2RS,SKF,85\n6204DDU,NSK,72\n")

with open(f"{workspace}/tools/scripts/check_inventory.sh", "w") as f:
    f.write("#!/bin/bash\necho 'Inventory check not implemented'\n")

with open(f"{workspace}/tools/scripts/generate_po.py", "w") as f:
    f.write("# Purchase Order generator - stub\nprint('PO generation not implemented')\n")

with open(f"{workspace}/archive/2022/bearing_log.csv", "w") as f:
    f.write("date,model,replaced_by\n2022-03-15,6204,6204-2RS\n")

with open(f"{workspace}/archive/2023/bearing_log.csv", "w") as f:
    f.write("date,model,replaced_by\n2023-07-20,NU208,NU208 ECP\n")

with open(f"{workspace}/reports/q1/summary.txt", "w") as f:
    f.write("Q1 bearing failures: 3\nMost common: 6204-2RS\n")

with open(f"{workspace}/archive/2022/vendor_comparison.xlsx.stub", "w") as f:
    f.write("STUB: binary xlsx file not available\n")

with open(f"{workspace}/docs/internal/bearing_basics.txt", "w") as f:
    f.write("Ball bearings handle radial loads. Roller bearings handle heavier loads.\n")

with open(f"{workspace}/tools/scripts/parse_model.py", "w") as f:
    f.write("# Model parser stub - not functional\ndef parse(model): return {}\n")

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")