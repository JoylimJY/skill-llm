import os
import random

random.seed(42)

workspace = "/workspace"

# --- Create realistic deeply nested distractor structure ---

dirs = [
    "references",
    "references/archive",
    "references/archive/2023",
    "references/archive/2024",
    "trips/guangzhou",
    "trips/shenzhen",
    "trips/zhuhai",
    "logistics/transport",
    "logistics/gear",
    "logistics/permits",
    "members/roster",
    "members/waivers",
    "safety/protocols",
    "safety/emergency",
    "finance/budgets",
    "finance/receipts",
    "comms/wechat_drafts",
    "comms/posters",
    "internal/meetings",
    "internal/reviews",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---

distractor_files = {
    "trips/guangzhou/baiyun_mountain_2024_notes.txt": """
白云山 2024年3月记录
天气晴，出发人数8人，无减员。
午餐在明珠楼，下午3点下山。
建议下次早30分钟出发。
""",
    "trips/shenzhen/tanglang_mountain_draft.txt": """
塘朗山路线草稿（未完成）
- 起点：塘朗地铁站
- 终点：大学城北站
- 预计距离：约12km
- 尚未核实门票要求
""",
    "trips/zhuhai/haibin_greenway_proposal.txt": """
珠海海滨绿道提案
全程平坦，适合亲子，无爬升。
返程公交稳定，班次约20分钟一班。
""",
    "logistics/transport/bus_schedule_template.txt": """
公交方案模板
去程：___路公交，首班___，末班___
返程：___路公交，首班___，末班___
打车备选：___（费用约___元）
""",
    "logistics/gear/gear_checklist_old_v1.txt": """
旧版装备清单（v1，已废弃）
- 登山鞋
- 雨衣
- 头灯
- 急救包
注意：此版本未包含防晒和补水要求
""",
    "logistics/permits/fenglining_permit_info.txt": """
凤凰岭预约信息（北京，不适用当前计划）
需提前在公众号预约
每日限流500人
""",
    "members/roster/group_a_members.csv": """姓名,联系方式,紧急联系人
张伟,138xxxx1234,张父
李娜,139xxxx5678,李母
王芳,137xxxx9012,王夫
""",
    "members/waivers/waiver_template_blank.txt": """
免责声明模板（空白）
本人（___）自愿参加本次徒步活动，了解活动风险，同意遵守领队安排。
签字：___  日期：___
""",
    "safety/protocols/general_safety_sop_v2.txt": """
通用安全规程 v2
1. 出发前清点人数
2. 途中每隔一段时间集合
3. 遇恶劣天气取消活动
4. 任何受伤立即停止前进
（注意：具体间隔时间和触发条件请参考各线路方案）
""",
    "safety/emergency/emergency_contacts.txt": """
应急联系人（广州地区）
山岳救援队：020-xxxxxxxx
急救中心：120
当地派出所：110
""",
    "finance/budgets/2024_q3_budget_overview.xlsx.txt": """
2024年Q3活动经费概览（纯文本备份）
白云山活动：实际支出580元（8人），人均72.5元
塘朗山计划：预算800元（10人），人均80元
""",
    "finance/receipts/receipt_log_july.txt": """
7月收据记录
- 公交充值：200元
- 应急打车（白云山）：85元
- 补给品（水+能量棒）：156元
""",
    "comms/wechat_drafts/announcement_template.txt": """
微信群公告模板（草稿）
【活动通知】
活动名称：___
集合地点：___
集合时间：___
领队：___
报名截止：___
""",
    "comms/posters/poster_copy_draft.txt": """
海报文案草稿
「周末山野·治愈系徒步」
时间：待定
地点：待定
人数限制：___
报名方式：___
""",
    "internal/meetings/planning_meeting_20240801_notes.txt": """
2024年8月1日策划会议纪要
议题：Q4活动安排
决议：
1. 优先选择公共交通可达线路
2. 新手比例较高时降低难度等级
3. 所有方案须经队长审核后发布
""",
    "internal/reviews/post_trip_review_baiyun.txt": """
白云山活动复盘
优点：路线熟悉，节奏稳定
不足：午餐点等待时间过长，建议提前预订
改进：增加中途集合口令，减少走散风险
""",
    "references/archive/2023/plan_sample_2023_nanyue.md": """
# 南岳衡山一日游方案（2023年旧版，格式已过时）
## 路线
略

## 时间
08:00 集合
...

## 费用
人均约150元

（此文件格式已废弃，请勿参考）
""",
    "references/archive/2024/plan_sample_2024_xiqiao.md": """
# 西樵山方案（2024年归档版）
路线、装备、费用信息从略。
注意：此文件未使用最新模板格式，仅供历史参考。
""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip())

# --- The critical template file the agent MUST read and follow ---

plan_template = """# 徒步活动完整方案

## 🥾 路线概览

| 字段 | 内容 |
|------|------|
| 线路名称 | |
| 起点 | |
| 终点 | |
| 总距离 | |
| 累计爬升 | |
| 难度等级 | |
| 适合人群 | |
| 最佳季节 | |

## 👀 路线亮点

- 亮点1
- 亮点2
- 亮点3

## 📅 行程安排

### 时间轴

| 时间 | 节点 | 活动 | 备注 |
|------|------|------|------|
| | 集合地点 | 签到、清点人数 | |
| | 出发点 | 正式出发 | |
| | 节点1 | | |
| | 午休点 | 午餐休息 | |
| | 折返/撤退判断点 | | |
| | 终点 | 集合、清点 | |
| | 返程出发 | | |

### 分段详情

| 段落 | 起止点 | 距离 | 预计用时 | 路况 | 休息安排 |
|------|--------|------|----------|------|----------|
| 第一段 | | | | | |
| 第二段 | | | | | |
| 第三段 | | | | | |

## 📍 交通方案

### 去程
- 主选方案：
- 备选方案：

### 返程
- 主选方案：
- 备选方案：
- 失败兜底（打车）：

## ⏰ 风险提示

### 地形风险

### 天气风险

### 队伍风险

### 返程窗口风险

## 🎒 装备与费用

### 装备清单

**必备**
- 

**推荐**
- 

### 费用估算（人均）

| 类别 | 费用 | 备注 |
|------|------|------|
| 交通 | | |
| 门票/预约 | | |
| 补给 | | |
| 应急打车分摊 | | |
| **合计** | | |

## 🌤 假设前提

- 假设1
- 假设2

---

### 信息分类说明
- **已核实**：来自官方或一手来源的信息
- **估算**：基于经验或参考数据的合理推测，已标注
- **假设**：尚未确认、以保守值代入的前提条件

---

## 领队执行建议

### 出发前
- 签到与分组：
- 口令约定：

### 途中
- 节奏控制：
- 前中后队分工：
- 补水提醒：
- 集合点安排：

### 应急处理
- 掉队处理：
- 应急触发条件：
- 取消或降级条件：
"""

template_path = os.path.join(workspace, "references/plan-template.md")
with open(template_path, "w", encoding="utf-8") as f:
    f.write(plan_template.strip())

print("Workspace setup complete.")
print(f"Template written to: {template_path}")
print(f"Total distractor files created: {len(distractor_files)}")