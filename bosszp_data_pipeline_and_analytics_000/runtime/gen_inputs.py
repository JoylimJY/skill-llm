import os
import random
import csv

random.seed(42)

# --- Build directory structure with distractors ---
dirs = [
    "workspace/bosszp/bosszp/spiders",
    "workspace/bosszp/web/templates",
    "workspace/bosszp/web/static/js",
    "workspace/bosszp/web/static/css",
    "workspace/bosszp/logs",
    "workspace/bosszp/data/raw",
    "workspace/bosszp/data/processed",
    "workspace/bosszp/config",
    "workspace/bosszp/docs",
    "workspace/analytics",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "workspace/bosszp/bosszp/spiders/boss.py": """
import scrapy
class BossSpider(scrapy.Spider):
    name = 'boss'
    start_urls = ['https://www.zhipin.com/']
    def parse(self, response):
        pass
""",
    "workspace/bosszp/bosszp/settings.py": """
COOKIES_ENABLED = True
DOWNLOAD_DELAY = 2
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
]
ITEM_PIPELINES = {'bosszp.pipelines.BosszpPipeline': 300}
""",
    "workspace/bosszp/bosszp/items.py": """
import scrapy
class BosszpItem(scrapy.Item):
    job_name = scrapy.Field()
    job_area = scrapy.Field()
    job_salary = scrapy.Field()
    com_name = scrapy.Field()
    com_type = scrapy.Field()
    com_size = scrapy.Field()
    finance_stage = scrapy.Field()
    work_year = scrapy.Field()
    education = scrapy.Field()
    job_benefits = scrapy.Field()
""",
    "workspace/bosszp/bosszp/pipelines.py": """
class BosszpPipeline:
    def process_item(self, item, spider):
        return item
""",
    "workspace/bosszp/web/run.py": """
from flask import Flask
app = Flask(__name__)
@app.route('/')
def index():
    return 'Dashboard'
if __name__ == '__main__':
    app.run(port=8080)
""",
    "workspace/bosszp/web/templates/index.html": """
<!DOCTYPE html><html><body>
<div id='salary-chart'></div>
<div id='finance-pie'></div>
</body></html>
""",
    "workspace/bosszp/logs/scrapy.log": "2024-01-01 10:00:00 [scrapy] INFO: Spider opened\n2024-01-01 10:05:00 [scrapy] INFO: Closing spider (finished)\n",
    "workspace/bosszp/config/db.conf": "[mysql]\nhost=127.0.0.1\nport=3306\nuser=root\npassword=\ndatabase=bosszp\n",
    "workspace/bosszp/docs/README_internal.txt": "Internal notes: remember to set DOWNLOAD_DELAY to avoid bans.\n",
    "workspace/analytics/previous_report_2023.json": '{"note": "old report, do not use", "top_company": "ByteDance"}\n',
}
for path, content in distractor_files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# --- Generate messy raw CSV (the actual problem input) ---
# Intentionally dirty: mixed salary formats, extra whitespace, empty fields,
# inconsistent encoding markers, duplicate headers in middle of file, etc.

job_names = [
    "Python开发工程师", "数据分析师", "Java后端工程师", "产品经理",
    "前端开发工程师", "算法工程师", "测试工程师", "运维工程师",
    "UI设计师", "数据工程师", "机器学习工程师", "后端开发",
    "全栈工程师", "大数据工程师", "DevOps工程师"
]
areas = ["北京", "上海", "深圳", "杭州", "成都", "广州", "武汉", "南京"]
# Messy salary formats intentionally
salary_pool = [
    "15-25K·13薪", "20-35K", "10-18K·14薪", "25-40K·13薪",
    "8-15K", "30-50K·16薪", "12-20K", "18-30K·12薪",
    "40-60K·13薪", "6-10K", "50-80K", "22-38K·15薪",
    "  15-20K  ", "10K-20K", "面议"  # intentionally dirty entries
]
companies = [
    "字节跳动", "腾讯", "阿里巴巴", "美团", "滴滴", "京东",
    "百度", "华为", "网易", "小米", "快手", "拼多多",
    "字节跳动", "腾讯", "阿里巴巴", "美团", "百度"  # duplicates for top-10 count
]
com_types = ["上市公司", "民营企业", "外资企业", "国有企业", "合伙企业"]
com_sizes = ["10000人以上", "1000-9999人", "500-999人", "100-499人", "20-99人", "少于20人"]
finance_stages = ["已上市", "D轮及以上", "C轮", "B轮", "A轮", "天使轮", "不需要融资", "已上市", "已上市", "不需要融资"]
work_years_list = ["经验不限", "1-3年", "3-5年", "5-10年", "10年以上", "应届生"]
educations = ["本科", "硕士", "大专", "博士", "不限"]
benefits_pool = [
    "五险一金,年终奖,带薪年假",
    "弹性工作,股票期权,团队活动",
    "六险一金,补充医疗,餐补",
    "年终奖,带薪年假,免费班车",
    "弹性上下班,零食下午茶,健身房",
    "期权激励,技术分享,内推奖励",
    "绩效奖金,节日福利,定期体检",
    "",  # intentionally empty
    "   ",  # whitespace-only
]

random.seed(42)

rows = []
for i in range(120):
    row = {
        "岗位名称": random.choice(job_names),
        "岗位地区": random.choice(areas),
        "薪资": random.choice(salary_pool),
        "公司名称": random.choice(companies),
        "公司类型": random.choice(com_types),
        "公司规模": random.choice(com_sizes),
        "融资阶段": random.choice(finance_stages),
        "工作年限": random.choice(work_years_list),
        "学历": random.choice(educations),
        "福利标签": random.choice(benefits_pool),
    }
    rows.append(row)

fieldnames = ["岗位名称", "岗位地区", "薪资", "公司名称", "公司类型", "公司规模", "融资阶段", "工作年限", "学历", "福利标签"]

raw_csv_path = "workspace/bosszp/data/raw/output.csv"
with open(raw_csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for idx, row in enumerate(rows):
        writer.writerow(row)
        # Insert a duplicate/garbage header in the middle to make it messy
        if idx == 49:
            writer.writerow({k: k for k in fieldnames})  # fake header row mid-file

print("Generated messy raw CSV:", raw_csv_path)
print("Generated distractor files in workspace/bosszp/")
print("Workspace ready.")