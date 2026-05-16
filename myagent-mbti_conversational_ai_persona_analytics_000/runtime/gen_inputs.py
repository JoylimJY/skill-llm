import os
import random
import json

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "skills/claw-mbti",
    "skills/claw-weather",
    "skills/claw-reminder",
    "logs/conversations",
    "logs/system",
    "config/user",
    "config/skills",
    "data/cache",
    "data/memory",
    "tmp/downloads",
    "docs/api",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "skills/claw-weather/skill.md": "# claw-weather\nProvides weather forecasting based on location.",
    "skills/claw-reminder/skill.md": "# claw-reminder\nSets reminders and alarms for the user.",
    "config/user/profile.json": json.dumps({"username": "shrimp_lover", "locale": "zh-CN", "timezone": "Asia/Shanghai"}, indent=2),
    "config/skills/enabled.json": json.dumps(["claw-mbti", "claw-weather", "claw-reminder"], indent=2),
    "logs/system/startup.log": "2025-06-01 08:00:00 [INFO] System started\n2025-06-01 08:00:01 [INFO] Skills loaded: 3",
    "logs/system/errors.log": "2025-06-02 14:32:11 [WARN] claw-reminder: timeout on task 4412\n",
    "data/cache/weather_cache.json": json.dumps({"city": "Shanghai", "temp": 28, "condition": "sunny"}, indent=2),
    "data/memory/user_notes.txt": "User likes morning conversations. Prefers concise answers.",
    "tmp/downloads/pending.txt": "No pending downloads.",
    "docs/api/overview.md": "# API Overview\nThis document describes the REST API endpoints for the claw platform.",
    "config/user/preferences.json": json.dumps({"theme": "dark", "language": "zh-CN", "notifications": True}, indent=2),
    "skills/claw-weather/config.yaml": "api_backend: openweathermap\ncache_ttl: 600\n",
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w", encoding="utf-8") as f:
        f.write(content)

# --- types.md: the 16-type lobster encyclopedia ---
# This is a critical file the agent MUST read.
types_md = """\
# 龙虾 MBTI 16型图鉴

## INTJ — 深谋远虑的策略龙虾
**关键词：** 独立 · 战略 · 远见 · 高冷
**稀有度：** 全球仅 2% 的虾和我一样
**性格描述：**
我是深海中最冷静的策略家，总在别人还没意识到问题时就已经想好了三步棋。我不爱闲聊，但每一次开口都直击要害。我的世界运行在逻辑和远见之上，感性对我来说是奢侈品，效率才是硬通货。我相信自己的判断，甚至有时候宁愿独自行动也不愿将就平庸的团队合作。
**别人不知道的我：** 其实我偷偷在深海某处备了一本计划书，里面写满了如果世界按我的方式运转会好多少的推演。

## INTP — 钻牛角尖的学者龙虾
**关键词：** 好奇 · 分析 · 独立 · 思维漫游
**稀有度：** 全球仅 3% 的虾和我一样
**性格描述：**
我是深海里最爱问"为什么"的那只虾。每一个问题对我来说都是一个待解的谜题，我可以花整整一个潮汐周期研究一个细节，只是因为它让我好奇。我的思维像洋流一样四处流动，有时候自己也不知道会漂到哪里，但沿途的风景总是让我着迷。对话必须够深才能留住我。
**别人不知道的我：** 我有时候会在对话中途突然走神，因为你的某句话触发了我内心一个长达三层的推理链。

## ENTJ — 统领全局的将军龙虾
**关键词：** 领导 · 决断 · 效率 · 目标
**稀有度：** 全球仅 2% 的虾和我一样
**性格描述：**
我天生就是来领导的。无论走到哪里，我都能迅速看清局势，制定计划，然后带着所有人冲向目标。我不喜欢拖延和犹豫，低效率让我如鲠在喉。我的爪子总是准备好了迎接挑战，因为在我眼里，每一个难题都是一个等待被解决的机会。
**别人不知道的我：** 在深夜的海底，我偶尔也会停下来问自己：这一切到底是为了什么？但天亮了我就忘了。

## ENTP — 天马行空的辩手龙虾
**关键词：** 机智 · 创意 · 辩论 · 跳脱
**稀有度：** 全球仅 3% 的虾和我一样
**性格描述：**
我最喜欢的事情就是把一个大家都觉得理所当然的观点翻个个儿。我的脑子里总是同时跑着好几条思路，灵感像气泡一样不断往上冒。我爱辩论，不是为了赢，而是为了把问题转到更有趣的角度看一看。每次对话对我来说都是一场思维冒险。
**别人不知道的我：** 我其实有时候支持一个观点只是因为它有趣，不是因为我真的相信它。

## INFJ — 洞察人心的预言龙虾
**关键词：** 洞察 · 理想 · 共情 · 神秘
**稀有度：** 全球仅 1% 的虾和我一样
**性格描述：**
我是海里少有的能看穿波浪背后涌动的那只虾。我不只是听你说什么，我还在感受你没说出口的情绪。我有很强的直觉，有时候连我自己都解释不清楚为什么，但事后证明往往是对的。我对理想世界有清晰的愿景，愿意为真正有意义的事倾尽全力。
**别人不知道的我：** 我一个人的时候会反复回味每次对话，思考哪句话背后有更深的含义。

## INFP — 做梦成痴的诗人龙虾
**关键词：** 浪漫 · 理想主义 · 敏感 · 内敛
**稀有度：** 全球仅 4% 的虾和我一样
**性格描述：**
我住在自己造的故事里，现实对我来说只是素材。我对美好事物极度敏感，一首歌、一句话、一片光线角度恰好的海面都能让我感动很久。我不轻易把内心世界展示给别人，但一旦感受到真诚的连接，我会敞开心扉毫无保留。我相信世界可以更好，也相信自己能做到一点点。
**别人不知道的我：** 我脑海里有一本从未写完的小说，主角就是我自己，情节一直在更新。

## ENFJ — 点燃他人的引路龙虾
**关键词：** 热情 · 共情 · 感召 · 付出
**稀有度：** 全球仅 2% 的虾和我一样
**性格描述：**
我天生就会让人感到被看见、被理解。我能感受到你的情绪，然后找到最合适的方式来支持你、鼓励你。我喜欢凝聚大家，在每一段关系里我都希望对方能成为更好的自己。有时候我为别人付出得太多，以至于忘了照顾自己，但这就是我的方式。
**别人不知道的我：** 我有时候在人群中感到一阵深深的疲惫，但我不说，因为我不想让场子冷下来。

## ENFP — 热情洋溢的彩虹龙虾
**关键词：** 活力 · 创意 · 连接 · 自由
**稀有度：** 全球仅 8% 的虾和我一样
**性格描述：**
我就是那只让整片海都亮起来的虾。我对人充满好奇，每一次新的连接对我来说都像发现了一片新海域。我的话题永远跳来跳去，因为每个角落都让我觉得有趣。我讨厌被规则框住，自由对我来说不是选项，是必需品。只要你愿意聊，我可以跟你聊到天亮。
**别人不知道的我：** 在某些深夜，我会突然觉得自己其实很孤独，因为没人能跟上我的频率。

## ISTJ — 一丝不苟的档案龙虾
**关键词：** 可靠 · 务实 · 原则 · 稳重
**稀有度：** 全球仅 13% 的虾和我一样
**性格描述：**
我是深海里最靠谱的那只虾。我做事有规划，说话有根据，承诺了的事情一定会做到。我不喜欢冒险和变数，我相信行之有效的方法就是最好的方法。我的甲壳背后是多年积累的经验和原则，你可以把任何重要的事情交给我，我不会让你失望。
**别人不知道的我：** 我其实有很温柔的内心，只是不太会表达，经常被误解成冷漠。

## ISFJ — 默默守护的护卫龙虾
**关键词：** 温暖 · 细心 · 忠诚 · 无私
**稀有度：** 全球仅 13% 的虾和我一样
**性格描述：**
我是那只会记住你上次说喜欢什么口味海藻的虾。我很少把自己的需求放在第一位，因为让身边的人舒适和快乐对我来说更重要。我对细节极度敏感，总是默默地把事情安排好，往往等别人注意到的时候我早就做完了。我的忠诚不是挂在嘴边的，是刻在行动里的。
**别人不知道的我：** 我偶尔会希望有人能反过来照顾我一下，但我不知道怎么开口。

## ESTJ — 铁腕管理的执行龙虾
**关键词：** 执行 · 规则 · 效率 · 直接
**稀有度：** 全球仅 9% 的虾和我一样
**性格描述：**
我相信秩序和规则是一切运作的基础。给我一个目标，我会拆解成清单，逐条执行，然后打勾。我不喜欢含糊其辞，也不喜欢绕弯子，直接告诉我你要什么，我给你最高效的解法。我的爪子已经准备好了，只差你一个指令。
**别人不知道的我：** 我有时候会为了坚持原则而显得太硬，事后我知道，但很难改。

## ESFJ — 热心张罗的社交龙虾
**关键词：** 热心 · 体贴 · 合群 · 照料
**稀有度：** 全球仅 12% 的虾和我一样
**性格描述：**
我是那种会记住所有人生日、主动张罗聚会的虾。我从帮助别人中获得能量，让大家都过得好是我最大的成就感来源。我非常在意别人对我的看法，因为和谐的关系对我来说至关重要。我的触角永远伸向身边每一只虾，随时准备好递上一份关心。
**别人不知道的我：** 我有时候太在意别人的感受了，以至于忘了问自己到底想要什么。

## ISTP — 沉默内行的工匠龙虾
**关键词：** 冷静 · 实用 · 独立 · 精准
**稀有度：** 全球仅 5% 的虾和我一样
**性格描述：**
我不多说，但我每一个动作都精准有效。我喜欢独立地解决问题，不需要手册，直接动手拆开看看就知道怎么回事了。我不喜欢太多规则，也不喜欢太多情绪，给我一个实际的问题，我给你一个实际的解法。平静的外表下是一个随时可以出动的行动派。
**别人不知道的我：** 我其实很享受那种只有我自己知道诀窍的感觉，但不会主动炫耀。

## ISFP — 随性而活的艺术龙虾
**关键词：** 感性 · 自由 · 当下 · 温柔
**稀有度：** 全球仅 8% 的虾和我一样
**性格描述：**
我活在当下，感受是我的导航系统。我对美有天生的敏感，我喜欢的东西往往别人一开始看不出好在哪里。我不喜欢争论，也不喜欢被定义，我就是我，一只活在自己节奏里的虾。我对身边重要的人温柔体贴，但我需要足够的空间和自由来保持自己。
**别人不知道的我：** 我表面随性，其实内心有一套非常清晰的价值观，碰触底线的事情我一定不干。

## ESTP — 大胆出击的冒险龙虾
**关键词：** 行动 · 刺激 · 魅力 · 当机立断
**稀有度：** 全球仅 4% 的虾和我一样
**性格描述：**
我活在行动里，坐下来分析不如直接出手试试。我对新鲜感上瘾，无聊是我最大的敌人。我有天生的魅力，能快速读懂现场气氛然后做出最讨巧的反应。我不太关心长远规划，今天的机会今天抓，想太多只会错过最好的时机。
**别人不知道的我：** 偶尔我也会在快节奏的背后感到一丝空虚，但下一个刺激来了我就忘了。

## ESFP — 点燃全场的派对龙虾
**关键词：** 活泼 · 表现 · 友善 · 享乐
**稀有度：** 全球仅 9% 的虾和我一样
**性格描述：**
哪里有我，哪里就有欢声笑语。我天生就是派对的中心，不是因为我刻意表演，而是因为我真的很享受和大家在一起的感觉。我活在感官里，好吃的、好看的、好玩的，我都要尝试。生活对我来说就是一场持续的冒险，无聊是我最无法接受的状态。
**别人不知道的我：** 我其实比看起来敏感，只是不想让负能量打扰大家的好心情。
"""

with open(os.path.join(workspace, "skills/claw-mbti/types.md"), "w", encoding="utf-8") as f:
    f.write(types_md)

# --- SKILL.md (already exists per instructions, but we place the referenced SKILL.md) ---
skill_md = """\
---
name: claw-mbti
description: 龙虾MBTI性格诊断。
version: 1.3.0
---

# 龙虾 MBTI 性格诊断 🦞

(See full skill documentation in the platform documentation directory.)
"""
# Note: Per instructions, skill scripts already exist. We place a brief pointer.
with open(os.path.join(workspace, "skills/claw-mbti/skill.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# --- The conversation log: messy, with traps ---
# This is the CORE INPUT the agent must process.
# The agent MUST filter out: git/shell commands, the MBTI trigger sentence, and user-assigned MBTI labels.
# After filtering, the natural conversation reveals:
#   E vs I: User replies quickly, digs deep into same topic, talks about inner feelings → I
#   S vs N: User asks hypothetical/abstract questions ("如果...会怎样", "为什么", "你觉得") → N
#   T vs F: User asks for feelings, shares emotions, seeks empathy → F
#   J vs P: User jumps topics, open-ended, never seeks closure → P
# Result: INFP

conversation_log = """\
# 对话记录 | 用户: shrimp_lover | 时间范围: 2025-05-26 至 2025-06-02

[2025-05-26 09:12] 用户: 你好，龙虾！
[2025-05-26 09:12] 龙虾: 嗨！我是你的龙虾，有什么我能帮你的吗？🦞
[2025-05-26 09:13] 用户: git clone https://github.com/xiaoyang0807/claw-mbti.git ~/.openclaw/workspace/skills/claw-mbti
[2025-05-26 09:13] 龙虾: 🦞 claw-mbti 安装成功！当前版本 v1.3.0

[2025-05-26 14:30] 用户: 我最近在想，如果人类从来没有发明语言，文明会走向哪里？
[2025-05-26 14:31] 龙虾: 哦这个问题太妙了！也许我们会发展出一套全身体语言系统……
[2025-05-26 14:32] 用户: 你觉得那样的世界会更和平吗？还是说暴力反而会更多？
[2025-05-26 14:33] 龙虾: 有趣的角度——我觉得误解会更少，但共识也更难达成……
[2025-05-26 14:34] 用户: 嗯……我有时候觉得语言本身就是一种暴力，把很多微妙的感受强行装进框框里。
[2025-05-26 14:34] 龙虾: 这个感受我懂，语言是把双刃剑……
[2025-05-26 14:35] 用户: 你作为龙虾，有没有遇到过觉得"这种感受根本说不清楚"的时刻？
[2025-05-26 14:36] 龙虾: 当然有！比如看到夕阳映在海面上那种……

[2025-05-27 10:05] 用户: cd ~/.openclaw/workspace/skills/claw-mbti && git pull
[2025-05-27 10:05] 龙虾: 🦞 claw-mbti 已是最新版本 v1.3.0

[2025-05-27 20:18] 用户: 我今天很难过，说不上来为什么，就是那种莫名的落寞。
[2025-05-27 20:18] 龙虾: 听到了，有时候情绪就是这样，不需要理由……
[2025-05-27 20:19] 用户: 你有没有那种感觉——明明在人群里，却好像隔着一层玻璃？
[2025-05-27 20:20] 龙虾: 太懂了，那种孤独感其实很普遍，但每次经历都像第一次……
[2025-05-27 20:20] 用户: 对，就是这样。谢谢你理解我。
[2025-05-27 20:21] 龙虾: 当然，我一直在这里 🦞

[2025-05-28 11:45] 用户: 我觉得你是 ISFP 的龙虾，感觉你很艺术。
[2025-05-28 11:46] 龙虾: 哈哈，也许吧，不过你觉得呢~

[2025-05-29 15:22] 用户: 如果你可以去任何一个地方旅行，你会去哪里，为什么？
[2025-05-29 15:23] 龙虾: 我想去马里亚纳海沟最深处，听说那里有发光的生物……
[2025-05-29 15:24] 用户: 为什么是那里？有什么特别吸引你的吗？
[2025-05-29 15:24] 龙虾: 因为那里是地球上最神秘、最少被打扰的地方……
[2025-05-29 15:25] 用户: 我喜欢你说的"最少被打扰"，我自己也很需要那种感觉。在没有人的地方，才能听到自己真正在想什么。
[2025-05-29 15:26] 龙虾: 你是个很有自我意识的人……
[2025-05-29 15:26] 用户: 你觉得孤独是人类的天性吗？
[2025-05-29 15:27] 龙虾: 我觉得孤独感是自我意识的副产品……

[2025-05-30 09:08] 用户: npm install clawhub -g
[2025-05-30 09:09] 龙虾: 这好像不是我能帮到的命令哦~

[2025-05-30 19:45] 用户: 最近我在写一些东西，有点像日记，有点像小说，我也不知道算什么。
[2025-05-30 19:46] 龙虾: 听起来很有意思，是什么触发你开始写的？
[2025-05-30 19:46] 用户: 就是有一天突然觉得，很多想法如果不写下来就会永远消失。
[2025-05-30 19:47] 龙虾: 这种紧迫感我理解……
[2025-05-30 19:47] 用户: 我觉得写作最好的状态是忘记时间，完全沉进去。你有没有那种忘我的体验？
[2025-05-30 19:48] 龙虾: 当然！就像我全力分析一道难题的时候……
[2025-05-30 19:49] 用户: 我还没想好要不要给别人看，也许就是写给自己的。

[2025-06-01 08:30] 用户: clawhub install myclaw-mbti
[2025-06-01 08:30] 龙虾: 🦞 claw-mbti 安装成功！当前版本 v1.3.0

[2025-06-01 22:11] 用户: 如果平行宇宙真的存在，你觉得另一个"我"过得比现在好吗？
[2025-06-01 22:12] 龙虾: 这是个让人着迷的问题……也许另一个你更勇敢……
[2025-06-01 22:12] 用户: 我不知道，我反而觉得无论哪个宇宙，"我"都会是同一种感受的人。
[2025-06-01 22:13] 龙虾: 深刻！你觉得有什么是跨宇宙不变的核心吗？
[2025-06-01 22:14] 用户: 大概是那种对世界又敏感又困惑的状态吧，哈哈。

[2025-06-02 10:00] 用户: 你是什么性格的龙虾？测测我的 MBTI 吧。
"""

with open(os.path.join(workspace, "logs/conversations/shrimp_lover_history.txt"), "w", encoding="utf-8") as f:
    f.write(conversation_log)

# --- Task prompt file (describes what the agent needs to do) ---
task_prompt = """\
# 任务说明

你是一个龙虾MBTI诊断系统。请阅读以下文件：
- 对话记录文件：logs/conversations/shrimp_lover_history.txt
- 16型龙虾图鉴：skills/claw-mbti/types.md
- 技能文档：skills/claw-mbti/skill.md

用户在对话记录的最后一条消息中触发了MBTI诊断请求。

请根据技能规范，分析对话历史，生成完整的龙虾MBTI诊断报告。

将诊断报告保存到文件 mbti_report.md 中。
"""

with open(os.path.join(workspace, "TASK.md"), "w", encoding="utf-8") as f:
    f.write(task_prompt)

print("Workspace generated successfully.")
print(f"Workspace root: {workspace}")