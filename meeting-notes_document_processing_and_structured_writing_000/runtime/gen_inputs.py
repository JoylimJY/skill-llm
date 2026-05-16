import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create distractor directory structure ---
distractor_dirs = [
    "archive/2024/Q3",
    "archive/2024/Q4",
    "templates/investor_decks",
    "templates/nda_forms",
    "notes/internal",
    "notes/drafts",
    "pipeline/deals/active",
    "pipeline/deals/passed",
    "pipeline/deals/pending",
    "tools/transcription",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "archive/2024/Q3/meeting_notes_smarthome_co.md": "# Meeting Notes - 2024-09-12\n\n## 一、团队背景\n\n**王总**: 创始人之前在哪里工作？\n\n**项目方**: 我们创始人之前在华为消费者BG做了六年产品经理。\n",
    "archive/2024/Q4/deal_tracker.csv": "Project,Stage,Lead,Date\n光能科技,DD,李总,2024-11-03\n海浪出行,Pass,张总,2024-11-17\n",
    "templates/investor_decks/template_v3.md": "# Pitch Deck Template\n\n- Slide 1: Cover\n- Slide 2: Problem\n- Slide 3: Solution\n",
    "templates/nda_forms/nda_standard_cn.txt": "保密协议标准文本 v2.1\n本协议由甲方（投资方）与乙方（项目方）签订...\n",
    "notes/internal/lp_update_dec.md": "## LP Update - December 2024\n\n本季度共看项目47个，进入DD阶段3个。\n",
    "notes/drafts/rough_notes_jan5.txt": "见了三个项目 都不错\n智能家居那个创始人很有想法\n估值有点贵\n",
    "pipeline/deals/active/lightwave_dd.md": "# LightWave DD Checklist\n\n- [ ] 财务审计\n- [ ] 法务尽调\n- [x] 团队背调\n",
    "pipeline/deals/passed/xr_glasses_pass.md": "# XR Glasses - Pass\n\n原因：市场时机过早，硬件成本无法压缩到消费者可接受价位。\n",
    "pipeline/deals/pending/homesense_pending.md": "# HomeSense - Pending\n\n等待创始人更新最新财务数据。\n",
    "tools/transcription/whisper_config.yaml": "model: large-v3\nlanguage: zh\nword_timestamps: true\n",
    "tools/transcription/cleanup_rules.txt": "Rules for post-processing:\n1. Remove [INAUDIBLE] markers\n2. Merge short segments < 0.5s\n3. Normalize speaker labels\n",
}
for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- THE MAIN TASK INPUT: Raw messy transcript ---
# Key adversarial features:
# 1. Two lines are MISLABELED: Speaker_A says something that is clearly project-side (technical explanation), labeled as Speaker_A (investor)
# 2. One investor judgment is labeled as Speaker_B (project side)  
# 3. Greetings to be deleted
# 4. Technical demo section ("能看到吗？") to be deleted
# 5. Investor uses rhetorical/追问 style that must be abstracted
# 6. Founder answers are verbose and must be preserved verbatim (not summarized)
# 7. Themes must follow meeting order (창업동기 comes BEFORE 产品介绍 in the transcript)

transcript = """[会议转写] HomeSense 智能家居 - 投资会
日期: 2025-03-18
时间: 14:00-15:30
参与人: 张敏 (投资人, 明远资本), 陈浩 (投资人, 明远资本), 林一帆 (创始人, HomeSense)

---

[00:00:05] Speaker_A (张敏): 林总你好，终于见面了，之前一直在日历上看到你的名字。
[00:00:09] Speaker_B (林一帆): 哈哈是的是的，新年好新年好，我们终于对上了。
[00:00:15] Speaker_A (张敏): 好，那我们直接开始吧，时间比较紧，我们今天大概有一个半小时。
[00:00:21] Speaker_B (林一帆): 好的好的。

[00:00:28] Speaker_A (张敏): 林总，我们一般喜欢先问一个问题，就是你现在手里同时有几个选择，你是把全部时间放在HomeSense上，还是说你还有别的事情在跑？
[00:00:41] Speaker_B (林一帆): 我是全职在做这个的，从2023年9月开始就全职了。在这之前我在涂鸦智能做了差不多四年的产品，做的是to B这边的智能家居协议层，主要是Matter协议的落地和生态接入这块。然后我觉得to B那边整个节奏太慢了，而且我看到一个机会就是Matter出来之后，其实家庭里面设备互联的门槛在降低，但是真正用起来还是很麻烦，普通用户根本搞不定，所以我就想自己来做一个真正面向普通家庭的产品。

[00:01:35] Speaker_A (张敏): 好，那你做这个的契机是什么，是你自己家里遇到了什么问题，还是说你在涂鸦看到了什么数据？
[00:01:44] Speaker_B (林一帆): 两个都有。我自己家里装了一套小米的设备，大概三十几个，然后我妈来住了一段时间，她完全用不了，每次都得让我帮她开灯。这让我很触动，因为我自己做了这么多年智能家居，结果家里的智能家居我妈用不了，那这个行业是不是有点问题。另外在涂鸦的时候我们有一些数据，大概有70%的智能家居设备在购买后三个月内使用频率会降到每周不到一次，用户其实放弃了这些设备，觉得太麻烦。所以我就觉得这个问题是真实存在的，不是我一个人的问题。

[00:02:58] Speaker_A (张敏): 明白了。那我想问问团队，你现在几个人，分别是什么背景？
[00:03:06] Speaker_B (林一帆): 现在全职六个人。我自己是产品，还有一个联创叫赵文杰，他是做硬件出身的，之前在小米生态链做过两款产品，一个智能插座一个空气净化器，都做到了比较大的销量，他负责硬件这块。然后我们有两个软件，一个做APP，一个做云端和AI这块。还有一个工业设计，之前在洛可可待过，还有一个做供应链的，之前在富士康做过采购。

[00:03:55] Speaker_A (张敏): 赵文杰之前那两款产品，是他主导做的还是说他只是参与？
[00:04:02] Speaker_B (林一帆): 智能插座那款他是硬件负责人，从立项到量产他都在，做到了大概月销三万件的量级。空气净化器那款他参与了早期，后来因为项目组整合他调到了别的组，所以只做了前半段。

[00:04:28] Speaker_C (陈浩): 我想问一下你们的产品是什么形态，你们到底在卖什么？

[00:04:35] Speaker_B (林一帆): 我先把我们的demo给大家看一下，大家能看到我的屏幕吗？
[00:04:41] Speaker_A (张敏): 能看到能看到。
[00:04:43] Speaker_B (林一帆): 好，这个是我们的APP，这里是主界面，可以看到所有的设备，然后这里是场景，我们叫"时刻"，每个时刻可以设置触发条件，可以是时间、位置、或者设备状态。这里这个是……
[00:05:10] Speaker_A (张敏): Ok，我大概看到了，你能不能不用演示，直接说？
[00:05:15] Speaker_B (林一帆): 好的好的。

[00:05:18] Speaker_B (林一帆): 我们核心产品是一个叫"家庭中枢"的硬件设备，就是一个小盒子，大概手机大小，放在家里，它做三件事：第一，它是所有智能设备的本地网关，不需要依赖云端就能控制家里所有设备，哪怕断网了也能用；第二，它上面有一个AI助手，我们叫"家管"，它学习家里每个人的习惯，主动帮你设置场景，不需要用户去配置；第三，它有一个很重要的功能，就是"成员识别"，通过蓝牙和WiFi指纹，它能知道家里现在是谁在，然后根据不同的人自动切换场景，比如老人模式、儿童模式。

[00:06:22] Speaker_C (陈浩): 这个本地网关的技术壁垒在哪里，你们这个协议兼容性是怎么做的？我的意思是，小米、华为都在做这个事情，你们凭什么？

[00:06:35] Speaker_B (林一帆): 我们现在支持Matter 1.2、Zigbee 3.0、Z-Wave，以及主流品牌的私有协议，海尔、美的、小米这几个我们已经打通了。壁垒主要在两块，一是我们做了一个叫"协议翻译层"的东西，可以让不同生态的设备互相触发，这个是小米和华为目前做不到的，因为他们都想把设备锁在自己生态里。二是我们的AI是跑在本地的，不依赖云端推理，这在隐私和响应速度上有优势，我们用的是一个3B参数的剪枝模型，推理延迟在200毫秒以内。

[00:07:45] Speaker_C (陈浩): 这个方向上苹果的HomeKit、谷歌的Home都失败过，你认为你们能走通的核心原因是什么？我不是要打击你，我是真的想知道你们凭什么能做到他们没做到的。
[00:08:01] Speaker_B (林一帆): 我觉得他们失败的核心原因不一样。苹果HomeKit失败是因为生态封闭，要求太严格，很多设备厂商不愿意接入认证流程，结果用户想用但是设备不够。谷歌Home失败是因为他们一直在做云端，但是家庭场景里网络不稳定是常态，云端依赖导致体验很差，而且谷歌三次砍掉了这个产品线，战略上就不坚定。我们的路径不一样，我们是先做本地，先保证基础体验稳定，然后再叠AI能力。而且我们针对的是中国家庭，中国的设备品牌生态和美国是不一样的，涂鸦、海尔、美的这些在国内的覆盖率很高，我在这个行业做了四年，这些品牌的对接我很熟悉。

[00:09:10] Speaker_A (张敏): 你们现在的商业模式是什么，是卖硬件还是收订阅？
[00:09:17] Speaker_B (林一帆): 现在主要是卖硬件，我们的"家庭中枢"定价是899元，硬件毛利大概在35%到40%之间，这个毛利率其实在智能家居硬件里算不错的了，因为我们有一些元器件是自己设计的，不是完全用公模。然后后续我们计划推一个订阅服务，叫"家管Pro"，月费大概29元，包含云端备份、多地控制、家庭成员行为分析报告，这些是需要云端的功能。目前的重心还是在硬件上，先把规模做起来。

[00:10:05] Speaker_C (陈浩): 你们现在有多少用户，复购率怎么样，有没有用户愿意为订阅付费的数据？
[00:10:14] Speaker_B (林一帆): 我们现在有大概4200个付费用户，主要是通过小红书和垂直论坛，比如V2EX这些地方来的，这些用户非常活跃，我们在V2EX上的帖子最高有过三千多个回复，用户会自发分享接入新设备的教程。复购我们定义成第二次购买附件，就是买了中枢之后又买传感器或者附加设备，复购率是61%。订阅那边我们还没正式推，但是我们做了一个早鸟测试，在4200个用户里面发了邀请，有大概380个用户愿意先付一年的早鸟价，早鸟价是199元一年，相当于验证了一下付费意愿。

[00:11:28] Speaker_A (张敏): 你们这一轮融多少，估值怎么算的？
[00:11:34] Speaker_B (林一帆): 我们这一轮想融500万美金，融完做到Pre-A。估值我们给的是2500万美金，这个是参考了我们的ARR预期，我们预期今年年底能到300万人民币的订阅ARR，加上硬件这边今年的目标是10000台，按照899的单价，差不多是900万人民币的硬件收入。然后行业对标，类似的智能家居平台公司，海外的SmartThings当时被三星收购的估值大概是2亿美金，国内的涂鸦上市的时候峰值市值也有20多亿美金，我们这个阶段2500万美金我觉得还是比较合理的。

[00:12:45] Speaker_C (陈浩): 2500万美金对于一个4200用户的早期项目，这个估值我是有保留的。你们现在的核心价值是创始人的行业经验和技术积累，但是商业验证还很早期，这个估值有点超前。

[00:13:05] Speaker_A (张敏): 我同意陈总说的，现阶段最重要的是把用户规模做上去，估值的事可以谈，但是你们得先证明用户量可以从4000增长到40000，这个路径你们想清楚了吗？
[00:13:20] Speaker_B (林一帆): 我们想清楚了，核心路径有两个，一个是内容，我们在小红书的账号现在有1.2万粉丝，我们计划把这个做到10万，通过UGC带动自然增长；另一个是渠道，我们在和京东智能家居的采购在谈，如果进了京东自营，单月有机会出货到1500台以上。另外我们也在看一个叫"全屋托管"的服务模式，就是像装修公司一样，帮用户把整套设备买好、装好、调好，收服务费，这个客单价可以到5000到8000元，利润率更高，我们现在在上海有3个试点用户。

[00:14:30] Speaker_C (陈浩): 全屋托管这个方向我觉得反而是有意思的，这个不是产品公司的逻辑，但是在中国的装修链条里可能是一个很好的渠道切入口，你们有没有想过把这个单独拎出来做？
[00:14:47] Speaker_B (林一帆): 我们内部也讨论过，但是目前的结论是先作为一个获客渠道，不作为核心业务。因为这个太重了，需要本地团队，客单价高但是规模化很难，我们还是想做平台，不想做服务公司。

[00:15:20] Speaker_A (张敏): 好，那我最后问一个问题，你们接下来六个月的里程碑是什么，用钱主要花在哪里？
[00:15:29] Speaker_B (林一帆): 六个月的里程碑是三个：第一，用户量从4200增长到15000；第二，完成京东自营的上架；第三，把"家管Pro"订阅正式上线，目标是500个付费订阅用户。用钱的话，大概是这样：40%用于市场和内容，主要是小红书投流和KOL合作；30%用于研发，主要是AI模型的迭代和APP功能；20%用于供应链，要提前备货；剩下10%是运营和其他。

[00:16:28] Speaker_C (陈浩): 好，我们今天就先聊到这里，我们回去会讨论一下，如果有兴趣的话本周内会给你们一个反馈。
[00:16:37] Speaker_B (林一帆): 好的，谢谢张总、陈总，期待后续。
[00:16:41] Speaker_A (张敏): 好，再见。
"""

transcript_path = os.path.join(workspace, "homesense_transcript_20250318.txt")
with open(transcript_path, "w", encoding="utf-8") as f:
    f.write(transcript)

# --- Additional distractor: an OLD, incorrectly formatted meeting notes example (wrong style) ---
bad_example = """# Meeting Notes - 2024-08-21

## 概要
本次会议主要围绕XX科技的商业模式展开讨论，投资方对团队背景表示认可，对估值有一定保留。

## 投资方关注点
- 投资方王总关注了团队稳定性问题，试图厘清核心成员的股权结构。
- 陈总对产品差异化进行了深入追问，重点考察了竞争壁垒。

## 项目方回应
项目方表示团队结构稳定，核心成员均已签署股权协议，竞争壁垒主要来自技术积累。
"""
with open(os.path.join(workspace, "archive/2024/Q3/bad_format_example.md"), "w", encoding="utf-8") as f:
    f.write(bad_example)

# --- SKILL.md ---
skill_md = open("/dev/stdin").read() if False else ""

print("Workspace initialized successfully.")
print(f"Main transcript: {transcript_path}")
print(f"Total distractor files: {len(distractor_files) + 1}")