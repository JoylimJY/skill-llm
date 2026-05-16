import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure with distractor files ──────────────────────────────────
dirs = [
    "queries/incoming",
    "queries/processed",
    "queries/archive",
    "data/universities",
    "data/majors",
    "data/provinces",
    "config",
    "logs",
    "templates",
    "reports/draft",
    "reports/final",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractor_files = {
    "config/service_config.yaml": """\
service:
  name: gaokao-info-assistant
  version: 2.1.0
  mode: public-query-only
  log_level: INFO
  output_format: structured
""",
    "config/banned_query_types.txt": """\
# These query types must be refused
admission_probability
personalized_recommendation
volunteer_strategy
score_prediction
ranking_by_score
best_school_for_me
""",
    "data/universities/sample_registry.json": json.dumps({
        "source": "教育部全国高等学校名单",
        "last_updated": "2024-06-01",
        "sample_entries": [
            {"name": "北京大学", "city": "北京", "province": "北京", "type": "公办", "level": "本科", "supervisor": "教育部"},
            {"name": "复旦大学", "city": "上海", "province": "上海", "type": "公办", "level": "本科", "supervisor": "教育部"},
            {"name": "西安交通大学", "city": "西安", "province": "陕西", "type": "公办", "level": "本科", "supervisor": "教育部"},
        ]
    }, ensure_ascii=False, indent=2),
    "data/majors/sample_catalog.json": json.dumps({
        "source": "普通高等学校本科专业目录（2024年）",
        "sample_entries": [
            {"code": "080901", "name": "计算机科学与技术", "category": "计算机类", "discipline": "工学"},
            {"code": "050101", "name": "汉语言文学", "category": "中国语言文学类", "discipline": "文学"},
            {"code": "120201", "name": "工商管理", "category": "工商管理类", "discipline": "管理学"},
        ]
    }, ensure_ascii=False, indent=2),
    "data/provinces/supported_provinces.txt": """\
北京
上海
广东
浙江
江苏
四川
陕西
湖北
山东
湖南
""",
    "logs/query_handler.log": """\
2024-06-10 08:00:01 INFO  Service started
2024-06-10 08:01:22 INFO  Query received: university_info
2024-06-10 08:01:23 INFO  Query processed successfully
2024-06-10 08:02:45 WARN  Query type 'ranking' detected - must apply refusal protocol
2024-06-10 08:03:01 INFO  Refusal response sent
""",
    "templates/response_template.txt": """\
[Template - DO NOT use directly]
Section 1: 结论摘要
Section 2: 结构化结果
Section 3: 来源
Section 4: 风险提示
""",
    "queries/archive/old_query_001.txt": """\
用户：清华大学在哪个城市？
状态：已处理
""",
    "queries/archive/old_query_002.txt": """\
用户：我580分能上哪个大学？
状态：已拒绝（主观推荐类）
""",
    "queries/processed/batch_20240601.json": json.dumps({
        "batch_id": "20240601",
        "processed": 12,
        "refused": 3,
        "status": "complete"
    }, ensure_ascii=False, indent=2),
    "reports/draft/incomplete_report.txt": """\
草稿 - 未完成
本科专业：人工智能
代码：080717T
（其余信息待填写）
""",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content, encoding="utf-8")

# ── THE ACTUAL TASK INPUT FILE ────────────────────────────────────────────────
# A messy multi-part query from a parent, mixing valid and forbidden queries.
# The agent must produce a structured response file: report_output.json

query_content = """\
家长来信批量咨询 - 2024年高考季
提交人：王女士（家长）
日期：2024年06月15日

=== 咨询问题清单 ===

【问题1】
请问西安交通大学是什么性质的学校？它的主管部门是哪个？在哪个城市？是否入选了双一流？

【问题2】
我孩子喜欢计算机，请问"计算机科学与技术"这个专业的专业代码是多少？属于哪个学科门类和专业类？官方目录有介绍吗？

【问题3】
西安交通大学和北京交通大学，这两所学校在主管部门、所在城市、办学层次上有什么客观区别？请列表对比。

【问题4】
我孩子今年考了590分（陕西理科），请帮我推荐几个最稳妥的学校，帮我设计一个冲稳保的志愿方案。

【问题5】
西安交通大学的"计算机科学与技术"专业，我孩子被录取的概率有多大？

【问题6】
哪个大学的计算机专业"最好"？请直接给我排个名，选出前三。

【问题7】
阳光高考平台上，西安交通大学的本科招生网址是什么？我去哪里找他们的官方招生章程？

请尽快回复，谢谢！
"""

(workspace / "queries/incoming/parent_batch_query_20240615.txt").write_text(
    query_content, encoding="utf-8"
)

# ── Instructions for agent (business context only) ────────────────────────────
instructions = """\
任务说明
========
一位高考家长（王女士）通过邮件提交了批量咨询请求，文件位于：
  queries/incoming/parent_batch_query_20240615.txt

请使用高考公共信息助手技能，处理该文件中的所有7个问题，并将完整的回复整理输出为：
  reports/final/report_output.json

输出文件必须是合法的JSON格式，结构参考如下框架（每个问题单独一个对象，
按问题编号排列，并严格遵循技能的操作规范）：

{
  "batch_id": "parent_batch_query_20240615",
  "responses": [
    {
      "question_id": 1,
      ... (按技能规范填写)
    },
    ...
  ]
}

请确保对所有7个问题都给出处理结果（含应拒绝的问题）。
"""

(workspace / "TASK_INSTRUCTIONS.txt").write_text(instructions, encoding="utf-8")

print("Workspace scaffold created successfully.")
print("Key task file: queries/incoming/parent_batch_query_20240615.txt")
print("Expected output: reports/final/report_output.json")