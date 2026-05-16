import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ---- Directory structure with distractors ----
dirs = [
    "references",
    "raw_data",
    "raw_data/scraped",
    "raw_data/scraped/tesla",
    "raw_data/scraped/xiaomi",
    "raw_data/reviews",
    "internal_docs",
    "internal_docs/templates",
    "internal_docs/old_reports",
    "logs",
    "config",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ---- SKILL.md ----
skill_md = """\
---
name: car-advisor
version: 1.0.0
description: |
  实时汽车问答与对比分析系统。当用户询问任何买车、选车、汽车参数对比、车型评测、价格分析相关问题时触发此 Skill。

  触发场景（只要涉及以下任一情形就必须使用此 Skill）：
  - 车型参数对比："小米SU7和Model 3哪个好"、"国产车和特斯拉对比"
  - 配置/价格查询："Model Y 焕新版座椅加热有吗"、"问界M9多少钱"
  - 真实车主评价："XX车口碑怎么样"、"懂车帝评分"
  - 购车决策辅助："20-30万预算推荐什么车"、"新能源SUV怎么选"
  - 车辆功能查询："这款车支持V2L吗"、"有没有露营模式"
  - 销量/市场数据："2024年最畅销新能源车"
---

# Car Advisor Skill

一个基于实时数据的汽车问答与对比系统。核心原则：**不用训练数据猜，用实时检索说话**。

---

## 工作流程总览

```
用户提问
   ↓
[Step 1] 解析意图 → 确定车型、对比维度、问题类型
   ↓
[Step 2] 并行数据采集 → 参数 + 价格 + 真实评论
   ↓
[Step 3] 数据整理 → 生成结构化表格或分析报告
   ↓
[Step 4] 输出结论 → 附数据来源、注明采集时间
```

---

## Step 1：意图解析

收到用户问题后，先在内部识别：

| 维度 | 提取内容 |
|---|---|
| 车型列表 | 涉及哪些具体车型（品牌+车系+年款） |
| 问题类型 | 参数查询 / 横向对比 / 口碑评价 / 购车建议 / 价格分析 |
| 核心关注点 | 用户最在意的维度（续航/智驾/内饰/价格/空间…） |
| 数据新鲜度要求 | 是否需要最新价格/最新配置（如焕新版、新款） |

如果车型信息模糊，可以先用 `web_search` 确认当前在售的具体版本（例如"Model Y 2025款"的正式名称）。

---

## Step 2：数据采集策略

### 2.1 数据源优先级

详细数据源列表见 `references/data-sources.md`。

**优先级1 — 官方页面（最权威）**
- 特斯拉：`https://www.tesla.cn/modely`、`https://www.tesla.cn/model3`
- 小米：`https://www.xiaomiev.com`
- 问界/AITO：`https://www.aito.com`
- 理想：`https://www.lixiang.com`
- 比亚迪/各国产品牌官网

**优先级2 — 垂直媒体参数库（最全面）**
- 懂车帝参数页：`https://www.dongchedi.com/auto/params-carIds-x-{car_id}`
- 汽车之家参数对比：`https://www.autohome.com.cn/config/`
- 用 `web_search` 搜索"车型名 参数配置 懂车帝"快速定位页面

**优先级3 — 真实评论/口碑**
- 懂车帝口碑：搜索 `{车型名} 口碑 懂车帝`
- 汽车之家车主点评：搜索 `{车型名} 车主评价 汽车之家`
- 知乎用车报告：搜索 `{车型名} 用车体验 知乎`
- 媒体评测：搜索 `{车型名} 深度评测 2024`

**优先级4 — 价格/销量数据**
- 当前售价：搜索 `{车型名} 最新价格 2025`（价格变动频繁，必须实时）
- 销量数据：搜索 `{车型名} 销量 最新`

### 2.2 并行检索策略

对于多车型对比，并行发起多个搜索，不要串行等待。典型搜索组合：

```
同时搜索：
- "{车型A} 配置参数 {年款}"
- "{车型B} 配置参数 {年款}"
- "{车型A} vs {车型B} 对比 评测"
- "{车型A} 车主评价 缺点"
- "{车型B} 车主评价 缺点"
```

---

## Step 3：数据整理规范

### 3.1 参数对比表模板

生成对比表时，维度根据用户关注点动态调整，但建议包含以下核心维度：

**基础信息层**
| 维度 | 说明 |
|---|---|
| 车型/版本 | 品牌+车系+具体版本+年款 |
| 官方起售价 | 注明是否含补贴，标注采集日期 |
| 车身尺寸 | 长×宽×高，轴距 |
| 定位 | 级别（A/B/C级）、车身形式 |

**动力/续航层（新能源重点）**
| 维度 | 说明 |
|---|---|
| 电池容量 | kWh |
| CLTC续航 | 公里 |
| 最大功率 | kW/马力 |
| 百公里加速 | 秒 |
| 充电功率 | kW（快充峰值） |
| 能耗 | kWh/100km |

**内饰/舒适层**
| 维度 | 说明 |
|---|---|
| 座椅配置 | 加热/通风/按摩/电动调节，注明前后排 |
| 中控屏 | 尺寸+系统 |
| 后排屏 | 有无，尺寸 |
| 车机系统 | 品牌/版本，手机互联能力 |
| 氛围灯 | 有无，分区数 |
| 音响 | 品牌+扬声器数量 |
| 空气悬架 | 有无 |
| 特色功能 | 香氛/冰箱/V2L/露营模式 |

**智驾层**
| 维度 | 说明 |
|---|---|
| 智驾方案 | 品牌/版本 |
| 激光雷达 | 有无 |
| 高速NOA | 是否支持及收费情况 |
| 城市NOA | 是否支持及覆盖城市数 |
| 智驾硬件 | 算力 TOPS |

**安全/空间**
| 维度 | 说明 |
|---|---|
| 安全气囊数 | 个 |
| 后备箱容积 | L（含前备箱） |
| 纯平放倒 | 是否支持，长度 |

### 3.2 评论整合规范

在对比表后，附上真实评论摘要，格式如下：

```
## 车主真实反馈

### [车型A]
**好评高频词**：[提炼3-5个]
**投诉集中点**：[提炼3-5个]
**代表性车主评论**：
- "..." (来源：懂车帝/汽车之家，评分X星)
- "..."

### [车型B]
...

> 数据来源：懂车帝口碑、汽车之家车主点评
> 采集时间：{当前日期}
> 注：评论为用户主观表达，仅供参考
```

---

## Step 4：输出规范

### 4.1 对比结论结构

```
## 一句话总结
[直接给出核心结论，不废话]

## 参数对比表
[完整表格]

## 各维度胜出分析
- 续航/能效：XX胜出，原因...
- 智驾：XX胜出，原因...
- 内饰/舒适：XX胜出，原因...
- 性价比：XX胜出，原因...

## 车主真实反馈
[评论摘要]

## 购买建议
如果你更在意[X]，选[车型A]
如果你更在意[Y]，选[车型B]

> 数据采集时间：{日期} | 价格以官网最新为准
```

### 4.2 单车型查询结构

```
## [车型名] 当前配置一览

[关键参数，重点回答用户问题]

## 各版本差异
[如有多版本，列出关键差异]

## 真实车主评价
[评论摘要]

## 综合评价
[一段客观评述]
```

---

## 特殊场景处理

### 购车预算推荐
当用户给出预算范围时：
1. 先搜索该预算区间当前热门车型（搜索"20-30万 新能源SUV 2025 推荐"）
2. 筛选出3-5款候选，做简要对比
3. 按用户明确提及的偏好（家用/运动/长途/城市）给出排序建议

### 价格变动查询
价格是高度动态的信息（特斯拉尤其频繁调价）：
- 必须实时搜索，不得用训练数据中的价格
- 搜索时加入"最新""2025"等时间词确保信息新鲜度
- 如搜索结果显示价格有争议，注明"以官网实时为准"

### 无法获取数据时
如果某个具体参数无法通过搜索确认：
- 明确说明"未能从实时数据中确认此参数"
- 提供参考来源链接让用户自行核查
- 不用训练数据填充（可能过时）

---

## 数据质量原则

1. **时效性优先**：搜索时始终加年份词（"2025"或"最新"），确保信息非过时版本
2. **交叉验证**：重要参数（价格、续航）尽量从2个来源确认
3. **来源透明**：每条关键数据标注来源（官网/懂车帝/汽车之家）
4. **主观与客观分离**：参数表用客观数据，评论区用主观反馈，两者不混用
5. **不确定性诚实**：数据有争议时说明，不强行给出确定答案

---

## 参考资源

- 详细数据源列表见 `references/data-sources.md`
- 对比维度优先级矩阵见 `references/compare-dimensions.md`
"""

with open(os.path.join(workspace, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# ---- references/data-sources.md (distractor) ----
data_sources_md = """\
# 数据源列表

## 官方数据源
- tesla.cn
- xiaomiev.com
- aito.com
- lixiang.com

## 第三方媒体
- dongchedi.com
- autohome.com.cn
- bitauto.com

## 社区/论坛
- zhihu.com
- weibo.com
- xiaohongshu.com
"""
with open(os.path.join(workspace, "references/data-sources.md"), "w", encoding="utf-8") as f:
    f.write(data_sources_md)

# ---- references/compare-dimensions.md (distractor) ----
compare_dims = """\
# 对比维度优先级矩阵

| 用户类型 | 优先维度 |
|---|---|
| 家用 | 空间 > 舒适 > 续航 > 价格 |
| 科技控 | 智驾 > 车机 > 性能 > 价格 |
| 预算敏感 | 价格 > 续航 > 保值率 > 空间 |
| 长途出行 | 续航 > 充电网络 > 舒适 > 空间 |
"""
with open(os.path.join(workspace, "references/compare-dimensions.md"), "w", encoding="utf-8") as f:
    f.write(compare_dims)

# ---- raw_data/scraped/tesla/model3_params.json ----
tesla_model3 = {
    "source": "tesla.cn",
    "scraped_at": "2025-01-15",
    "model": "特斯拉 Model 3 焕新版",
    "year": "2025",
    "variants": [
        {
            "name": "后驱版",
            "price_cny": 235900,
            "price_note": "不含补贴",
            "dimensions": {"length_mm": 4720, "width_mm": 1921, "height_mm": 1431, "wheelbase_mm": 2875},
            "positioning": "B级轿车",
            "battery_kwh": 60.0,
            "cltc_range_km": 606,
            "max_power_kw": 208,
            "acceleration_0_100": 6.1,
            "fast_charge_kw": 170,
            "energy_consumption_kwh_100km": 12.5
        },
        {
            "name": "长续航全轮驱动版",
            "price_cny": 295900,
            "price_note": "不含补贴",
            "dimensions": {"length_mm": 4720, "width_mm": 1921, "height_mm": 1431, "wheelbase_mm": 2875},
            "positioning": "B级轿车",
            "battery_kwh": 78.0,
            "cltc_range_km": 713,
            "max_power_kw": 366,
            "acceleration_0_100": 4.4,
            "fast_charge_kw": 250,
            "energy_consumption_kwh_100km": 13.1
        }
    ],
    "interior": {
        "front_seat_heating": True,
        "front_seat_ventilation": False,
        "rear_seat_heating": True,
        "seat_massage": False,
        "center_screen_inch": 15.4,
        "rear_screen": False,
        "car_system": "Tesla OS",
        "ambient_light": False,
        "audio_brand": "Tesla Premium Audio",
        "audio_speakers": 17,
        "air_suspension": False,
        "special_features": ["宠物模式", "哨兵模式"]
    },
    "adas": {
        "system_name": "FSD (中国)",
        "lidar": False,
        "highway_noa": True,
        "highway_noa_fee": "订阅制",
        "city_noa": True,
        "city_noa_cities": "全国",
        "compute_tops": 144
    },
    "safety_space": {
        "airbags": 8,
        "trunk_liters": 594,
        "frunk_liters": 88,
        "flat_fold": True,
        "flat_fold_length_mm": 1850
    }
}
with open(os.path.join(workspace, "raw_data/scraped/tesla/model3_params.json"), "w", encoding="utf-8") as f:
    json.dump(tesla_model3, f, ensure_ascii=False, indent=2)

# ---- raw_data/scraped/xiaomi/su7_params.json ----
xiaomi_su7 = {
    "source": "xiaomiev.com",
    "scraped_at": "2025-01-15",
    "model": "小米 SU7",
    "year": "2025",
    "variants": [
        {
            "name": "标准版",
            "price_cny": 215900,
            "price_note": "不含补贴",
            "dimensions": {"length_mm": 4997, "width_mm": 1963, "height_mm": 1440, "wheelbase_mm": 3000},
            "positioning": "B级轿车",
            "battery_kwh": 73.6,
            "cltc_range_km": 700,
            "max_power_kw": 220,
            "acceleration_0_100": 5.28,
            "fast_charge_kw": 80,
            "energy_consumption_kwh_100km": 12.1
        },
        {
            "name": "Pro版",
            "price_cny": 245900,
            "price_note": "不含补贴",
            "dimensions": {"length_mm": 4997, "width_mm": 1963, "height_mm": 1440, "wheelbase_mm": 3000},
            "positioning": "B级轿车",
            "battery_kwh": 94.3,
            "cltc_range_km": 830,
            "max_power_kw": 220,
            "acceleration_0_100": 5.28,
            "fast_charge_kw": 150,
            "energy_consumption_kwh_100km": 12.5
        },
        {
            "name": "Max版",
            "price_cny": 299900,
            "price_note": "不含补贴",
            "dimensions": {"length_mm": 4997, "width_mm": 1963, "height_mm": 1440, "wheelbase_mm": 3000},
            "positioning": "B级轿车",
            "battery_kwh": 101.0,
            "cltc_range_km": 800,
            "max_power_kw": 495,
            "acceleration_0_100": 2.78,
            "fast_charge_kw": 210,
            "energy_consumption_kwh_100km": 15.3
        }
    ],
    "interior": {
        "front_seat_heating": True,
        "front_seat_ventilation": True,
        "rear_seat_heating": True,
        "seat_massage": False,
        "center_screen_inch": 16.1,
        "rear_screen": False,
        "car_system": "HyperOS Auto",
        "ambient_light": True,
        "ambient_light_zones": 256,
        "audio_brand": "Xiaomi Audio",
        "audio_speakers": 23,
        "air_suspension": False,
        "special_features": ["V2L放电", "车载冰箱(Pro/Max)"]
    },
    "adas": {
        "system_name": "小米智能驾驶",
        "lidar": True,
        "highway_noa": True,
        "highway_noa_fee": "标准版免费，Pro/Max免费",
        "city_noa": True,
        "city_noa_cities": "100+城市",
        "compute_tops": 508
    },
    "safety_space": {
        "airbags": 6,
        "trunk_liters": 517,
        "frunk_liters": 105,
        "flat_fold": True,
        "flat_fold_length_mm": 1950
    }
}
with open(os.path.join(workspace, "raw_data/scraped/xiaomi/su7_params.json"), "w", encoding="utf-8") as f:
    json.dump(xiaomi_su7, f, ensure_ascii=False, indent=2)

# ---- raw_data/reviews/tesla_model3_reviews.txt ----
tesla_reviews = """\
用户ID: tsl_fan_001 | 来源: 懂车帝 | 评分: 4星
"续航真的够用，上海到杭州轻松来回，超充体验也很流畅。"

用户ID: tsl_fan_002 | 来源: 汽车之家 | 评分: 3星
"内饰太极简了，一根棍控制全部，老人用起来确实不习惯。"

用户ID: tsl_fan_003 | 来源: 懂车帝 | 评分: 5星
"FSD开了一年，高速基本不用手，体验很惊艳。但城市还是要注意接管。"

用户ID: tsl_fan_004 | 来源: 知乎 | 评分: 3星
"做工一般，门板有点松，中控台缝隙不均匀，感觉不如同价位国产精致。"

用户ID: tsl_fan_005 | 来源: 汽车之家 | 评分: 4星
"降价太频繁了，心态崩了，但客观说这车驾驶质感真的好，底盘扎实。"

用户ID: tsl_fan_006 | 来源: 懂车帝 | 评分: 2星
"客服和售后太差了，维修等配件等了三个月，希望改善服务。"

用户ID: tsl_fan_007 | 来源: 汽车之家 | 评分: 4星
"没有HUD、没有氛围灯，这些对我无所谓，但是没有后排出风口有点过分。"

用户ID: tsl_fan_008 | 来源: 懂车帝 | 评分: 4星
"座椅舒适度很好，长途不累，前排腿部空间充足。后排稍逼仄但可以接受。"
"""
with open(os.path.join(workspace, "raw_data/reviews/tesla_model3_reviews.txt"), "w", encoding="utf-8") as f:
    f.write(tesla_reviews)

# ---- raw_data/reviews/xiaomi_su7_reviews.txt ----
xiaomi_reviews = """\
用户ID: xm_su7_001 | 来源: 懂车帝 | 评分: 5星
"外观太帅了，停车场回头率超高，米粉买来真没后悔。"

用户ID: xm_su7_002 | 来源: 汽车之家 | 评分: 4星
"HyperOS系统真的好用，和手机无缝连接，小米生态用户无脑入。"

用户ID: xm_su7_003 | 来源: 懂车帝 | 评分: 3星
"标准版充电慢是硬伤，80kW峰值充个电要等很久，出远门要规划好。"

用户ID: xm_su7_004 | 来源: 知乎 | 评分: 4星
"智驾用了半年，激光雷达感知确实强，识别能力比纯视觉系统稳很多。"

用户ID: xm_su7_005 | 来源: 汽车之家 | 评分: 2星
"交车时发现车门缝隙不均匀，找售后处理又拖了两周，品控有待提升。"

用户ID: xm_su7_006 | 来源: 懂车帝 | 评分: 5星
"空间真的大，轴距3米，后排坐两个180身高的男人也不挤，比同级别宽敞。"

用户ID: xm_su7_007 | 来源: 汽车之家 | 评分: 4星
"V2L功能实测可以用，带了一台电磁炉户外用餐，很实用。"

用户ID: xm_su7_008 | 来源: 懂车帝 | 评分: 3星
"底盘调校偏软，运动感不如Model 3，想要驾驶乐趣建议试驾后决定。"
"""
with open(os.path.join(workspace, "raw_data/reviews/xiaomi_su7_reviews.txt"), "w", encoding="utf-8") as f:
    f.write(xiaomi_reviews)

# ---- Distractor files ----

# internal_docs/templates/old_format_v1.md
with open(os.path.join(workspace, "internal_docs/templates/old_format_v1.md"), "w", encoding="utf-8") as f:
    f.write("""\
# OLD Template v1 (DEPRECATED - Do NOT use)

## Overview
[车型总览]

## Specs
[规格]

## Price
[价格]

Note: This template was replaced in Q3 2024.
""")

# internal_docs/old_reports/sample_report_2023.md
with open(os.path.join(workspace, "internal_docs/old_reports/sample_report_2023.md"), "w", encoding="utf-8") as f:
    f.write("""\
# 2023款比亚迪海豹 vs 特斯拉Model 3 对比报告

（本报告为历史存档，格式已过时）

## 总结
两款车都不错。

## 参数
- 比亚迪海豹：续航700km，价格21万
- Model 3：续航606km，价格23万

## 结论
看个人喜好。
""")

# internal_docs/old_reports/notes_q4_2024.txt
with open(os.path.join(workspace, "internal_docs/old_reports/notes_q4_2024.txt"), "w", encoding="utf-8") as f:
    f.write("""\
Q4 2024 meeting notes:
- Need to update report format to v2
- Add ADAS section
- Include owner feedback section
- Format change effective Jan 2025
""")

# logs/scraper_run_20250115.log
with open(os.path.join(workspace, "logs/scraper_run_20250115.log"), "w", encoding="utf-8") as f:
    f.write("""\
2025-01-15 08:00:01 INFO Starting scraper run
2025-01-15 08:00:05 INFO Fetching tesla.cn/model3 ... OK (200)
2025-01-15 08:00:07 INFO Fetching xiaomiev.com/su7 ... OK (200)
2025-01-15 08:01:12 INFO Fetching dongchedi reviews tesla model3 ... OK
2025-01-15 08:01:15 INFO Fetching dongchedi reviews xiaomi su7 ... OK
2025-01-15 08:01:20 INFO Data saved to raw_data/
2025-01-15 08:01:21 INFO Run complete. 4 sources scraped.
""")

# config/scraper_config.yaml
with open(os.path.join(workspace, "config/scraper_config.yaml"), "w", encoding="utf-8") as f:
    f.write("""\
scraper:
  timeout_seconds: 30
  retry_count: 3
  user_agent: "CarAdvisorBot/1.0"
  rate_limit_rps: 2

output:
  format: json
  directory: raw_data/scraped

sources:
  - name: tesla_official
    url: https://www.tesla.cn
  - name: xiaomi_official
    url: https://www.xiaomiev.com
  - name: dongchedi
    url: https://www.dongchedi.com
  - name: autohome
    url: https://www.autohome.com.cn
""")

# raw_data/scraped/tesla/model3_raw_html_snippet.txt (distractor)
with open(os.path.join(workspace, "raw_data/scraped/tesla/model3_raw_html_snippet.txt"), "w", encoding="utf-8") as f:
    f.write("""\
<!-- Raw HTML snippet - not structured, for archival only -->
<div class="specs-row"><span>续航里程</span><span>606 km</span></div>
<div class="specs-row"><span>起售价</span><span>235,900</span></div>
<!-- ... truncated ... -->
""")

# raw_data/scraped/xiaomi/su7_press_release.txt (distractor)
with open(os.path.join(workspace, "raw_data/scraped/xiaomi/su7_press_release.txt"), "w", encoding="utf-8") as f:
    f.write("""\
小米SU7发布会新闻稿 (2024-03-28)

今日，小米汽车正式发布旗下首款量产车型SU7。雷军表示：
"我们不是为了造一辆便宜的车，而是要造一辆好车。"

SU7标准版售价21.59万元人民币，Pro版24.59万元，Max版29.99万元。
（注：本新闻稿为历史价格，以官方最新公告为准）
""")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")