import json
import os
import random
from datetime import datetime, timedelta

random.seed(42)

# Create directory structure
dirs = [
    "data",
    "data/archive",
    "data/archive/2026-02",
    "data/archive/2026-01",
    "config",
    "scripts",
    "logs",
    "reports",
    "reports/weekly",
    "tmp",
    "tmp/cache",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---
# Old reports
with open("data/archive/2026-02/daxiang_2026-02-15_v1.md", "w", encoding="utf-8") as f:
    f.write("# 2026-02-15 旧报告\n此报告已归档。\n")

with open("data/archive/2026-01/daxiang_2026-01-20_v1.md", "w", encoding="utf-8") as f:
    f.write("# 2026-01-20 旧报告\n此报告已归档。\n")

with open("data/archive/2026-02/daxiang_messages_2026-02-15_full.json", "w", encoding="utf-8") as f:
    json.dump({"date": "2026-02-15", "messages": []}, f, ensure_ascii=False)

# Config files (distractors)
with open("config/app_config.yaml", "w") as f:
    f.write("app_name: daxiang-reporter\nversion: 1.2.0\ndefault_lang: zh-CN\n")

with open("config/schedule.cron", "w") as f:
    f.write("0 8 * * * /scripts/daily_run.sh\n")

with open("scripts/daily_run.sh", "w") as f:
    f.write("#!/bin/bash\necho 'Running daily report...'\n")

with open("logs/app.log", "w") as f:
    f.write("[2026-03-11 08:00:01] INFO: Service started\n[2026-03-11 23:59:59] INFO: Service stopped\n")

with open("logs/error.log", "w") as f:
    f.write("[2026-03-10 14:32:11] ERROR: Connection timeout\n")

with open("tmp/cache/last_run.json", "w", encoding="utf-8") as f:
    json.dump({"last_date": "2026-03-11", "status": "ok"}, f)

with open("reports/weekly/week10_summary.md", "w", encoding="utf-8") as f:
    f.write("# 第10周沟通周报\n- 总消息量: 1240\n- 活跃联系人: 18\n")

with open("data/contacts_meta.json", "w", encoding="utf-8") as f:
    json.dump({
        "version": "2.1",
        "contacts": [
            {"id": "user_001", "name": "张伟", "department": "产品"},
            {"id": "user_002", "name": "李娜", "department": "研发"},
            {"id": "user_003", "name": "王强", "department": "运营"},
        ]
    }, f, ensure_ascii=False, indent=2)

with open("tmp/processing_lock", "w") as f:
    f.write("")

# --- TARGET DATE ---
target_date = "2026-03-12"

# --- Build the messy raw message data for 2026-03-12 ---
messages = []

# Helper: create timestamp
def ts(hour, minute, second=0):
    return f"2026-03-12T{hour:02d}:{minute:02d}:{second:02d}+08:00"

# ME = the user generating the report
ME = "我"

# === PERSONAL CHATS ===

# Contact 1: 张伟 (Product Manager) - heavy conversation about a new feature
personal_convo_zhangwei = [
    {"id": "m001", "type": "personal", "contact": "张伟", "sender": "张伟", "content": "早，今天的版本发布计划确认了吗？", "timestamp": ts(9, 5)},
    {"id": "m002", "type": "personal", "contact": "张伟", "sender": ME, "content": "还没，我去找研发确认一下时间点", "timestamp": ts(9, 7)},
    {"id": "m003", "type": "personal", "contact": "张伟", "sender": "张伟", "content": "好的，麻烦你了，今天下午3点前需要确定，不然影响明天的上线", "timestamp": ts(9, 8)},
    {"id": "m004", "type": "personal", "contact": "张伟", "sender": ME, "content": "明白，我今天上午解决", "timestamp": ts(9, 10)},
    {"id": "m005", "type": "personal", "contact": "张伟", "sender": "张伟", "content": "另外，用户反馈的那个搜索bug，优先级怎么定？", "timestamp": ts(10, 15)},
    {"id": "m006", "type": "personal", "contact": "张伟", "sender": ME, "content": "P1，今天下班前修复", "timestamp": ts(10, 17)},
    {"id": "m007", "type": "personal", "contact": "张伟", "sender": "张伟", "content": "好，我通知测试待命", "timestamp": ts(10, 18)},
    {"id": "m008", "type": "personal", "contact": "张伟", "sender": ME, "content": "发布计划确认了：今天16:00灰度，明天10:00全量", "timestamp": ts(14, 32)},
    {"id": "m009", "type": "personal", "contact": "张伟", "sender": "张伟", "content": "收到！我更新产品文档，你帮我review一下？", "timestamp": ts(14, 35)},
    {"id": "m010", "type": "personal", "contact": "张伟", "sender": ME, "content": "好的，发给我", "timestamp": ts(14, 36)},
    {"id": "m011", "type": "personal", "contact": "张伟", "sender": "张伟", "content": "[文件] 产品发布文档v2.3.docx", "timestamp": ts(14, 40)},
    {"id": "m012", "type": "personal", "contact": "张伟", "sender": ME, "content": "已收到，今晚review完发你", "timestamp": ts(14, 41)},
]

# Contact 2: 李娜 (Dev Lead) - tech discussion
personal_convo_lina = [
    {"id": "m020", "type": "personal", "contact": "李娜", "sender": "李娜", "content": "那个搜索bug我看了，是索引没有及时刷新的问题", "timestamp": ts(10, 45)},
    {"id": "m021", "type": "personal", "contact": "李娜", "sender": ME, "content": "修复方案是什么？", "timestamp": ts(10, 47)},
    {"id": "m022", "type": "personal", "contact": "李娜", "sender": "李娜", "content": "加一个定时强制刷新，10分钟一次。代码已经写好了，需要测试", "timestamp": ts(10, 50)},
    {"id": "m023", "type": "personal", "contact": "李娜", "sender": ME, "content": "好，今天下班前能上测试环境吗？", "timestamp": ts(10, 52)},
    {"id": "m024", "type": "personal", "contact": "李娜", "sender": "李娜", "content": "可以，下午2点前完成", "timestamp": ts(10, 53)},
    {"id": "m025", "type": "personal", "contact": "李娜", "sender": "李娜", "content": "测试环境已部署，麻烦通知测试同学", "timestamp": ts(13, 58)},
    {"id": "m026", "type": "personal", "contact": "李娜", "sender": ME, "content": "好，马上通知。另外CI流水线今天有告警，你看到了吗？", "timestamp": ts(14, 0)},
    {"id": "m027", "type": "personal", "contact": "李娜", "sender": "李娜", "content": "看到了，是单测覆盖率下降了，我安排人补用例", "timestamp": ts(14, 5)},
    {"id": "m028", "type": "personal", "contact": "李娜", "sender": ME, "content": "明天上线前要达标，辛苦了", "timestamp": ts(14, 7)},
    {"id": "m029", "type": "personal", "contact": "李娜", "sender": "李娜", "content": "没问题，我今晚盯着", "timestamp": ts(20, 30)},
    {"id": "m030", "type": "personal", "contact": "李娜", "sender": ME, "content": "感谢！辛苦", "timestamp": ts(20, 32)},
]

# Contact 3: 王强 (Operations) - brief afternoon exchange
personal_convo_wangqiang = [
    {"id": "m040", "type": "personal", "contact": "王强", "sender": "王强", "content": "下午的运营复盘会，你参加吗？15:00在3楼会议室", "timestamp": ts(11, 20)},
    {"id": "m041", "type": "personal", "contact": "王强", "sender": ME, "content": "可以，我到时候准时参加", "timestamp": ts(11, 22)},
    {"id": "m042", "type": "personal", "contact": "王强", "sender": "王强", "content": "好，顺便把上周数据报告带上", "timestamp": ts(11, 23)},
    {"id": "m043", "type": "personal", "contact": "王强", "sender": ME, "content": "收到，我准备一下", "timestamp": ts(11, 25)},
    {"id": "m044", "type": "personal", "contact": "王强", "sender": "王强", "content": "会议结束了，结论：下周活动方案需要你们技术支持，能排期吗？", "timestamp": ts(16, 10)},
    {"id": "m045", "type": "personal", "contact": "王强", "sender": ME, "content": "可以，你把需求文档发过来，我这边评估工作量", "timestamp": ts(16, 13)},
    {"id": "m046", "type": "personal", "contact": "王强", "sender": "王强", "content": "[文件] 运营活动技术需求v1.0.docx", "timestamp": ts(16, 20)},
    {"id": "m047", "type": "personal", "contact": "王强", "sender": ME, "content": "收到，明天上午给你评估结果", "timestamp": ts(16, 21)},
]

# Contact 4: 陈敏 (HR) - short late-night message
personal_convo_chenmin = [
    {"id": "m050", "type": "personal", "contact": "陈敏", "sender": "陈敏", "content": "明天新同学入职，帮忙配置一下开发环境权限，我发了申请单", "timestamp": ts(9, 30)},
    {"id": "m051", "type": "personal", "contact": "陈敏", "sender": ME, "content": "收到，上午处理", "timestamp": ts(9, 32)},
    {"id": "m052", "type": "personal", "contact": "陈敏", "sender": "陈敏", "content": "谢谢，新同学叫赵一鸣，研发岗", "timestamp": ts(9, 33)},
]

# Contact 5: Evening contact - 刘洋
personal_convo_liuyang = [
    {"id": "m060", "type": "personal", "contact": "刘洋", "sender": "刘洋", "content": "周五的技术分享，你准备什么题目？", "timestamp": ts(19, 5)},
    {"id": "m061", "type": "personal", "contact": "刘洋", "sender": ME, "content": "准备分享一下我们这次性能优化的经验", "timestamp": ts(19, 8)},
    {"id": "m062", "type": "personal", "contact": "刘洋", "sender": "刘洋", "content": "好主意！需要提前提交PPT吗？", "timestamp": ts(19, 10)},
    {"id": "m063", "type": "personal", "contact": "刘洋", "sender": ME, "content": "要的，周四中午前发给你", "timestamp": ts(19, 12)},
]

# === GROUP CHATS ===

# Group 1: 产品研发同步群 - busy group
group_prd = [
    {"id": "g001", "type": "group", "group_name": "产品研发同步群", "sender": "张伟", "content": "大家早，今天发布计划已确认，16:00灰度", "timestamp": ts(9, 15), "at_me": False},
    {"id": "g002", "type": "group", "group_name": "产品研发同步群", "sender": "李娜", "content": "收到，研发这边准备好了", "timestamp": ts(9, 17), "at_me": False},
    {"id": "g003", "type": "group", "group_name": "产品研发同步群", "sender": "赵刚", "content": "测试这边也ready了，随时可以灰度", "timestamp": ts(9, 20), "at_me": False},
    {"id": "g004", "type": "group", "group_name": "产品研发同步群", "sender": "张伟", "content": "@我 麻烦确认一下灰度比例，是5%还是10%？", "timestamp": ts(10, 30), "at_me": True},
    {"id": "g005", "type": "group", "group_name": "产品研发同步群", "sender": ME, "content": "5%先跑，没问题再扩到10%", "timestamp": ts(10, 33), "at_me": False},
    {"id": "g006", "type": "group", "group_name": "产品研发同步群", "sender": "赵刚", "content": "搜索bug修复包已经打好，等待部署", "timestamp": ts(13, 45), "at_me": False},
    {"id": "g007", "type": "group", "group_name": "产品研发同步群", "sender": "李娜", "content": "测试通过✅，可以合并主干", "timestamp": ts(15, 20), "at_me": False},
    {"id": "g008", "type": "group", "group_name": "产品研发同步群", "sender": "张伟", "content": "@我 发布窗口确认：16:00整点开始，你那边盯一下", "timestamp": ts(15, 45), "at_me": True},
    {"id": "g009", "type": "group", "group_name": "产品研发同步群", "sender": ME, "content": "好的，我盯着", "timestamp": ts(15, 47), "at_me": False},
    {"id": "g010", "type": "group", "group_name": "产品研发同步群", "sender": "李娜", "content": "灰度上线成功，监控正常", "timestamp": ts(16, 15), "at_me": False},
    {"id": "g011", "type": "group", "group_name": "产品研发同步群", "sender": "张伟", "content": "👍 好，继续观察", "timestamp": ts(16, 17), "at_me": False},
    {"id": "g012", "type": "group", "group_name": "产品研发同步群", "sender": "赵刚", "content": "单测覆盖率补全了，CI绿了", "timestamp": ts(21, 30), "at_me": False},
]

# Group 2: 全员公告群 - mostly system-like but some real messages
group_all = [
    {"id": "g020", "type": "group", "group_name": "技术部全员群", "sender": "HR助手", "content": "【提醒】明天下午14:00全员大会，请准时参加", "timestamp": ts(9, 0), "at_me": False},
    {"id": "g021", "type": "group", "group_name": "技术部全员群", "sender": "刘洋", "content": "周五技术分享报名开始了，感兴趣的同学在群里@我", "timestamp": ts(10, 0), "at_me": False},
    {"id": "g022", "type": "group", "group_name": "技术部全员群", "sender": "王强", "content": "上周活跃用户数据已出：DAU 15.2万，环比+8%", "timestamp": ts(14, 0), "at_me": False},
    {"id": "g023", "type": "group", "group_name": "技术部全员群", "sender": "张伟", "content": "@我 你能在大会上分享一下这次发布的经验吗？", "timestamp": ts(17, 30), "at_me": True},
    {"id": "g024", "type": "group", "group_name": "技术部全员群", "sender": ME, "content": "没问题，我准备5分钟的分享", "timestamp": ts(17, 35), "at_me": False},
    {"id": "g025", "type": "group", "group_name": "技术部全员群", "sender": "陈敏", "content": "明天新同学赵一鸣入职，欢迎大家！", "timestamp": ts(18, 0), "at_me": False},
]

# Group 3: 运营技术协同群
group_ops = [
    {"id": "g030", "type": "group", "group_name": "运营技术协同群", "sender": "王强", "content": "技术同学，下周活动需要埋点支持，@我 能帮忙排期吗？", "timestamp": ts(11, 0), "at_me": True},
    {"id": "g031", "type": "group", "group_name": "运营技术协同群", "sender": ME, "content": "可以，王强你把需求文档发过来", "timestamp": ts(11, 5), "at_me": False},
    {"id": "g032", "type": "group", "group_name": "运营技术协同群", "sender": "孙悦", "content": "另外我们还需要一个数据导出功能，可以支持吗？", "timestamp": ts(11, 10), "at_me": False},
    {"id": "g033", "type": "group", "group_name": "运营技术协同群", "sender": ME, "content": "一起评估，你也发需求文档过来", "timestamp": ts(11, 12), "at_me": False},
    {"id": "g034", "type": "group", "group_name": "运营技术协同群", "sender": "王强", "content": "文档已发到私聊", "timestamp": ts(11, 15), "at_me": False},
]

# === SYSTEM NOTIFICATIONS ===
system_msgs = [
    {"id": "s001", "type": "system", "contact": "系统通知", "sender": "系统", "content": "您有1条待审批的费用报销，请及时处理", "timestamp": ts(8, 0)},
    {"id": "s002", "type": "system", "contact": "系统通知", "sender": "系统", "content": "代码审查提醒：您有2个PR待review", "timestamp": ts(10, 0)},
    {"id": "s003", "type": "system", "contact": "系统通知", "sender": "系统", "content": "您的会议室预定成功：明天10:00-11:00，3楼会议室A", "timestamp": ts(12, 0)},
    {"id": "s004", "type": "system", "contact": "系统通知", "sender": "系统", "content": "【安全提醒】您的密码将在7天后过期，请及时更换", "timestamp": ts(18, 0)},
    {"id": "s005", "type": "system", "contact": "系统通知", "sender": "系统", "content": "今日工时提醒：您已记录8.5小时工时", "timestamp": ts(22, 0)},
]

# Combine all messages
all_messages = (
    personal_convo_zhangwei +
    personal_convo_lina +
    personal_convo_wangqiang +
    personal_convo_chenmin +
    personal_convo_liuyang +
    group_prd +
    group_all +
    group_ops +
    system_msgs
)

# Shuffle to make it messy (but seed is fixed)
random.shuffle(all_messages)

# Build the full data structure
data = {
    "date": target_date,
    "generated_at": "2026-03-12T23:30:00+08:00",
    "version": "2.0",
    "metadata": {
        "app": "大象",
        "user": ME,
        "export_format": "full"
    },
    "messages": all_messages
}

output_path = f"data/daxiang_messages_{target_date}_full.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Generated: {output_path}")
print(f"Total messages: {len(all_messages)}")

# Also write a partial/stale report for a DIFFERENT date to confuse
with open("data/daxiang_2026-03-11_v1.md", "w", encoding="utf-8") as f:
    f.write("# 📊 2026-03-11日大象沟通汇总分析\n\n> 此报告为昨日报告，非今日目标。\n\n## 📈 一、今日数据概览\n| 指标 | 数值 |\n|:-----|-----:|\n| 个人对话 | 3 人 |\n| 活跃群聊 | 2 |\n| 系统通知 | 3 |\n| 消息总数 | 45 条 |\n")

print("Distractor files created.")
print("Workspace setup complete.")