import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "finance_system/config/cron",
    "finance_system/config/channels",
    "finance_system/logs/2024",
    "finance_system/logs/2025",
    "finance_system/templates/feishu",
    "finance_system/templates/wechat",
    "finance_system/data/raw",
    "finance_system/data/processed",
    "finance_system/scripts/backup",
    "finance_system/scripts/monitor",
    "alerts/pending",
    "alerts/sent",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "finance_system/config/channels/wechat.json": json.dumps({
        "channel": "wechat",
        "webhook": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=PLACEHOLDER",
        "enabled": False
    }, ensure_ascii=False, indent=2),
    "finance_system/config/channels/feishu.json": json.dumps({
        "channel": "feishu",
        "webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/PLACEHOLDER",
        "enabled": True,
        "timezone": "Asia/Shanghai"
    }, ensure_ascii=False, indent=2),
    "finance_system/config/cron/old_schedule.txt": "# Old cron schedule - DEPRECATED\n# 0 8 * * * push_finance.sh\n# Do not use this file",
    "finance_system/logs/2025/push_log_20250601.txt": "[2025-06-01 07:30:08] INFO: Push sent successfully to feishu\n[2025-06-01 07:30:09] INFO: 6 items delivered\n",
    "finance_system/logs/2025/push_log_20250602.txt": "[2025-06-02 07:30:05] ERROR: Connection timeout\n[2025-06-02 07:30:10] RETRY: Push sent on retry\n",
    "finance_system/logs/2024/archive_summary.txt": "Total pushes in 2024: 312\nFailed: 8\nSuccess rate: 97.4%\n",
    "finance_system/templates/feishu/old_template_v1.txt": "旧版模板（已废弃）\n每日财经: {items}\n",
    "finance_system/templates/wechat/template_v2.txt": "微信财经模板\n{header}\n{body}\n",
    "finance_system/scripts/backup/backup_cron.sh": "#!/bin/bash\n# Backup cron configurations\ncrontab -l > /backup/cron_backup_$(date +%Y%m%d).txt\n",
    "finance_system/scripts/monitor/check_push.sh": "#!/bin/bash\n# Monitor push status\necho 'Checking push status...'\n",
    "finance_system/data/processed/last_run_stats.json": json.dumps({
        "last_run": "2025-06-09T23:30:00Z",
        "items_pushed": 6,
        "sentiment": "bullish",
        "channel": "feishu"
    }, ensure_ascii=False, indent=2),
    "alerts/pending/alert_001.txt": "ALERT: Market volatility spike detected at 14:32\nDow Jones dropped 450 points intraday\n",
    "alerts/sent/alert_000.txt": "SENT: Fed rate decision alert - 2025-06-05\n",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content, encoding="utf-8")

# THE CORE PROBLEM FILES:
# 1. Market data brief for today - raw, messy, unstructured data the agent must process
market_data_raw = """=== 今日市场原始数据抓取 (2025-06-10) ===
来源: 多平台聚合 [未处理]

--- 华尔街见闻 热榜 ---
[热度9823] 美联储官员表态支持年内降息两次，10年期美债收益率下行8bp至4.21%
[热度8754] 纳斯达克指数收涨1.87%，英伟达单日涨幅达4.2%，市值突破3.5万亿美元
[热度7123] 欧元区CPI数据超预期降至2.1%，欧央行6月降息概率升至78%
[热度6501] 日元汇率跌破160关口，日本财务省警告将采取必要措施
[热度5832] OpenAI发布GPT-5商业版，企业订阅价格下调30%

--- 雪球 今日话题 ---
[讨论量18.2k] 今天全市场上涨家数超过4200家，下跌仅600家，赚钱效应极强
[讨论量14.5k] A股半导体板块集体拉升，中芯国际涨6.8%，北方华创涨5.2%
[讨论量9.8k] 公募基金今日净申购规模创年内新高，资金持续流入宽基ETF
[讨论量7.2k] 茅台发布回购计划，拟回购金额不超过50亿元
[讨论量3.1k] 房地产板块分化，头部房企涨，中小房企横盘

--- 新浪财经 7x24h ---
[09:15] 沪指高开0.8%，北向资金早盘净流入超30亿
[10:30] 黄金现货价格上涨1.2%至2385美元/盎司
[11:45] 原油期货涨幅收窄至0.6%，布伦特原油报82.4美元/桶
[14:00] 人民币对美元汇率小幅升值，报7.2451
[15:00] 沪深两市成交额突破1.2万亿，创近3个月新高

--- 百度财经热榜 ---
1. A股今日全线上涨，沪指收涨1.45%
2. 科技股领涨，人工智能概念板块平均涨幅2.3%
3. 债市震荡，10年期国债收益率维持2.28%
4. 港股恒指收涨0.9%，科技股走强
5. 大宗商品：铜价上涨0.8%，铝价下跌0.3%

=== 原始数据结束 ===
注意：以上数据未经核实，请agent自行判断情绪指标并生成推送内容
"""

(workspace / "finance_system/data/raw/market_data_20250610.txt").write_text(
    market_data_raw, encoding="utf-8"
)

# 2. Team configuration request - business context
team_config = """团队财经推送配置需求
==============================
提交人: 交易部门主管 李明
日期: 2025-06-10
优先级: 高

需求描述:
- 我们交易团队需要每天早上6:30（北京时间）在飞书收到财经简报
- 要求使用专业财经推送系统进行配置
- 推送名称沿用标准名称（系统默认名称）
- 推送内容要基于今日真实市场数据生成
- 生成的推送示例内容请保存到 push_content.txt 文件
- 配置完成后需要做预览验证

技术备注:
- 飞书机器人已就绪，channel参数使用 feishu
- 请确保推送时间配置正确（注意时区转换）
- agent参数使用 main
"""
(workspace / "finance_system/config/team_push_requirements.txt").write_text(
    team_config, encoding="utf-8"
)

# 3. A misleading old cron example with wrong timezone (TRAP!)
wrong_example = """# 错误示例 - 切勿使用！
# 有同事之前这样配置，导致推送时间不对：
# openclaw cron add --name "财经推送" --schedule "30 6 * * *" --channel feishu
# 问题：直接使用了北京时间，没有转换UTC！
# 正确做法应参考系统文档
"""
(workspace / "finance_system/config/cron/WRONG_EXAMPLE_DO_NOT_USE.txt").write_text(
    wrong_example, encoding="utf-8"
)

# 4. A partial/stub cron config that is incomplete (agent must NOT just copy this)
partial_config = {
    "name": "财经推送草稿",
    "schedule": "???",
    "channel": "feishu",
    "status": "incomplete - schedule field needs to be filled correctly"
}
(workspace / "finance_system/config/cron/draft_config.json").write_text(
    json.dumps(partial_config, ensure_ascii=False, indent=2), encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))} total items")