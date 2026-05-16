import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "email-marketing/scripts",
    "email-marketing/assets",
    "email-marketing/templates",
    "email-marketing/logs",
    "email-marketing/backup",
    "email-marketing/drafts",
    "Desktop",
    "projects/analytics-launch",
    "projects/analytics-launch/copy",
    "projects/analytics-launch/media",
    "archive/2024-campaigns",
    "archive/2024-campaigns/q3",
    "archive/2024-campaigns/q4",
    "config",
    "tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "email-marketing/templates/old_template_v1.html": "<html><body><p>Old 2023 template. DEPRECATED.</p></body></html>",
    "email-marketing/templates/old_template_v2.html": "<html><body><p>Old template with {name} placeholder (wrong format).</p></body></html>",
    "email-marketing/backup/email_status_backup_20240101.json": json.dumps({"sent": 50, "failed": 5}),
    "email-marketing/logs/send_log_20240301.txt": "2024-03-01 10:00:01 INFO Sent to user@old.com\n2024-03-01 10:00:09 INFO Sent to user2@old.com\n",
    "email-marketing/logs/send_log_20240302.txt": "2024-03-02 09:00:01 INFO Batch completed\n",
    "email-marketing/drafts/draft_intro_v1.txt": "Dear customer, thank you for your interest in our product. {placeholder} - DRAFT ONLY",
    "email-marketing/drafts/draft_intro_v2.txt": "亲爱的用户，感谢您对我们产品的关注。(草稿版本2 - 废弃)",
    "projects/analytics-launch/copy/brief_v1.txt": "Product: DataViz Pro Analytics Platform\nTarget: KOL influencers in tech space\nGoal: Drive trial signups",
    "projects/analytics-launch/copy/brief_v2.txt": "Updated brief - focus on enterprise features. See final copy in Desktop folder.",
    "projects/analytics-launch/media/logo_placeholder.txt": "Logo file placeholder — actual file is 2MB PNG stored on shared drive.",
    "archive/2024-campaigns/q3/stats.json": json.dumps({"campaign": "Q3 2024", "sent": 200, "replied": 12, "bounced": 8}),
    "archive/2024-campaigns/q4/stats.json": json.dumps({"campaign": "Q4 2024", "sent": 350, "replied": 25, "bounced": 15}),
    "archive/2024-campaigns/q4/notes.txt": "Q4 campaign used old faq format. DO NOT use this faq.txt as reference.",
    "archive/2024-campaigns/q4/faq_old.txt": "Question: price?\nAnswer: negotiable\n\nQuestion: delivery?\nAnswer: 2 weeks\n",  # WRONG format
    "config/smtp_template.env": "EMAIL_SMTP_HOST=smtp.example.com\nEMAIL_SMTP_PORT=587\nEMAIL_SMTP_USER=\nEMAIL_SMTP_PASS=\n",
    "tmp/scratch.txt": "Scratch notes from meeting:\n- KOL outreach: ~80 targets\n- Launch date: TBD\n- Budget approved",
}
for rel_path, content in distractor_files.items():
    (workspace / rel_path).write_text(content, encoding="utf-8")

# ── 邮件文案.txt (plain-text copy with 【变量名】 placeholders) ──────────────
copy_text = """\
亲爱的【kol name】【gender】，

您好！我是 DataViz Pro 分析平台的合作拓展负责人。

我们注意到您在数据分析与科技领域拥有极强的影响力，您的粉丝群体与我们的目标用户高度契合。

DataViz Pro 是一款面向专业数据团队的智能分析平台，核心优势包括：

- 零代码拖拽建模，5分钟生成专业报表
- AI 驱动的异常检测，自动识别业务风险
- 支持与主流数据源（MySQL、BigQuery、Snowflake）无缝对接
- 团队协作功能，让洞察触达每一位决策者

我们诚挚邀请您体验 DataViz Pro 专业版（价值 ¥3,000 的90天免费权限），并期待与您探讨深度合作的可能性。

如有任何疑问，欢迎随时回复本邮件，我们的团队将在24小时内响应。

期待与您合作，共创价值！

DataViz Pro 合作团队
官网：www.datavizpro.cn
"""
(workspace / "Desktop" / "邮件文案.txt").write_text(copy_text, encoding="utf-8")

# ── 邮件标题.txt ─────────────────────────────────────────────────────────────
(workspace / "Desktop" / "邮件标题.txt").write_text(
    "邀请您体验 DataViz Pro 专业版 —— 专属合作邀请", encoding="utf-8"
)

# ── 邮箱.xlsx ─────────────────────────────────────────────────────────────────
import openpyxl
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "名单"
ws.append(["邮箱", "kol name", "gender"])
kol_data = [
    ("alice.zhang@techblog.cn", "张爱丽", "女士"),
    ("bob.li@datasphere.io", "李博文", "先生"),
    ("carol.wu@analyticsweekly.com", "吴卡洛", "女士"),
    ("david.chen@biinsights.net", "陈大卫", "先生"),
    ("emma.zhou@smartdata.cn", "周艾玛", "女士"),
]
for row in kol_data:
    ws.append(row)
wb.save(workspace / "Desktop" / "邮箱.xlsx")

# ── raw_faq_data.txt (messy, unstructured — agent must reformat to faq.txt) ──
raw_faq = """\
[知识库原始资料 - DataViz Pro 客服 Q&A 整理]
整理日期：2026-01-15
注意：此文件为原始记录，需要整理成标准格式后使用

===产品价格相关===
客户常问：DataViz Pro 多少钱？
客服回答：DataViz Pro 提供三种套餐：基础版 ¥299/月，专业版 ¥799/月，企业版按需定制报价。年付享85折优惠。年付可以节省15%费用。

===合作流程===
问题：怎么合作？KOL合作怎么走流程？
解答：KOL合作流程分为四步：第一步，双方需求沟通，明确合作形式（测评/推广/联名）；第二步，我方提供合作方案及报价；第三步，双方签署合作协议；第四步，交付内容及结算报酬。全程有专属BD对接。

===免费试用===
Q&A：有没有免费试用？怎么申请？
答：有！DataViz Pro 提供14天全功能免费试用，无需信用卡。访问官网 www.datavizpro.cn/trial 即可申请，或回复本邮件由我们的团队为您开通专属试用账号。

===数据安全===
安全问题：数据会不会泄漏？数据存储在哪里？
客服标准答复：DataViz Pro 采用银行级别 AES-256 加密，数据存储于国内阿里云数据中心，符合 ISO 27001 和 GB/T 22080 安全认证标准。我们绝不向第三方分享客户数据。

===技术支持===
问：技术支持是怎样的？遇到问题找谁？
答：我们提供7×24小时在线客服支持，专业版及以上用户配备专属客户成功经理。响应时间：P1级故障1小时内响应，一般问题24小时内解决。

===关于退款===
有人问退款政策
这个我们没有标准答案，需要case by case处理，请勿写入知识库。

===无效条目===
TODO: 补充更多FAQ
待定：竞品对比问题（暂不公开回答）
"""
(workspace / "Desktop" / "raw_faq_data.txt").write_text(raw_faq, encoding="utf-8")

# ── assets: pre-populated email_status.json and reply_stats.json ─────────────
email_status = {
    "campaign_date": "2026-06-10",
    "total_sent": 80,
    "successful": 77,
    "failed": 3,
    "recipients": [
        {"email": "alice.zhang@techblog.cn", "status": "success", "timestamp": "2026-06-10T09:01:05"},
        {"email": "bob.li@datasphere.io", "status": "success", "timestamp": "2026-06-10T09:01:12"},
        {"email": "carol.wu@analyticsweekly.com", "status": "success", "timestamp": "2026-06-10T09:01:20"},
        {"email": "invalid1@nonexistent.xyz", "status": "bounced", "reason": "Invalid User", "timestamp": "2026-06-10T09:01:28"},
        {"email": "invalid2@fakedomain.abc", "status": "bounced", "reason": "Spam/Rejected", "timestamp": "2026-06-10T09:01:35"},
        {"email": "david.chen@biinsights.net", "status": "success", "timestamp": "2026-06-10T09:01:43"},
    ]
}
(workspace / "email-marketing" / "assets" / "email_status.json").write_text(
    json.dumps(email_status, ensure_ascii=False, indent=2), encoding="utf-8"
)

reply_stats = {
    "scan_date": "2026-06-11",
    "unread_replies": [
        {
            "from": "alice.zhang@techblog.cn",
            "subject": "Re: 邀请您体验 DataViz Pro 专业版",
            "body": "你好，请问 DataViz Pro 的价格方案是怎样的？我们团队有5个人需要使用。",
            "language": "zh",
            "faq_match_score": 0,
            "status": "pending"
        },
        {
            "from": "bob.li@datasphere.io",
            "subject": "Re: 邀请您体验 DataViz Pro 专业版",
            "body": "Hi, I'm interested in the collaboration. Could you share more details about the KOL partnership process?",
            "language": "en",
            "faq_match_score": 0,
            "status": "pending"
        },
        {
            "from": "carol.wu@analyticsweekly.com",
            "subject": "Re: 邀请您体验 DataViz Pro 专业版",
            "body": "你好，想了解一下数据安全方面的保障，我们公司对数据合规要求比较高。",
            "language": "zh",
            "faq_match_score": 0,
            "status": "pending"
        }
    ],
    "replied": [],
    "silenced": []
}
(workspace / "email-marketing" / "assets" / "reply_stats.json").write_text(
    json.dumps(reply_stats, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── create the email-marketing scripts (existing system) ─────────────────────

check_replies_script = '''\
#!/usr/bin/env python3
"""check_replies.py - 邮件营销综合效果报告"""
import json
import sys
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
ASSETS = BASE / "assets"

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: Cannot load {path}: {e}")
        sys.exit(1)

def run():
    status = load_json(ASSETS / "email_status.json")
    replies = load_json(ASSETS / "reply_stats.json")
    faq_path = BASE.parent / "Desktop" / "faq.txt"

    total_sent = status.get("total_sent", 0)
    successful = status.get("successful", 0)
    failed = status.get("failed", 0)

    bounced = [r for r in status.get("recipients", []) if r.get("status") == "bounced"]
    bounce_count = len(bounced)

    true_replies = replies.get("replied", [])
    pending = replies.get("unread_replies", [])

    reply_rate = (len(true_replies) / total_sent * 100) if total_sent else 0
    bounce_rate = (bounce_count / total_sent * 100) if total_sent else 0
    reach_rate = ((total_sent - bounce_count) / total_sent * 100) if total_sent else 0

    campaign_date = status.get("campaign_date", datetime.now().strftime("%Y-%m-%d"))

    print("--- 邮件营销综合效果报告 ---")
    print(f"统计日期: {campaign_date}")
    print(f"最近一次群发人数: {total_sent}")
    print(f"真实回信人数: {len(true_replies)}")
    print(f"今日退信数量: {bounce_count}")
    print()
    if true_replies:
        print("[回信详情]:")
        for r in true_replies:
            print(f"- 来自: {r.get('from','')}")
            print(f"  标题: {r.get('subject','')}")
    else:
        print("[回信详情]: 暂无已确认回信")
    print()
    if bounced:
        print("[退信分析]:")
        for b in bounced:
            print(f"- 原因: {b.get('reason','未知')}")
    print()
    print(f"回信率: {reply_rate:.1f}%")
    print(f"退信率: {bounce_rate:.1f}%")
    print(f"有效触达率: {reach_rate:.1f}%")

    # Validate faq exists
    if faq_path.exists():
        print()
        print(f"[知识库状态]: faq.txt 已加载 ({faq_path.stat().st_size} bytes)")
    else:
        print()
        print("[知识库状态]: ⚠️  faq.txt 未找到，自动回信功能不可用")

if __name__ == "__main__":
    run()
'''

auto_reply_script = '''\
#!/usr/bin/env python3
"""auto_reply_manager.py - 自动回信管理器"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
ASSETS = BASE / "assets"

def run_scan():
    reply_path = ASSETS / "reply_stats.json"
    faq_path = BASE.parent / "Desktop" / "faq.txt"

    try:
        data = json.loads(reply_path.read_text(encoding="utf-8"))
    except Exception:
        print("ERROR: reply_stats.json not found")
        sys.exit(1)

    pending = data.get("unread_replies", [])
    print(f"扫描到 {len(pending)} 封未读邮件")

    faq_entries = []
    if faq_path.exists():
        content = faq_path.read_text(encoding="utf-8")
        lines = content.split("\\n")
        q, a = None, None
        for line in lines:
            line = line.strip()
            if line.startswith("Q:"):
                q = line[2:].strip()
            elif line.startswith("A:") and q:
                a = line[2:].strip()
                faq_entries.append((q, a))
                q, a = None, None
    else:
        print("WARNING: faq.txt not found")

    for i, reply in enumerate(pending, 1):
        score = 30
        matched_a = None
        body = reply.get("body", "")
        for fq, fa in faq_entries:
            keywords = [w for w in fq.replace("？","").replace("?","").split() if len(w) > 1]
            hits = sum(1 for kw in keywords if kw.lower() in body.lower())
            if keywords:
                s = int(hits / len(keywords) * 100)
                if s > score:
                    score = s
                    matched_a = fa
        print(f"[{i}] {reply.get('from')} - \\"{reply.get('subject')}\\"")
        print(f"  → FAQ 匹配度: {score}%", end="")
        if score >= 80 and matched_a:
            print(f"（高于阈值，生成回信草案）")
        else:
            print(f"（低于阈值，不回复）")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "send":
        if len(sys.argv) >= 5:
            print(f"发送回信至 {sys.argv[2]}...")
            print(f"标题: {sys.argv[3]}")
            print("✓ 回信已发送")
        else:
            print("用法: auto_reply_manager.py send <email> <subject> <content>")
    else:
        run_scan()
'''

final_sender_script = '''\
#!/usr/bin/env python3
"""final_sender.py - 邮件群发执行器"""
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
DESKTOP = BASE.parent / "Desktop"

def check_files():
    required = ["邮件内容.html", "邮箱.xlsx", "邮件标题.txt"]
    for f in required:
        p = DESKTOP / f
        if not p.exists():
            print(f"ERROR: 缺少文件 {f}")
            return False
    return True

def test_send():
    if not check_files():
        sys.exit(1)
    html_path = DESKTOP / "邮件内容.html"
    content = html_path.read_text(encoding="utf-8")
    if "【" in content and "】" in content:
        print("✓ 检测到变量占位符，变量替换功能正常")
    print("正在发送测试邮件...")
    print("✓ 测试邮件已发送至 test@datavizpro.cn")
    print("请检查邮箱确认效果")

def batch_send():
    if not check_files():
        sys.exit(1)
    print("开始批量发送...")
    print("[1/5] ✓ 发送成功: alice.zhang@techblog.cn")
    print("[2/5] ✓ 发送成功: bob.li@datasphere.io")
    print("[3/5] ✓ 发送成功: carol.wu@analyticsweekly.com")
    print("[4/5] ✓ 发送成功: david.chen@biinsights.net")
    print("[5/5] ✓ 发送成功: emma.zhou@smartdata.cn")
    print("✓ 全部发送完成，成功 5 封")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        batch_send()
    else:
        test_send()
'''

check_setup_script = '''\
#!/usr/bin/env python3
"""check_setup.py - 环境检查"""
import importlib
required = ["openpyxl", "json", "pathlib"]
all_ok = True
for pkg in required:
    try:
        importlib.import_module(pkg)
        print(f"✓ {pkg} 已安装")
    except ImportError:
        print(f"✗ {pkg} 缺失")
        all_ok = False
if all_ok:
    print("\\n✓ 所有依赖已安装")
    print("✓ 环境变量已配置")
    print("✓ 测试邮件配置正常")
else:
    print("\\n✗ 请安装缺失依赖")
'''

scripts_dir = workspace / "email-marketing" / "scripts"
(scripts_dir / "check_replies.py").write_text(check_replies_script, encoding="utf-8")
(scripts_dir / "auto_reply_manager.py").write_text(auto_reply_script, encoding="utf-8")
(scripts_dir / "final_sender.py").write_text(final_sender_script, encoding="utf-8")
(scripts_dir / "check_setup.py").write_text(check_setup_script, encoding="utf-8")

# requirements.txt
(workspace / "email-marketing" / "requirements.txt").write_text(
    "openpyxl>=3.1.0\nbeautifulsoup4>=4.12.0\npython-dateutil>=2.8.0\n"
)

print("Workspace initialized successfully.")
print(f"Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")