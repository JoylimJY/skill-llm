import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create the scripts directory and the email.sh script
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

email_sh_content = r'''#!/bin/bash
# email-writer: Email writing assistant
# Usage: email.sh <command> [args...]

COMMAND="$1"
shift

case "$COMMAND" in
  business)
    RECIPIENT="$1"
    SUBJECT="$2"
    cat <<EOF
=== 商务邮件模板 ===

Subject: 关于${SUBJECT}的商务合作
To: ${RECIPIENT}

尊敬的${RECIPIENT}，

您好！感谢您抽出时间阅读此邮件。

我方希望就${SUBJECT}与贵方展开深入交流，探讨互利合作的可能性。

期待您的回复，欢迎安排进一步的沟通。

此致
敬礼

[您的姓名]
[职位] | [公司]
[联系方式]
EOF
    ;;

  followup)
    TOPIC="$1"
    cat <<EOF
=== 跟进邮件模板 ===

Subject: 跟进：${TOPIC}

您好，

我想跟进一下关于"${TOPIC}"的事宜。

上次沟通后，我方已完成相关准备工作，期待您的进一步反馈。

如有任何问题，请随时联系我。

最诚挚的问候，
[您的姓名]
EOF
    ;;

  cold)
    COMPANY="$1"
    PURPOSE="$2"
    cat <<EOF
=== 冷启动邮件模板 ===

Subject: [合作机会] 关于${PURPOSE} — 致${COMPANY}团队

您好，

我在了解${COMPANY}的业务时，发现贵公司在相关领域有卓越的表现。

我方专注于${PURPOSE}，希望能与${COMPANY}探讨潜在的合作机会。

如您有兴趣，期待安排15分钟通话了解更多。

期待您的回复！
[您的姓名]
EOF
    ;;

  apology)
    REASON="$1"
    cat <<EOF
=== 道歉邮件模板 ===

Subject: 诚挚道歉：关于${REASON}

尊敬的客户，

首先，我方对${REASON}造成的不便深表歉意。

这完全是我方的责任，我们已采取措施防止类似情况再次发生。

感谢您的理解与支持。

诚挚道歉，
[您的姓名] | [公司]
EOF
    ;;

  reply)
    SUMMARY="$1"
    TONE="formal"
    if [[ "$2" == "--tone" ]]; then
      TONE="$3"
    fi
    if [[ "$TONE" == "friendly" ]]; then
      cat <<EOF
=== 回复邮件模板（友好语气）===

Subject: Re: ${SUMMARY}

嗨，

谢谢你的来信！关于${SUMMARY}，我这边的想法是……

有什么问题随时说，我们保持联系！

祝好，
[您的姓名]
EOF
    else
      cat <<EOF
=== 回复邮件模板（正式语气）===

Subject: Re: ${SUMMARY}

尊敬的，

感谢您的来函。就您提及的"${SUMMARY}"，我方回复如下：

[正式回复内容]

如需进一步沟通，请随时告知。

此致
敬礼
[您的姓名] | [职位]
EOF
    fi
    ;;

  series)
    SCENARIO="$1"
    case "$SCENARIO" in
      销售)
        cat <<EOF
=== 邮件序列：销售场景（4封）===

【第1封 - 初次接触】
Subject: 发现一个可能对您有价值的方案
正文：您好，我是[姓名]，专注于[领域]解决方案……

【第2封 - 价值深化 (3天后)】
Subject: 关于您面临的[痛点]——我们的解决思路
正文：上封邮件介绍了我们的方案，今天我想分享一个具体案例……

【第3封 - 社会证明 (7天后)】
Subject: [客户名]如何用我们的方案提升了30%效率
正文：我们的客户[案例公司]曾面临和您类似的挑战……

【第4封 - 最终跟进 (14天后)】
Subject: 最后一封——是否合适简单聊聊？
正文：我理解您很忙，这是我最后一次跟进。如有兴趣，欢迎回复……
EOF
        ;;
      合作)
        cat <<EOF
=== 邮件序列：合作场景（4封）===

【第1封 - 合作意向】
Subject: [公司名]×[我方公司]——合作共赢的机会
正文：您好，我方希望探讨与贵方的战略合作……

【第2封 - 方案细化 (3天后)】
Subject: 我们为贵方定制的合作框架
正文：基于对贵公司的了解，我们拟定了以下合作方案……

【第3封 - 解答疑虑 (7天后)】
Subject: 关于合作的几个常见问题解答
正文：我方了解贵方可能有一些顾虑，特此说明……

【第4封 - 推动决策 (14天后)】
Subject: 期待推进我们的合作——您方便本周安排通话吗？
正文：我们非常期待与贵方建立合作关系……
EOF
        ;;
      催款)
        cat <<EOF
=== 邮件序列：催款场景（4封）===

【第1封 - 友好提醒】
Subject: 友好提醒：[发票号]款项到期提醒
正文：您好，我们注意到[金额]款项已于[日期]到期……

【第2封 - 正式跟进 (7天后)】
Subject: 重要：[发票号]逾期款项处理
正文：我们再次提醒您关注逾期未付款项……

【第3封 - 最后通知 (14天后)】
Subject: 最终通知：请于[日期]前完成付款
正文：这是我方就此款项的最终友好通知……

【第4封 - 法律声明 (21天后)】
Subject: 正式通知：逾期付款法律程序启动
正文：我方遗憾地通知您，如款项仍未结清，我们将启动相应法律程序……
EOF
        ;;
      招聘)
        cat <<EOF
=== 邮件序列：招聘场景（4封）===

【第1封 - 初次触达】
Subject: 发现您的背景与我们正在寻找的人才高度匹配
正文：您好，我是[公司]的HR[姓名]，在了解您的职业背景后，认为您与我们的[职位]需求高度契合……期待与您进一步沟通。

【第2封 - 价值传递 (3天后)】
Subject: [公司名]——一个值得您了解的机会
正文：我想进一步介绍我们团队的文化和这个职位的发展空间……我们提供[薪资范围]及丰厚的期权激励。

【第3封 - 社会证明 (7天后)】
Subject: 来听听我们团队成员怎么说
正文：我们的工程师[姓名]曾在[上家公司]任职，加入我们后……如您方便，我们可以安排您与团队成员直接交流。

【第4封 - 最终邀约 (14天后)】
Subject: 最后机会——[职位]面试名额即将截止
正文：我们的招聘流程即将结束，非常希望能在截止前与您完成面试……请回复此邮件或直接拨打[电话]。
EOF
        ;;
      *)
        echo "错误：未知场景 '$SCENARIO'。可用场景：销售|合作|催款|招聘"
        exit 1
        ;;
    esac
    ;;

  template)
    TYPE="$1"
    case "$TYPE" in
      感谢)
        cat <<EOF
=== 邮件模板：感谢信 ===

Subject: 衷心感谢您的[帮助/支持/参与]

尊敬的[姓名]，

感谢您在[具体事项]中给予的大力支持，您的付出对我们意义重大。

我们非常珍视与您的合作关系，期待未来有更多合作机会。

再次致谢！

此致
敬礼
[您的姓名]
EOF
        ;;
      通知)
        cat <<EOF
=== 邮件模板：通知邮件 ===

Subject: 【重要通知】[通知主题]

各位好，

特此通知：[具体通知内容]

生效时间：[日期]
影响范围：[相关人员/部门]

如有疑问，请联系[联系人]。

[公司/部门名称]
[日期]
EOF
        ;;
      邀请)
        cat <<EOF
=== 邮件模板：邀请邮件 ===

Subject: 诚挚邀请您参加[活动名称]

尊敬的[姓名]，

我们诚挚地邀请您参加[活动名称]。

活动详情：
- 时间：[日期] [时间]
- 地点：[地址/线上链接]
- 议程：[简要议程]

请于[回复截止日期]前确认出席，以便我们做好安排。

期待您的光临！

诚挚邀请，
[您的姓名] | [职位] | [公司]
EOF
        ;;
      拒绝)
        cat <<EOF
=== 邮件模板：拒绝邮件 ===

Subject: Re: [原邮件主题] — 回复

尊敬的[姓名]，

感谢您的来函及对我方的关注。

经慎重考虑，我方目前暂时无法[接受该提案/参与该项目/满足该需求]，主要原因是[简要说明]。

希望未来有机会合作，祝贵方业务顺利！

此致
敬礼
[您的姓名]
EOF
        ;;
      催款)
        cat <<EOF
=== 邮件模板：催款邮件 ===

Subject: 付款提醒：[发票编号] 金额 [金额]

尊敬的[客户姓名]，

根据我们的记录，以下款项尚未结清：

发票编号：[编号]
金额：[金额]
到期日：[日期]

请于[具体日期]前完成付款。如已付款，请忽略此提醒。

如有疑问，请联系[财务联系人]。

谢谢您的配合！

[公司财务部]
EOF
        ;;
      *)
        echo "错误：未知模板类型 '$TYPE'。可用类型：感谢|通知|邀请|拒绝|催款"
        exit 1
        ;;
    esac
    ;;

  subject)
    CONTENT="$1"
    cat <<EOF
=== 高打开率主题行：${CONTENT} ===

【风格1 - 好奇心驱动】
"你不知道的关于${CONTENT}的3件事"

【风格2 - 数字量化】
"5个关键步骤，让您的${CONTENT}效果提升200%"

【风格3 - 紧迫感】
"仅限本周：${CONTENT}专属方案即将截止"

【风格4 - 个性化痛点】
"还在为${CONTENT}烦恼？这篇邮件专为您准备"

【风格5 - 社会证明】
"1000+客户信赖的${CONTENT}解决方案"
EOF
    ;;

  help)
    cat <<EOF
email-writer 使用帮助
====================
命令列表：
  business "收件人" "主题"          商务邮件模板
  followup "主题"                   跟进邮件模板
  cold "公司" "目的"                冷启动邮件模板
  apology "原因"                    道歉邮件模板
  reply "原文摘要" [--tone formal|friendly]  回复邮件模板
  series "场景(销售|合作|催款|招聘)"         邮件序列（4封自动化）
  template "类型(感谢|通知|邀请|拒绝|催款)" 邮件模板库
  subject "内容描述"                高打开率主题行生成（5种风格）
  help                              显示帮助信息
EOF
    ;;

  *)
    echo "错误：未知命令 '$COMMAND'"
    echo "运行 'email.sh help' 查看使用帮助"
    exit 1
    ;;
esac
'''

with open(scripts_dir / "email.sh", "w", encoding="utf-8") as f:
    f.write(email_sh_content)

# ── Create distractor directory structure ──────────────────────────────────────
dirs = [
    "hr/recruitment/jd",
    "hr/recruitment/pipeline",
    "hr/onboarding",
    "hr/policies",
    "marketing/campaigns/q4",
    "marketing/assets",
    "ops/infra",
    "ops/runbooks",
    "finance/invoices",
    "product/roadmap",
    "product/specs",
    "legal/contracts",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "hr/recruitment/jd/senior_engineer.txt": "职位：高级后端工程师\n要求：5年以上经验，熟悉分布式系统\n薪资：30-50K",
    "hr/recruitment/jd/product_manager.txt": "职位：产品经理\n要求：3年以上产品经验\n薪资：25-40K",
    "hr/recruitment/pipeline/candidates_q4.csv": "name,stage,status\n张三,初面,通过\n李四,技术面,待定\n王五,HR面,通过",
    "hr/recruitment/pipeline/notes.txt": "2024 Q4 招聘目标：后端工程师×3，产品经理×1，数据分析师×2",
    "hr/onboarding/checklist.txt": "入职清单：\n1. 签署保密协议\n2. 领取设备\n3. 系统权限申请\n4. 导师分配",
    "hr/policies/leave_policy.txt": "年假政策：入职满1年享有10天年假，每增加1年增加1天，最多20天。",
    "marketing/campaigns/q4/plan.txt": "Q4营销计划：\n目标：品牌曝光提升50%\n渠道：社交媒体、邮件营销、线下活动",
    "marketing/assets/brand_guidelines.txt": "品牌色：#2B5CE6（主色），#F5A623（辅色）\n字体：思源黑体（中文），Inter（英文）",
    "ops/infra/servers.txt": "生产服务器：prod-01.internal (192.168.1.10)\n测试服务器：test-01.internal (192.168.1.20)",
    "ops/runbooks/incident_response.txt": "P0事故响应流程：\n1. 立即通知on-call\n2. 建立战情室\n3. 15分钟内发出初步通报",
    "finance/invoices/pending.txt": "待收款发票：\nINV-2024-001 客户A 50,000元 2024-11-30到期\nINV-2024-002 客户B 30,000元 2024-12-15到期",
    "product/roadmap/2024_q4.txt": "Q4产品路线图：\n- AI推荐引擎上线\n- 移动端重构\n- API v3发布",
    "product/specs/api_v3.txt": "API v3规范：\nPOST /api/v3/users - 创建用户\nGET /api/v3/users/{id} - 获取用户信息",
    "legal/contracts/nda_template.txt": "保密协议模板：\n本协议由甲方[公司名]与乙方[姓名]签订……",
}

for path, content in distractor_files.items():
    file_path = workspace / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

# Create a misleading "email_drafts" folder with raw unstructured notes 
# (these are NOT the answer, just distractors)
(workspace / "hr/recruitment/email_drafts").mkdir(parents=True, exist_ok=True)
with open(workspace / "hr/recruitment/email_drafts/raw_notes.txt", "w", encoding="utf-8") as f:
    f.write("""招聘邮件草稿备忘（未整理）
================
需要给候选人发一系列跟进邮件，包括：
- 第一封：自我介绍+岗位介绍
- 后续跟进
TODO: 还需要一个面试邀请模板
TODO: 想想邮件标题怎么写更吸引人——针对"高级工程师招聘"这个主题
最终要把所有内容整合到一个文件里给hiring manager看
""")

with open(workspace / "hr/recruitment/email_drafts/subject_ideas.txt", "w", encoding="utf-8") as f:
    f.write("""主题行想法（随手记）
- "加入我们？"
- "职位机会"  
- "期待您的回复"
这些都太普通了，需要更吸引人的风格
""")

print("Workspace created successfully.")
print(f"Files created in: {workspace}")