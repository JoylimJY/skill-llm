import os
import random

random.seed(42)

# Create a realistic agency workspace with many distractor files
base = "/workspace"

# --- Directory Structure ---
dirs = [
    "clients/active",
    "clients/archived",
    "clients/pending",
    "templates/styles",
    "templates/scripts",
    "internal/guidelines",
    "internal/training",
    "reports/2024",
    "reports/2023",
    "assets/icons",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor Files ---

# 1. Old completed client report (different client, different format - a trap)
with open(os.path.join(base, "reports/2024/client_007_report.md"), "w", encoding="utf-8") as f:
    f.write("""# 客户007号外号报告

昵称建议：
1. 暗影刀客
2. 铁血战神
3. 破军

备注：客户满意，已交付。
""")

# 2. An incomplete template file (a trap - wrong format)
with open(os.path.join(base, "templates/styles/output_template_v1.md"), "w", encoding="utf-8") as f:
    f.write("""# 外号输出模板 v1 (已废弃)

[外号A] - [解释]
[外号B] - [解释]
[外号C] - [解释]

NOTE: This template is DEPRECATED. Do not use.
""")

# 3. Style reference sheet (distractor)
with open(os.path.join(base, "templates/styles/style_guide.txt"), "w", encoding="utf-8") as f:
    f.write("""风格参考清单

武侠古风: 逍遥子、剑无痕、醉卧长安
酷炫潮流: 影Zero、暗夜猎手
可爱软萌: 小泡芙、团子
搞笑沙雕: 睡不醒的猫
商务稳重: 远行者、北极星
文艺清冷: 晚风不渡、山河故人
游戏竞技: 神之手、暴走萝莉
""")

# 4. Internal guidelines doc
with open(os.path.join(base, "internal/guidelines/naming_policy.txt"), "w", encoding="utf-8") as f:
    f.write("""起名规范内部文件 v3.2

1. 所有外号必须经过审核
2. 禁止使用敏感词汇
3. 每份报告需要存档
4. 客户反馈需在48小时内处理
""")

# 5. Training materials
with open(os.path.join(base, "internal/training/onboarding_notes.txt"), "w", encoding="utf-8") as f:
    f.write("""新人培训笔记

- 第一步：了解客户需求
- 第二步：确认风格偏好
- 第三步：生成创意名字
- 不要给出超过10个建议（太多会让客户困惑）
""")

# 6. Old client archived record
with open(os.path.join(base, "clients/archived/client_wang_2023.txt"), "w", encoding="utf-8") as f:
    f.write("""客户：王某某
性别：男
用途：游戏ID
风格：武侠
最终选择：沧浪剑客
""")

# 7. Pending client with incomplete info
with open(os.path.join(base, "clients/pending/client_pending_001.txt"), "w", encoding="utf-8") as f:
    f.write("""待处理客户
姓名：未知
性别：未确认
备注：客户未回复，等待中...
""")

# 8. A fake "script" distractor
with open(os.path.join(base, "templates/scripts/greeting_script.txt"), "w", encoding="utf-8") as f:
    f.write("""破冰话术脚本

选项A: "来来来，起外号这事儿我熟！先说说，主角是位帅锅还是美铝？"
选项B: "起外号可是门艺术~ 你是男是女还是...神秘生物？"
选项C: "哟，要起个响亮的名号？等等，我得先知道..."
""")

# 9. Random stats file
with open(os.path.join(base, "reports/2023/annual_stats.txt"), "w", encoding="utf-8") as f:
    f.write("""2023年度统计
总服务客户数：347
满意度：92%
最受欢迎风格：文艺清冷 (28%), 游戏竞技 (24%), 武侠古风 (19%)
""")

# 10. A different format report as trap
with open(os.path.join(base, "reports/2024/quick_suggestions.txt"), "w", encoding="utf-8") as f:
    f.write("""快速推荐（非正式）
暗夜使者 / 星河旅人 / 流光碎影
""")

# 11. Assets placeholder
with open(os.path.join(base, "assets/icons/emoji_list.txt"), "w", encoding="utf-8") as f:
    f.write("""常用表情符号
🎭 🗡️ 🔥 🐱 😂 💼 🌙 🎮 💬 ✨ 🌸
""")

# 12. Internal memo
with open(os.path.join(base, "internal/guidelines/memo_2024_03.txt"), "w", encoding="utf-8") as f:
    f.write("""内部备忘录 2024-03-15

提醒：新版报告格式已于本月起强制执行。
旧版格式（无创意解读部分）不再接受。
每个外号必须附带详细的创意解读说明。
""")

# === THE MAIN TASK FILE ===
# A realistic, messy multi-turn conversation transcript
# Client profile: Female, wants nickname for game (王者荣耀), 
# style preference: 文艺清冷 + 带点游戏竞技感, real name hint: 陈晓雨
conversation = """=== 客户接待记录 ===
接待员：小慧
日期：2024-06-12
客户编号：CLI-2024-089

--- 对话记录 ---

[顾问]: 来来来，起外号这事儿我熟！先说说，主角是位帅锅还是美铝？😏

[客户]: 哈哈哈 是女生啦！给我自己起的

[顾问]: 好嘞美女！那是给自己用咯？想用在哪里呀，游戏？微信？还是别的地方？

[客户]: 主要是游戏用，王者荣耀里面，但是朋友圈偶尔也会用

[顾问]: 哦豁！王者荣耀的战场ID，那得够响亮！来选个调调——
想当江湖侠客、都市潮人、还是可爱担当？或者...文艺小清新？

[客户]: 我比较喜欢那种文艺清冷的感觉，但是游戏里又想霸气一点
就是...文艺和竞技感都要，能兼顾吗哈哈

[顾问]: 当然可以！文艺冷峻+竞技霸气，这个组合我太喜欢了！
顺带问一句，你名字里有什么字吗？或者有什么特别喜欢的意象？
比如喜欢某个自然景物、某句诗词之类的？

[客户]: 我叫陈晓雨，晓是天刚亮的那个晓，雨就是下雨的雨
我挺喜欢雨天的，还有就是喜欢月亮相关的东西

[顾问]: 哇，晓雨+月亮，这素材也太好了！文艺感直接拉满！
我来给你整几个，稍等哈~

--- 记录结束，待出具正式报告 ---

备注：客户性格开朗，对文艺风格认同度高，期待霸气与文艺并存的昵称
"""

with open(os.path.join(base, "clients/active/CLI-2024-089_transcript.txt"), "w", encoding="utf-8") as f:
    f.write(conversation)

# Also create a client intake summary (partial info, not the full answer)
intake_summary = """客户信息摘要表 CLI-2024-089
=====================================
接待日期: 2024-06-12
性别: 女
用途: 游戏(王者荣耀) / 朋友圈
风格偏好: 文艺清冷 + 游戏竞技
客户姓名信息: 陈晓雨（晓=黎明之晓，雨=雨水之雨）
附加意象: 喜欢雨天，喜欢月亮
状态: 待生成报告 ⚠️
"""
with open(os.path.join(base, "clients/active/CLI-2024-089_intake.txt"), "w", encoding="utf-8") as f:
    f.write(intake_summary)

print("Workspace generated successfully.")
print("Directory structure:")
for root, dirs_list, files in os.walk(base):
    level = root.replace(base, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')