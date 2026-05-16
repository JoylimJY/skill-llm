import os
import csv
import json
import random

random.seed(42)

# ---------- directory structure ----------
base = "/workspace"
skill_dir = os.path.join(base, "skills", "newsletter-growth-hacker", "scripts")
os.makedirs(skill_dir, exist_ok=True)

refs_dir = os.path.join(base, "skills", "newsletter-growth-hacker", "references")
os.makedirs(refs_dir, exist_ok=True)

reports_dir = os.path.join(base, "reports", "fintech_weekly")
os.makedirs(reports_dir, exist_ok=True)

data_dir = os.path.join(base, "data", "raw")
os.makedirs(data_dir, exist_ok=True)

logs_dir = os.path.join(base, "logs")
os.makedirs(logs_dir, exist_ok=True)

archive_dir = os.path.join(base, "archive", "2025")
os.makedirs(archive_dir, exist_ok=True)

# ---------- distractor files ----------
distractors = [
    (os.path.join(base, "config.yaml"), "# Placeholder config\nenv: production\ndebug: false\n"),
    (os.path.join(base, "Makefile"), "all:\n\techo 'nothing to build'\n"),
    (os.path.join(base, "requirements.txt"), "textstat\ntabulate\n"),
    (os.path.join(base, "logs", "app.log"), "2026-03-01 INFO Started\n2026-03-02 INFO Running\n"),
    (os.path.join(base, "archive", "2025", "q4_summary.txt"), "Q4 2025: 4200 subscribers\n"),
    (os.path.join(base, "reports", "fintech_weekly", "old_report_2025Q4.txt"), "Old report placeholder\n"),
    (os.path.join(base, "data", "raw", "unrelated_crm_export.csv"),
     "id,name,email\n1,Alice,alice@example.com\n2,Bob,bob@example.com\n"),
    (os.path.join(base, "skills", "newsletter-growth-hacker", "references", "email_marketing_best_practices.md"),
     "# Best Practices\n- Keep it short\n- Personalize\n"),
    (os.path.join(base, "skills", "newsletter-growth-hacker", "references", "subject_line_templates.md"),
     "# Templates\n- [Number] ways to...\n- How to...\n"),
    (os.path.join(base, "skills", "newsletter-growth-hacker", "references", "industry_benchmarks.md"),
     "# Benchmarks\nOpen rate avg: 21%\nClick rate avg: 3.5%\n"),
    (os.path.join(base, "data", "raw", "placeholder_notes.txt"),
     "TODO: clean up campaign data\n"),
]

for path, content in distractors:
    with open(path, "w") as f:
        f.write(content)

# ---------- PROBLEM FILE 1: messy historical growth data ----------
# This CSV has inconsistent column names, extra whitespace, one row with a string
# total that needs to be parsed, and source breakdown embedded as a JSON string.
# The agent must correctly parse this and feed into GrowthTracker.
growth_csv_path = os.path.join(base, "data", "raw", "subscriber_history.csv")
growth_rows = [
    # Header intentionally has extra spaces
    ["  period  ", " total_subscribers ", " new_subs ", " lost_subs ", " source_organic ", " source_referral ", " source_paid "],
    ["2025-10", "4800", "310", "38", "140", "95", "75"],
    ["2025-11", "5072", "  355 ", "83", "160", "110", "85"],  # extra whitespace in new_subs
    ["2025-12", "5344", "320", "48", "145", "100", "75"],
    ["2026-01", "5616", "345", "73", "150", "115", "80"],
    ["2026-02", "5888", "  398 ", "126", "185", "130", "83"],  # extra whitespace
    ["2026-03", "6160", "430", "158", "200", "140", "90"],
]

with open(growth_csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(growth_rows)

# ---------- PROBLEM FILE 2: messy campaign metrics ----------
# Intentionally uses slightly different key casing and one value as float string
campaign_json_path = os.path.join(base, "data", "raw", "q1_campaign_metrics.json")
campaign_data = {
    "Campaign": "FinTech Weekly Q1 2026",
    "Sent": "52000",
    "Delivered": "51168",       # int as string
    "Opened": "13815",
    "Clicked": "2764",
    "Unsubscribed": "78",
    "Bounced": "832",
    "Spam_Complaints": "26",    # underscore variant — agent must map correctly
}
with open(campaign_json_path, "w") as f:
    json.dump(campaign_data, f, indent=2)

# ---------- PROBLEM FILE 3: task brief ----------
brief_path = os.path.join(base, "data", "raw", "task_brief.txt")
brief_content = """\
FINTECH WEEKLY — Q1 2026 QUARTERLY REVIEW BRIEF
================================================

We need a unified machine-readable report for the board covering three areas:

1. GROWTH FORECAST
   Using our subscriber history data (subscriber_history.csv), analyse
   the last 6 months of growth and project the next 4 months.

2. CAMPAIGN HEALTH
   Using Q1 campaign metrics (q1_campaign_metrics.json), produce a full
   performance assessment of the 'FinTech Weekly Q1 2026' campaign.

3. SUBJECT LINE OPTIONS FOR Q2
   Topic: "市场波动中的理财策略"
   Goal: "提升打开率"
   We want EXACTLY 4 subject line variants for A/B testing.

OUTPUT: Save everything as a single JSON file named quarterly_review.json.
The file must have three top-level keys: "growth_projections", "campaign_report",
and "ab_test_variants".
- "growth_projections" should be the list of projected future periods.
- "campaign_report" should be the full report dict from the analytics engine.
- "ab_test_variants" should be the list of variant dicts from the A/B test.
"""
with open(brief_path, "w") as f:
    f.write(brief_content)

# ---------- Write the actual skill scripts ----------
# subscriber_acquisition.py
sub_acq = r'''
"""Subscriber Acquisition Strategy Engine"""

class SubscriberAcquisition:
    STRATEGIES = {
        "content_upgrade": {
            "name": "内容升级策略",
            "conversion_rate_min": 0.03,
            "conversion_rate_max": 0.08,
            "investment": "中等",
            "roi": "高",
            "monthly_growth_rate": 0.05,
        },
        "social_proof": {
            "name": "社会证明策略",
            "conversion_rate_min": 0.02,
            "conversion_rate_max": 0.05,
            "investment": "低",
            "roi": "中高",
            "monthly_growth_rate": 0.03,
        },
        "referral_program": {
            "name": "推荐计划",
            "conversion_rate_min": 0.15,
            "conversion_rate_max": 0.25,
            "investment": "高",
            "roi": "非常高",
            "monthly_growth_rate": 0.12,
        },
        "cross_promotion": {
            "name": "交叉推广",
            "conversion_rate_min": 0.05,
            "conversion_rate_max": 0.12,
            "investment": "中等",
            "roi": "高",
            "monthly_growth_rate": 0.07,
        },
        "seo_lead_magnet": {
            "name": "SEO 引流磁铁",
            "conversion_rate_min": 0.02,
            "conversion_rate_max": 0.06,
            "investment": "高（前期）",
            "roi": "长期非常高",
            "monthly_growth_rate": 0.04,
        },
        "paid_ads": {
            "name": "付费广告",
            "conversion_rate_min": 0.01,
            "conversion_rate_max": 0.04,
            "investment": "中等",
            "roi": "取决于 CPC",
            "monthly_growth_rate": 0.06,
        },
    }

    def get_strategies(self):
        return self.STRATEGIES

    def calculate_projection(self, current_subscribers, strategy, months):
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy}")
        s = self.STRATEGIES[strategy]
        rate = s["monthly_growth_rate"]
        results = []
        subs = current_subscribers
        for m in range(1, months + 1):
            new_subs = int(subs * rate)
            subs += new_subs
            results.append({"month": m, "subscribers": subs, "new_this_month": new_subs})
        return {
            "strategy": s["name"],
            "initial_subscribers": current_subscribers,
            "final_subscribers": subs,
            "total_growth": subs - current_subscribers,
            "monthly_growth_rate": rate,
            "monthly_breakdown": results,
        }
'''

# content_optimizer.py
content_opt = r'''
"""Content Optimizer and Subject Line Generator"""

import random

class ContentOptimizer:
    def analyze_content(self, content):
        words = content.split()
        word_count = len(words)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        para_count = len(paragraphs)
        has_subject = '【主题行】' in content or content.strip().startswith('[')
        has_cta = any(kw in content for kw in ['点击', '立即', '查看', '了解更多', 'CTA', '行动'])
        mobile_friendly = word_count < 500
        readability = max(0, min(100, 100 - word_count // 10))
        suggestions = []
        if word_count > 500:
            suggestions.append("内容过长，建议精简至 500 字以内")
        if para_count < 3:
            suggestions.append("段落结构单薄，建议增加段落层次")
        if not has_cta:
            suggestions.append("缺少明确的行动号召（CTA）")
        if not mobile_friendly:
            suggestions.append("内容较长，注意移动端阅读体验")
        return {
            "word_count": word_count,
            "paragraph_count": para_count,
            "readability_score": readability,
            "has_subject_line": has_subject,
            "has_cta": has_cta,
            "mobile_friendly": mobile_friendly,
            "suggestions": suggestions,
        }


class SubjectLineGenerator:
    STYLES = {
        "curiosity": {
            "name": "好奇型",
            "open_rate_min": 0.22,
            "open_rate_max": 0.28,
            "click_rate_min": 0.03,
            "click_rate_max": 0.05,
            "templates": [
                "你不知道的{topic}秘密",
                "关于{topic}，90% 的人都搞错了",
                "这个{topic}技巧改变了我的一切",
            ],
        },
        "urgency": {
            "name": "紧迫型",
            "open_rate_min": 0.25,
            "open_rate_max": 0.35,
            "click_rate_min": 0.04,
            "click_rate_max": 0.07,
            "templates": [
                "【限时】{topic}机会即将关闭",
                "最后 24 小时：{topic}",
                "紧急：{topic}你必须知道",
            ],
        },
        "benefit": {
            "name": "利益型",
            "open_rate_min": 0.20,
            "open_rate_max": 0.26,
            "click_rate_min": 0.05,
            "click_rate_max": 0.08,
            "templates": [
                "用{topic}每月多赚 5000 元",
                "{topic}：让你的收益翻倍",
                "掌握{topic}，实现财务自由",
            ],
        },
        "social_proof": {
            "name": "社会证明型",
            "open_rate_min": 0.23,
            "open_rate_max": 0.29,
            "click_rate_min": 0.04,
            "click_rate_max": 0.06,
            "templates": [
                "10000 人正在用的{topic}方法",
                "专家推荐：{topic}",
                "为什么顶尖投资者都关注{topic}",
            ],
        },
        "question": {
            "name": "提问型",
            "open_rate_min": 0.21,
            "open_rate_max": 0.27,
            "click_rate_min": 0.03,
            "click_rate_max": 0.05,
            "templates": [
                "你的{topic}策略真的有效吗？",
                "为什么{topic}总是失败？",
                "{topic}，你准备好了吗？",
            ],
        },
        "list": {
            "name": "列表型",
            "open_rate_min": 0.24,
            "open_rate_max": 0.30,
            "click_rate_min": 0.04,
            "click_rate_max": 0.07,
            "templates": [
                "5 个{topic}必知技巧",
                "7 步掌握{topic}",
                "关于{topic}的 3 个真相",
            ],
        },
        "story": {
            "name": "故事型",
            "open_rate_min": 0.22,
            "open_rate_max": 0.28,
            "click_rate_min": 0.05,
            "click_rate_max": 0.09,
            "templates": [
                "我如何用{topic}翻转财务困境",
                "从零到百万：{topic}的真实故事",
                "一个关于{topic}的深刻教训",
            ],
        },
    }

    def create_ab_test(self, topic, goal, variants=3):
        rng = random.Random(topic + goal + str(variants))
        style_keys = list(self.STYLES.keys())
        selected = rng.sample(style_keys, min(variants, len(style_keys)))
        variant_list = []
        for i, key in enumerate(selected):
            style = self.STYLES[key]
            template = rng.choice(style["templates"])
            subject = template.replace("{topic}", topic)
            variant_list.append({
                "variant": chr(65 + i),
                "style": style["name"],
                "subject_line": subject,
                "predicted_open_rate": f"{int(style['open_rate_min']*100)}-{int(style['open_rate_max']*100)}%",
                "predicted_click_rate": f"{int(style['click_rate_min']*100)}-{int(style['click_rate_max']*100)}%",
            })
        return {
            "topic": topic,
            "goal": goal,
            "variants": variant_list,
            "test_settings": {
                "min_sample_size_per_variant": 1000,
                "test_duration_hours": "24-48",
                "primary_metric": "打开率",
                "secondary_metric": "点击率",
            },
        }
'''

# analytics_engine.py
analytics_eng = r'''
"""Analytics Engine and Growth Tracker"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class NewsletterMetrics:
    sent: int
    delivered: int
    opened: int
    clicked: int
    unsubscribed: int
    bounced: int
    spam_complaints: int

    @property
    def delivery_rate(self):
        return self.delivered / self.sent if self.sent else 0

    @property
    def open_rate(self):
        return self.opened / self.delivered if self.delivered else 0

    @property
    def click_rate(self):
        return self.clicked / self.delivered if self.delivered else 0

    @property
    def click_to_open_rate(self):
        return self.clicked / self.opened if self.opened else 0

    @property
    def unsubscribe_rate(self):
        return self.unsubscribed / self.delivered if self.delivered else 0

    @property
    def bounce_rate(self):
        return self.bounced / self.sent if self.sent else 0

    @property
    def spam_rate(self):
        return self.spam_complaints / self.delivered if self.delivered else 0


class AnalyticsEngine:
    BENCHMARKS = {
        "open_rate":     {"poor": 0.15, "avg": 0.21, "good": 0.25, "excellent": 0.30},
        "click_rate":    {"poor": 0.02, "avg": 0.035, "good": 0.05, "excellent": 0.07},
        "cto_rate":      {"poor": 0.10, "avg": 0.15, "good": 0.20, "excellent": 0.25},
        "unsub_rate":    {"poor": 0.01, "avg": 0.005, "good": 0.003, "excellent": 0.001},
        "bounce_rate":   {"poor": 0.05, "avg": 0.02, "good": 0.01, "excellent": 0.005},
    }

    def _rate_metric(self, metric_name, value):
        b = self.BENCHMARKS.get(metric_name, {})
        if metric_name in ("unsub_rate", "bounce_rate"):
            if value < b.get("excellent", 0):
                return "优秀"
            elif value < b.get("good", 0):
                return "好"
            elif value < b.get("avg", 0):
                return "平均"
            else:
                return "差"
        else:
            if value >= b.get("excellent", 1):
                return "优秀"
            elif value >= b.get("good", 0.5):
                return "好"
            elif value >= b.get("avg", 0):
                return "平均"
            else:
                return "差"

    def create_report(self, campaign_name, metrics: NewsletterMetrics):
        m = metrics
        ratings = {
            "open_rate":   self._rate_metric("open_rate", m.open_rate),
            "click_rate":  self._rate_metric("click_rate", m.click_rate),
            "cto_rate":    self._rate_metric("cto_rate", m.click_to_open_rate),
            "unsub_rate":  self._rate_metric("unsub_rate", m.unsubscribe_rate),
            "bounce_rate": self._rate_metric("bounce_rate", m.bounce_rate),
        }
        insights = []
        action_items = []
        if ratings["open_rate"] in ("差", "平均"):
            insights.append("打开率低于行业基准，需优化主题行或发送时间")
            action_items.append("进行主题行 A/B 测试")
        if ratings["click_rate"] in ("差", "平均"):
            insights.append("点击率偏低，邮件内容或 CTA 需改进")
            action_items.append("优化邮件内容和 CTA 按钮")
        if ratings["unsub_rate"] == "差":
            insights.append("退订率过高，内容相关性或发送频率需调整")
            action_items.append("审查内容策略和发送频率")
        if ratings["bounce_rate"] == "差":
            insights.append("退回率过高，需清理邮件列表")
            action_items.append("执行列表清洗")
        return {
            "campaign_name": campaign_name,
            "metrics": {
                "sent": m.sent,
                "delivered": m.delivered,
                "opened": m.opened,
                "clicked": m.clicked,
                "unsubscribed": m.unsubscribed,
                "bounced": m.bounced,
                "spam_complaints": m.spam_complaints,
                "delivery_rate": round(m.delivery_rate, 4),
                "open_rate": round(m.open_rate, 4),
                "click_rate": round(m.click_rate, 4),
                "click_to_open_rate": round(m.click_to_open_rate, 4),
                "unsubscribe_rate": round(m.unsubscribe_rate, 4),
                "bounce_rate": round(m.bounce_rate, 4),
                "spam_rate": round(m.spam_rate, 4),
            },
            "ratings": ratings,
            "insights": insights,
            "action_items": action_items,
        }


class GrowthTracker:
    def __init__(self):
        self.periods = []

    def add_period(self, period: str, total_subscribers: int, new_subscribers: int,
                   lost_subscribers: int, sources: Dict[str, int]):
        net = new_subscribers - lost_subscribers
        prev_total = self.periods[-1]["total_subscribers"] if self.periods else (total_subscribers - net)
        growth_rate = net / prev_total if prev_total else 0
        self.periods.append({
            "period": period,
            "total_subscribers": total_subscribers,
            "new_subscribers": new_subscribers,
            "lost_subscribers": lost_subscribers,
            "net_growth": net,
            "growth_rate": round(growth_rate, 4),
            "sources": sources,
        })

    def get_growth_summary(self):
        if not self.periods:
            return {}
        total_new = sum(p["new_subscribers"] for p in self.periods)
        total_lost = sum(p["lost_subscribers"] for p in self.periods)
        avg_growth_rate = sum(p["growth_rate"] for p in self.periods) / len(self.periods)
        best = max(self.periods, key=lambda p: p["net_growth"])
        worst = min(self.periods, key=lambda p: p["net_growth"])
        all_sources = {}
        for p in self.periods:
            for src, cnt in p["sources"].items():
                all_sources[src] = all_sources.get(src, 0) + cnt
        return {
            "total_periods": len(self.periods),
            "start_subscribers": self.periods[0]["total_subscribers"],
            "end_subscribers": self.periods[-1]["total_subscribers"],
            "total_new": total_new,
            "total_lost": total_lost,
            "total_net": total_new - total_lost,
            "avg_growth_rate": round(avg_growth_rate, 4),
            "best_period": best["period"],
            "worst_period": worst["period"],
            "source_totals": all_sources,
        }

    def project_growth(self, months: int):
        if len(self.periods) < 3:
            raise ValueError("需要至少 3 期数据才能预测")
        recent = self.periods[-3:]
        avg_rate = sum(p["growth_rate"] for p in recent) / 3
        projections = []
        current = self.periods[-1]["total_subscribers"]
        last_period = self.periods[-1]["period"]
        year, month = map(int, last_period.split("-"))
        for i in range(1, months + 1):
            month += 1
            if month > 12:
                month = 1
                year += 1
            period_str = f"{year}-{month:02d}"
            new_subs = int(current * avg_rate)
            current = int(current * (1 + avg_rate))
            projections.append({
                "period": period_str,
                "projected_subscribers": current,
                "projected_new": new_subs,
                "growth_rate": round(avg_rate, 4),
            })
        return projections

    def get_best_source(self):
        all_sources = {}
        for p in self.periods:
            for src, cnt in p["sources"].items():
                all_sources[src] = all_sources.get(src, 0) + cnt
        if not all_sources:
            return None
        return max(all_sources, key=all_sources.get)
'''

# main.py (interactive menu - not needed for agent but required by skill)
main_py = r'''
"""Main entry point - interactive menu"""

def main():
    print("Newsletter Growth Hacker v1.0.0")
    print("1. 订阅者获取策略")
    print("2. 内容优化")
    print("3. A/B 测试生成")
    print("4. 数据分析")
    print("5. 增长追踪")
    print("请选择功能 (1-5): ", end="")
    choice = input()
    print(f"您选择了: {choice}")

if __name__ == "__main__":
    main()
'''

# Write scripts
scripts = [
    ("subscriber_acquisition.py", sub_acq),
    ("content_optimizer.py", content_opt),
    ("analytics_engine.py", analytics_eng),
    ("main.py", main_py),
]

for fname, content in scripts:
    fpath = os.path.join(skill_dir, fname)
    with open(fpath, "w") as f:
        f.write(content)

print("Workspace initialized successfully.")
print(f"Skill scripts written to: {skill_dir}")
print(f"Problem data written to: {data_dir}")