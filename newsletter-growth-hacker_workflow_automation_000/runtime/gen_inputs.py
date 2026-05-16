import os
import json
import csv
import random

random.seed(42)

WORKSPACE = "/workspace"

# ─── Directory Structure ───────────────────────────────────────────────────────
dirs = [
    "skills/newsletter-growth-hacker/scripts",
    "skills/newsletter-growth-hacker/references",
    "data/raw",
    "data/processed",
    "reports/archive",
    "reports/drafts",
    "config",
    "logs",
    "marketing/campaigns/q1",
    "marketing/campaigns/q2",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ─── Distractor Files ──────────────────────────────────────────────────────────
distractor_files = {
    "config/email_provider.yaml": "provider: mailchimp\napi_key: REDACTED\nlist_id: abc123\n",
    "config/schedule.json": json.dumps({"send_day": "Tuesday", "send_time": "10:00", "timezone": "UTC+8"}, indent=2),
    "logs/send_log_2026-01.txt": "2026-01-15 10:00:01 INFO Sent batch 1: 2500 emails\n2026-01-15 10:01:12 INFO Sent batch 2: 2500 emails\n",
    "logs/send_log_2026-02.txt": "2026-02-12 10:00:05 INFO Sent batch 1: 3000 emails\n",
    "reports/archive/q4_2025_summary.txt": "Q4 2025 Summary: 3 campaigns sent, avg open rate 22%\n",
    "reports/drafts/q2_plan_rough.txt": "Q2 Goals:\n- Reach 8000 subscribers\n- Launch referral program\n- Test 3 new subject line styles\n",
    "marketing/campaigns/q1/campaign_notes.txt": "Jan: Product launch email\nFeb: Feature update\nMar: Monthly digest\n",
    "marketing/campaigns/q2/ideas.md": "# Q2 Campaign Ideas\n- 'Behind the scenes' story series\n- Customer spotlight\n- Product roadmap reveal\n",
    "skills/newsletter-growth-hacker/references/industry_benchmarks.md": "# Industry Benchmarks\nSee SKILL.md for full table.\nKey: Open Rate avg 21%, Click Rate avg 3.5%\n",
    "skills/newsletter-growth-hacker/references/subject_line_templates.md": "# Templates\n- Curiosity: 'You won't believe what happened to our open rates...'\n- Urgency: 'Last 24 hours: [offer]'\n",
    "data/processed/subscriber_segments.csv": "segment,count\npower_users,450\ncasual_readers,1200\nleads,380\n",
}
for path, content in distractor_files.items():
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# ─── The actual skill scripts (stubs that work correctly) ─────────────────────
# subscriber_acquisition.py
subscriber_acquisition_py = '''
class SubscriberAcquisition:
    STRATEGIES = {
        "content_upgrade": {"conversion_rate": (0.03, 0.08), "investment": "medium", "roi": "high"},
        "social_proof": {"conversion_rate": (0.02, 0.05), "investment": "low", "roi": "medium_high"},
        "referral_program": {"conversion_rate": (0.15, 0.25), "investment": "high", "roi": "very_high"},
        "cross_promotion": {"conversion_rate": (0.05, 0.12), "investment": "medium", "roi": "high"},
        "seo_lead_magnet": {"conversion_rate": (0.02, 0.06), "investment": "high_upfront", "roi": "long_term_very_high"},
        "paid_ads": {"conversion_rate": (0.01, 0.04), "investment": "medium", "roi": "depends_on_cpc"},
    }

    def get_strategies(self):
        return self.STRATEGIES

    def calculate_projection(self, current_subscribers, strategy, months):
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy}")
        low, high = self.STRATEGIES[strategy]["conversion_rate"]
        avg_rate = (low + high) / 2
        monthly_growth = int(current_subscribers * avg_rate)
        total_after = current_subscribers
        for _ in range(months):
            total_after += monthly_growth
        return {
            "strategy": strategy,
            "current": current_subscribers,
            "months": months,
            "projected_total": total_after,
            "total_growth": total_after - current_subscribers,
            "monthly_growth_rate": avg_rate,
        }
'''

# content_optimizer.py
content_optimizer_py = '''
class ContentOptimizer:
    def analyze_content(self, content):
        words = content.split()
        paragraphs = [p.strip() for p in content.split("\\n\\n") if p.strip()]
        has_subject = "【主题行】" in content or "Subject:" in content.lower()
        has_cta = any(kw in content for kw in ["点击", "立即", "现在", "click", "subscribe", "join", "get"])
        word_count = len(words)
        readability = min(100, max(0, 80 - max(0, word_count - 500) // 20))
        suggestions = []
        if word_count > 800:
            suggestions.append("邮件过长，建议控制在800字以内")
        if not has_cta:
            suggestions.append("缺少明确的行动号召(CTA)")
        if len(paragraphs) < 3:
            suggestions.append("段落较少，建议增加结构层次")
        return {
            "word_count": word_count,
            "paragraph_count": len(paragraphs),
            "readability_score": readability,
            "has_subject_line": has_subject,
            "has_cta": has_cta,
            "suggestions": suggestions,
        }


STYLE_BENCHMARKS = {
    "curiosity": {"open_rate": (0.22, 0.28), "click_rate": (0.03, 0.05)},
    "urgency": {"open_rate": (0.25, 0.35), "click_rate": (0.04, 0.07)},
    "benefit": {"open_rate": (0.20, 0.26), "click_rate": (0.05, 0.08)},
    "social_proof": {"open_rate": (0.23, 0.29), "click_rate": (0.04, 0.06)},
    "question": {"open_rate": (0.21, 0.27), "click_rate": (0.03, 0.05)},
    "list": {"open_rate": (0.24, 0.30), "click_rate": (0.04, 0.07)},
    "story": {"open_rate": (0.22, 0.28), "click_rate": (0.05, 0.09)},
}

STYLE_TEMPLATES = {
    "curiosity": ["你不会相信我们的订阅者是怎么做到的...", "关于{topic}，99%的人都不知道这件事"],
    "urgency": ["仅剩24小时：{topic}限时分享", "今晚截止：{topic}独家内容"],
    "benefit": ["如何通过{topic}提升你的成果", "用{topic}让你的效率翻倍"],
    "social_proof": ["10,000人已经用{topic}改变了工作方式", "行业专家推荐：{topic}完全指南"],
    "question": ["{topic}真的有效吗？我们测试了6个月", "你的{topic}策略是否犯了这些错误？"],
    "list": ["关于{topic}的7个秘密，第3个最实用", "5个{topic}技巧，今天就能用"],
    "story": ["我曾经不相信{topic}，直到这件事发生了", "从0到1：我们用{topic}的真实经历"],
}


class SubjectLineGenerator:
    def create_ab_test(self, topic, goal, variants=3):
        styles = list(STYLE_TEMPLATES.keys())
        selected_styles = styles[:variants]
        result_variants = []
        for style in selected_styles:
            template = STYLE_TEMPLATES[style][0]
            subject = template.replace("{topic}", topic)
            bench = STYLE_BENCHMARKS[style]
            result_variants.append({
                "style": style,
                "subject_line": subject,
                "predicted_open_rate": f"{int(bench[\'open_rate\'][0]*100)}-{int(bench[\'open_rate\'][1]*100)}%",
                "predicted_click_rate": f"{int(bench[\'click_rate\'][0]*100)}-{int(bench[\'click_rate\'][1]*100)}%",
            })
        return {
            "topic": topic,
            "goal": goal,
            "variants": result_variants,
            "test_settings": {
                "min_sample_size_per_variant": 1000,
                "recommended_duration_hours": "24-48",
                "primary_metric": "open_rate",
                "secondary_metric": "click_rate",
            },
        }
'''

# analytics_engine.py
analytics_engine_py = '''
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


class AnalyticsEngine:
    BENCHMARKS = {
        "open_rate":        {"poor": 0.15, "average": 0.21, "good": 0.25, "excellent": 0.30},
        "click_rate":       {"poor": 0.02, "average": 0.035, "good": 0.05, "excellent": 0.07},
        "cto_rate":         {"poor": 0.10, "average": 0.15, "good": 0.20, "excellent": 0.25},
        "unsubscribe_rate": {"excellent": 0.001, "good": 0.003, "average": 0.005, "poor": 0.01},
        "bounce_rate":      {"excellent": 0.005, "good": 0.01, "average": 0.02, "poor": 0.05},
    }

    def _rate_metric(self, metric_name, value):
        b = self.BENCHMARKS.get(metric_name, {})
        if not b:
            return "unknown"
        if metric_name in ("unsubscribe_rate", "bounce_rate"):
            if value <= b["excellent"]: return "excellent"
            if value <= b["good"]: return "good"
            if value <= b["average"]: return "average"
            return "poor"
        else:
            if value >= b["excellent"]: return "excellent"
            if value >= b["good"]: return "good"
            if value >= b["average"]: return "average"
            return "poor"

    def create_report(self, campaign_name, metrics: NewsletterMetrics):
        delivery_rate = metrics.delivered / metrics.sent if metrics.sent else 0
        open_rate = metrics.opened / metrics.delivered if metrics.delivered else 0
        click_rate = metrics.clicked / metrics.delivered if metrics.delivered else 0
        cto_rate = metrics.clicked / metrics.opened if metrics.opened else 0
        unsubscribe_rate = metrics.unsubscribed / metrics.delivered if metrics.delivered else 0
        bounce_rate = metrics.bounced / metrics.sent if metrics.sent else 0
        spam_rate = metrics.spam_complaints / metrics.delivered if metrics.delivered else 0

        ratings = {
            "open_rate": self._rate_metric("open_rate", open_rate),
            "click_rate": self._rate_metric("click_rate", click_rate),
            "cto_rate": self._rate_metric("cto_rate", cto_rate),
            "unsubscribe_rate": self._rate_metric("unsubscribe_rate", unsubscribe_rate),
            "bounce_rate": self._rate_metric("bounce_rate", bounce_rate),
        }

        insights = []
        if ratings["open_rate"] == "poor":
            insights.append("打开率低于行业平均水平，建议优化主题行和发送时间")
        if ratings["click_rate"] == "poor":
            insights.append("点击率偏低，建议强化CTA和内容相关性")
        if ratings["bounce_rate"] == "poor":
            insights.append("退回率偏高，建议清理邮件列表")
        if ratings["unsubscribe_rate"] == "poor":
            insights.append("退订率偏高，建议检查发送频率和内容质量")
        if spam_rate > 0.001:
            insights.append("垃圾邮件投诉率偏高，请检查内容和发送策略")

        return {
            "campaign_name": campaign_name,
            "metrics": {
                "sent": metrics.sent,
                "delivered": metrics.delivered,
                "opened": metrics.opened,
                "clicked": metrics.clicked,
                "unsubscribed": metrics.unsubscribed,
                "bounced": metrics.bounced,
                "spam_complaints": metrics.spam_complaints,
            },
            "rates": {
                "delivery_rate": round(delivery_rate, 4),
                "open_rate": round(open_rate, 4),
                "click_rate": round(click_rate, 4),
                "cto_rate": round(cto_rate, 4),
                "unsubscribe_rate": round(unsubscribe_rate, 4),
                "bounce_rate": round(bounce_rate, 4),
                "spam_rate": round(spam_rate, 6),
            },
            "ratings": ratings,
            "insights": insights,
            "action_items": insights,
        }


@dataclass
class GrowthPeriod:
    period: str
    total_subscribers: int
    new_subscribers: int
    churned_subscribers: int
    sources: Dict[str, int] = field(default_factory=dict)


class GrowthTracker:
    def __init__(self):
        self.periods: List[GrowthPeriod] = []

    def add_period(self, period: str, total_subscribers: int, new_subscribers: int,
                   churned_subscribers: int, sources: Dict[str, int] = None):
        self.periods.append(GrowthPeriod(
            period=period,
            total_subscribers=total_subscribers,
            new_subscribers=new_subscribers,
            churned_subscribers=churned_subscribers,
            sources=sources or {},
        ))

    def get_growth_summary(self):
        if not self.periods:
            return {}
        net_growths = []
        growth_rates = []
        all_sources = {}
        for p in self.periods:
            net = p.new_subscribers - p.churned_subscribers
            net_growths.append(net)
            rate = net / p.total_subscribers if p.total_subscribers else 0
            growth_rates.append(rate)
            for src, cnt in p.sources.items():
                all_sources[src] = all_sources.get(src, 0) + cnt

        best_idx = net_growths.index(max(net_growths))
        worst_idx = net_growths.index(min(net_growths))

        return {
            "total_periods": len(self.periods),
            "start_subscribers": self.periods[0].total_subscribers,
            "end_subscribers": self.periods[-1].total_subscribers,
            "total_net_growth": sum(net_growths),
            "avg_net_growth_per_period": round(sum(net_growths) / len(net_growths), 1),
            "avg_growth_rate": round(sum(growth_rates) / len(growth_rates), 4),
            "best_period": self.periods[best_idx].period,
            "worst_period": self.periods[worst_idx].period,
            "source_totals": all_sources,
        }

    def project_growth(self, periods_ahead: int):
        if len(self.periods) < 3:
            raise ValueError("At least 3 periods of data are required for projection")
        recent = self.periods[-3:]
        avg_net = sum(p.new_subscribers - p.churned_subscribers for p in recent) / 3
        projections = []
        last_total = self.periods[-1].total_subscribers
        for i in range(1, periods_ahead + 1):
            last_total = last_total + avg_net
            projections.append({
                "period_offset": i,
                "projected_subscribers": round(last_total),
                "projected_net_growth": round(avg_net),
            })
        return projections
'''

main_py = '''#!/usr/bin/env python3
"""Newsletter Growth Hacker - Interactive Menu (non-interactive batch mode also supported)"""
import sys

def main():
    print("Newsletter Growth Hacker v1.0.0")
    print("Use individual modules for batch processing.")

if __name__ == "__main__":
    main()
'''

scripts_dir = os.path.join(WORKSPACE, "skills/newsletter-growth-hacker/scripts")
with open(os.path.join(scripts_dir, "subscriber_acquisition.py"), "w") as f:
    f.write(subscriber_acquisition_py)
with open(os.path.join(scripts_dir, "content_optimizer.py"), "w") as f:
    f.write(content_optimizer_py)
with open(os.path.join(scripts_dir, "analytics_engine.py"), "w") as f:
    f.write(analytics_engine_py)
with open(os.path.join(scripts_dir, "main.py"), "w") as f:
    f.write(main_py)

# ─── Messy Raw Input Data (what the agent must process) ──────────────────────

# 1. Historical growth data as a messy CSV (fields in odd order, extra blank lines, notes)
growth_csv = """# Q1 2026 Subscriber Growth Data - exported from CRM
# Note: sources are approximate

period,total,new,lost,src_organic,src_referral,src_paid,notes
2026-01,5100,310,48,140,95,75,Product launch push
2026-02,5362,298,36,130,108,60,Valentine campaign
2026-03,5624,330,68,155,112,63,End of quarter

# Do not edit above lines
"""

with open(os.path.join(WORKSPACE, "data/raw/q1_growth_data.csv"), "w") as f:
    f.write(growth_csv)

# 2. Campaign metrics as a messy JSON (field names differ slightly from NewsletterMetrics)
campaign_json = {
    "campaign": "Q1 March Digest",
    "date": "2026-03-15",
    "stats": {
        "emails_sent": 5624,
        "emails_delivered": 5501,
        "unique_opens": 1430,
        "unique_clicks": 264,
        "unsubscribes": 22,
        "hard_bounces": 89,
        "soft_bounces": 34,
        "spam_reports": 3
    },
    "notes": "Best performing campaign of Q1. Subject line: '5个技巧让你的Newsletter打开率翻倍'"
}

with open(os.path.join(WORKSPACE, "data/raw/march_campaign_stats.json"), "w") as f:
    json.dump(campaign_json, f, indent=2, ensure_ascii=False)

# 3. Q2 planning brief
q2_brief = """Q2 Newsletter Planning Brief
==============================
Next campaign topic: SaaS产品增长
Primary goal: 提升打开率
Required A/B test variants: 4
Target subscriber count by end of Q2: 7500
Key question: Based on Q1 growth, will we hit 7500 by June?
"""

with open(os.path.join(WORKSPACE, "data/raw/q2_planning_brief.txt"), "w") as f:
    f.write(q2_brief)

print("Workspace generated successfully.")
print(f"Scripts at: {scripts_dir}")
print(f"Raw data at: {os.path.join(WORKSPACE, 'data/raw/')}")