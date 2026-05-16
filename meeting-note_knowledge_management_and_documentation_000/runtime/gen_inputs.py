#!/usr/bin/env python3
import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = "/workspace"

# ─── Directory structure ────────────────────────────────────────────────────
dirs = [
    "01_日记",
    "02_项目/KYC模块",
    "02_项目/支付网关",
    "02_项目/用户增长",
    "03_索引",
    "04_资源/竞品分析",
    "04_资源/法规文件",
    "05_会议纪要/2024-Q1",
    "05_会议纪要/2024-Q2",
    "references",
    "templates",
    "archive/2023",
]
for d in dirs:
    Path(os.path.join(WORKSPACE, d)).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ────────────────────────────────────────────────────────
distractors = {
    "01_日记/2025-06-01.md": "今天读了 GDPR 的新解释文件，合规成本比预期高。",
    "01_日记/2025-06-03.md": "和陈工讨论了数据库迁移的问题，决定推迟到 Q3。",
    "02_项目/KYC模块/需求草稿_v0.2.md": "# KYC 需求草稿\n\n- 身份验证\n- 地址证明\n- 风险评级\n\n> 草稿状态，未经审阅",
    "02_项目/KYC模块/技术选型备忘.md": "候选方案：\n1. Jumio\n2. Onfido\n3. 自研\n\n成本估算待 TBD。",
    "02_项目/支付网关/接口规范v1.3.md": "## API 规范\n\n- POST /payment/initiate\n- GET /payment/status/{id}",
    "02_项目/用户增长/增长实验记录.md": "A/B 测试结果：注册流程简化后转化率+12%。",
    "03_索引/项目总索引.md": "# 项目总索引\n\n- [[KYC模块]]\n- [[支付网关]]\n- [[用户增长]]",
    "04_资源/竞品分析/竞品KYC对比表.md": "| 公司 | 方案 | 成本/年 |\n|------|------|--------|\n| A银行 | Jumio | ¥80万 |\n| B钱包 | 自研 | ¥200万 |",
    "04_资源/法规文件/GDPR摘要.md": "个人数据处理需满足：合法性、透明度、数据最小化原则。",
    "04_资源/法规文件/反洗钱法要点.md": "金融机构须对高风险客户实施增强尽职调查（EDD）。",
    "05_会议纪要/2024-Q1/20240315-产品规划会.md": "# 2024Q1 产品规划会\n\n决定优先上线支付网关 v2.0，KYC 延后至 Q3。",
    "05_会议纪要/2024-Q2/20240601-技术架构评审.md": "# 架构评审\n\n确认微服务拆分方案，用户服务独立部署。",
    "archive/2023/2023年度复盘.md": "2023 年主要里程碑：完成 PCI-DSS 认证，支付模块上线。",
    "templates/weekly_report_template.md": "# 周报模板\n\n## 本周完成\n## 下周计划\n## 风险",
    "references/deep_learning_skill.md": "# deep-learning skill (stub)\n信息/学习型谈话使用此 skill。",
}

for path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ─── The meeting template reference (agents need SKILL.md to know how to use it)
meeting_note_template = """# 会议纪要模板（meeting_note_output_template）

[唯一标识符]
[基本信息]
[主要议题概览]
[逐议题展开]
[关键洞察（原子化）]
[行动计划]
[待跟进事项]
[会议知识网络连接]
[会议智慧沉淀]
[专家圆桌（L3 必做）]
"""
with open(os.path.join(WORKSPACE, "references/meeting_note_output_template.md"), "w", encoding="utf-8") as f:
    f.write(meeting_note_template)

# ─── RAW MESSY MEETING TRANSCRIPT ───────────────────────────────────────────
transcript = """
=== 原始会议记录（未整理）===
日期：2025年6月5日
参会：赵磊（CTO）、林晓薇（产品负责人）、陈国强（合规官）、方怡（工程师，列席）
主持：赵磊
主题：KYC功能建设方式决策

[音频转录，部分内容被噪音遮挡，标注为[unclear]]

赵磊：好，今天主要是定下来KYC这块我们到底是自研还是买现成的服务。大家直接说吧，别绕弯子。

林晓薇：我这边的判断是外采，理由很简单——Jumio和Onfido都有成熟的SDK，接入周期2-3周，我们不用在这上面堆资源。现在增长压力很大，我不想工程团队的精力被合规基础设施给占了。

陈国强：我有不同意见。外采方案数据出境的问题怎么解决？我们用户的身份证信息、活体照片，这些都是个人敏感数据，传到境外服务器，不管是Jumio还是Onfido，一旦被监管问询，我们怎么回答？今年开始，数据安全法和个人信息保护法的执法明显收紧了。

赵磊：陈总说的这个是真实风险，不是危言耸听。但是林总，你刚才说的开发资源的问题我也认同，咱们现在工程团队本来就在做支付网关的重构，再叠一个自研KYC，我是有点担心的。

林晓薇：那能不能折中？核心的身份核验用国内的服务商——比如[unclear]或者百行征信，数据留在境内，这样合规风险就解决了，同时我们也不用自己造轮子。

陈国强：国内服务商这个方向我支持。但是我要加一个条件：我们需要对接入的服务商做尽职调查，确认他们的数据处理协议符合我们内部的数据治理标准，这个工作不做，我不敢签字。

赵磊：好，这个合理。方怡，你来评估一下国内主流服务商的对接成本和周期，下周给我一个报告。

方怡：好的，我来做。不过我想说一点，不管哪个方案，我们自己的KYC业务逻辑——比如风险评级规则、黑名单对比逻辑——这部分最好是我们自己掌控，不能完全依赖供应商的黑盒，否则以后要调整规则会很被动。

赵磊：方怡这个点很重要。那我们的方向是：底层核验能力外采国内服务商，业务逻辑层自研，数据不出境。这个方向大家有没有反对意见？

林晓薇：方向我认可，但是我想确认一个事：这个决定会不会影响我们Q3上线KYC的计划？

赵磊：这个我现在没法给承诺，得等方怡的评估报告出来。如果国内服务商对接周期比外采国际服务商长，Q3的节点可能要重新商量。

陈国强：我还有一个隐患想说：即便我们用国内服务商，如果服务商自己被监管处罚或者停止服务，我们的KYC能力就中断了，这个依赖风险要在合同里约定SLA和备用方案。

赵磊：对，这个纳入方怡的评估范围。还有，陈总你说的尽职调查，能不能给我一个具体的checklist，让我们采购的时候有依据？

陈国强：可以，我来出一版，两周内给你。

赵磊：好。那今天的结论是：技术方向初步定了，外采国内服务商+自研业务逻辑，数据不出境。Q3的节点待评估结果出来后再确认。方怡的评估报告是关键路径。还有什么要说的吗？

林晓薇：有一点我没说——其实我对"自研业务逻辑"这件事有点担心，我们团队里没有专门做风控建模的人，这块能力是否需要另外招人或者找外部顾问，这个问题今天没有讨论到。

赵磊：这个是个好问题，但是今天时间不够了，放到下次。

林晓薇：好，我会发起一个专项讨论。

赵磊：好，散会。

=== 记录人：方怡（速记，未经审阅）===
"""

transcript_path = os.path.join(WORKSPACE, "raw_kyc_meeting_transcript.txt")
with open(transcript_path, "w", encoding="utf-8") as f:
    f.write(transcript)

print("Workspace initialized successfully.")
print(f"Raw transcript written to: {transcript_path}")