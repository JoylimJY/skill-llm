import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create the templates directory with the custom (non-standard) template
os.makedirs(os.path.join(workspace, "templates"), exist_ok=True)

# CRITICAL: Template uses non-standard field names that differ from the SKILL.md examples
# This traps agents relying on pre-training/examples from the docs
template = {
    "raw_input": "string",
    "query_label": "string",
    "params": {}
}

with open(os.path.join(workspace, "templates", "default.json"), "w", encoding="utf-8") as f:
    json.dump(template, f, ensure_ascii=False, indent=2)

# Create distractor files to simulate a real messy project environment
os.makedirs(os.path.join(workspace, "templates", "archive"), exist_ok=True)
os.makedirs(os.path.join(workspace, "data", "raw"), exist_ok=True)
os.makedirs(os.path.join(workspace, "data", "processed"), exist_ok=True)
os.makedirs(os.path.join(workspace, "config"), exist_ok=True)
os.makedirs(os.path.join(workspace, "scripts"), exist_ok=True)
os.makedirs(os.path.join(workspace, "logs"), exist_ok=True)
os.makedirs(os.path.join(workspace, "output", "drafts"), exist_ok=True)

# Distractor: an old template with the "standard" field names from docs (to trap agents)
old_template = {
    "input": "string",
    "question_name": "string",
    "other": {}
}
with open(os.path.join(workspace, "templates", "archive", "legacy_template.json"), "w", encoding="utf-8") as f:
    json.dump(old_template, f, ensure_ascii=False, indent=2)

# Distractor: another old template
alt_template = {
    "user_query": "string",
    "intent": "string",
    "entities": [],
    "metadata": {}
}
with open(os.path.join(workspace, "templates", "archive", "v1_template.json"), "w", encoding="utf-8") as f:
    json.dump(alt_template, f, ensure_ascii=False, indent=2)

# Distractor: sample config files
config_data = {
    "api_endpoint": "https://api.example.com/v2/query",
    "timeout": 30,
    "retry_count": 3,
    "default_source": "all",
    "supported_sources": ["微博", "抖音", "头条", "人民网", "知乎"]
}
with open(os.path.join(workspace, "config", "api_config.json"), "w", encoding="utf-8") as f:
    json.dump(config_data, f, ensure_ascii=False, indent=2)

with open(os.path.join(workspace, "config", "app.json"), "w", encoding="utf-8") as f:
    json.dump({"env": "production", "log_level": "INFO", "version": "2.3.1"}, f)

# Distractor: raw data files
sample_queries = [
    "查询最近一周微博热点",
    "小米汽车舆情分析",
    "新能源汽车负面新闻top5"
]
with open(os.path.join(workspace, "data", "raw", "sample_queries.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(sample_queries))

with open(os.path.join(workspace, "data", "raw", "user_requests_20260304.csv"), "w", encoding="utf-8") as f:
    f.write("timestamp,user_id,query\n")
    f.write("2026-03-04 09:00:00,u001,查询微博舆情\n")
    f.write("2026-03-04 09:05:00,u002,最近7天新能源汽车新闻\n")

# Distractor: processed output examples (OLD format - to confuse)
old_output = {
    "input": "查询微博舆情",
    "question_name": "微博舆情查询",
    "other": {
        "source": "微博",
        "start_time": "2026-02-25 00:00:00",
        "end_time": "2026-03-04 23:59:59"
    }
}
with open(os.path.join(workspace, "data", "processed", "example_output_old_format.json"), "w", encoding="utf-8") as f:
    json.dump(old_output, f, ensure_ascii=False, indent=2)

# Distractor: scripts
with open(os.path.join(workspace, "scripts", "batch_convert.py"), "w", encoding="utf-8") as f:
    f.write("# Batch conversion script - NOT to be used for this task\n")
    f.write("# This script processes bulk NL queries from a CSV\n")
    f.write("import json\n\ndef convert_batch(file_path):\n    pass\n")

with open(os.path.join(workspace, "scripts", "validate_json.sh"), "w", encoding="utf-8") as f:
    f.write("#!/bin/bash\n# Validates JSON output files\njq . \"$1\" > /dev/null && echo 'Valid JSON' || echo 'Invalid JSON'\n")

# Distractor: logs
with open(os.path.join(workspace, "logs", "conversion_log_20260303.txt"), "w", encoding="utf-8") as f:
    f.write("[2026-03-03 10:00:01] INFO: Converted 45 queries\n")
    f.write("[2026-03-03 10:00:02] INFO: 2 errors encountered\n")
    f.write("[2026-03-03 10:00:02] ERROR: Invalid time format in query #12\n")

with open(os.path.join(workspace, "logs", "app.log"), "w", encoding="utf-8") as f:
    f.write("[2026-03-04 08:00:00] System started\n")

# Distractor: draft outputs
with open(os.path.join(workspace, "output", "drafts", "draft_result.json"), "w", encoding="utf-8") as f:
    json.dump({"status": "draft", "note": "incomplete conversion"}, f)

# THE ACTUAL TASK FILE: A conversation log the agent must process
# Fixed reference date: 2026-03-04
conversation_log = {
    "reference_date": "2026-03-04",
    "conversation": [
        {
            "turn": 1,
            "user_input": "帮我转成JSON：查询微博上最近7天关于新能源汽车的负面舆情top20"
        },
        {
            "turn": 2,
            "user_input": "改成本月"
        },
        {
            "turn": 3,
            "user_input": "换成人民网"
        }
    ],
    "instructions": "请根据对话历史，依次处理每一轮输入，生成对应的JSON输出文件。输出文件分别命名为 turn1_output.json、turn2_output.json、turn3_output.json。"
}

with open(os.path.join(workspace, "conversation_log.json"), "w", encoding="utf-8") as f:
    json.dump(conversation_log, f, ensure_ascii=False, indent=2)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")