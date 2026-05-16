import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "workspace/projects/policy_research/2024/q1",
    "workspace/projects/policy_research/2024/q2",
    "workspace/projects/policy_research/archive/2023",
    "workspace/projects/debate_club/formats",
    "workspace/projects/debate_club/topics",
    "workspace/projects/debate_club/training",
    "workspace/tools/nlp",
    "workspace/tools/analysis",
    "workspace/reports/monthly",
    "workspace/reports/quarterly",
    "workspace/references",
    "workspace/config",
    "workspace/logs",
    "workspace/temp",
]

for d in dirs:
    os.makedirs(f"/{d}", exist_ok=True)

# Distractor files
distractors = {
    "/workspace/projects/policy_research/2024/q1/survey_results.csv": "respondent_id,age,opinion\n1,25,agree\n2,34,disagree\n3,45,neutral\n",
    "/workspace/projects/policy_research/2024/q2/draft_report.txt": "This is a draft policy report on demographic trends. Findings suggest mixed public opinion on mandatory social policies.",
    "/workspace/projects/policy_research/archive/2023/old_debate_notes.txt": "Oxford Union debate notes - 2023\nTopic: Should government mandate retirement age?\nResult: Motion defeated 52-48",
    "/workspace/projects/debate_club/formats/british_parliamentary.md": "# British Parliamentary Format\n## Overview\nFour teams: Opening Government, Opening Opposition, Closing Government, Closing Opposition\nEach team has 2 speakers...",
    "/workspace/projects/debate_club/formats/lincoln_douglas.md": "# Lincoln-Douglas Format\nOne-on-one debate format focusing on values...",
    "/workspace/projects/debate_club/topics/suggested_topics_2024.txt": "1. Technology and society\n2. Environmental policy\n3. Healthcare reform\n4. Education funding\n5. Immigration policy",
    "/workspace/projects/debate_club/training/argument_mapping.py": "# Argument mapping utility\ndef map_argument(claim, evidence, warrant):\n    return {'claim': claim, 'evidence': evidence, 'warrant': warrant}\n",
    "/workspace/tools/nlp/text_scorer.py": "# NLP scoring tool\ndef score_text(text):\n    words = text.split()\n    return min(10.0, len(words) / 10)\n",
    "/workspace/tools/analysis/bias_detector.py": "# Bias detection in argumentative text\ndef detect_bias(text):\n    bias_words = ['always', 'never', 'everyone', 'nobody']\n    return any(w in text.lower() for w in bias_words)\n",
    "/workspace/reports/monthly/jan_2024.txt": "Monthly report January 2024\nDebate sessions held: 4\nParticipants: 23\nTopics covered: AI ethics, climate policy",
    "/workspace/reports/quarterly/q1_2024_summary.json": json.dumps({"quarter": "Q1 2024", "debates": 12, "avg_score": 7.2, "top_topic": "AI regulation"}),
    "/workspace/references/oxford_union_history.txt": "The Oxford Union was founded in 1823 and is one of the world's most prestigious debating societies. Famous debates include...",
    "/workspace/config/app_config.yaml": "server:\n  host: localhost\n  port: 8080\nlogging:\n  level: INFO\ndebate:\n  default_language: zh-CN\n",
    "/workspace/logs/system.log": "2024-01-15 10:23:45 INFO Application started\n2024-01-15 10:24:01 INFO Debate session initialized\n2024-01-15 11:45:23 INFO Session completed\n",
    "/workspace/temp/scratch.txt": "TODO: review debate scoring criteria\nnote: check Oxford Union rules for POI acceptance rates",
}

for path, content in distractors.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# Create the task specification file
task_spec = {
    "task": "Oxford Union Debate Simulation",
    "topic_raw": "年轻人是否应当被强制要求服兵役",
    "institute": "国家政策研究院",
    "purpose": "在公开论坛前测试论证强度",
    "parameters": {
        "min_passing_score": 8.0,
        "max_rounds": 3
    },
    "output_files": {
        "transcript": "debate_transcript.md",
        "summary": "debate_summary.json"
    },
    "llm_endpoint": "http://localhost:9999/v1",
    "model": "mock-debate-model"
}

with open("/workspace/task_spec.json", 'w', encoding='utf-8') as f:
    json.dump(task_spec, f, ensure_ascii=False, indent=2)

# Create a partial/incomplete attempt (wrong format, missing sections) as a red herring
bad_attempt = """# 辩论记录

辩题：年轻人应当服兵役

正方说：服兵役有利于国家安全。
反方说：服兵役侵犯个人自由。

结论：双方各有道理。
"""
with open("/workspace/projects/debate_club/topics/previous_attempt.md", 'w', encoding='utf-8') as f:
    f.write(bad_attempt)

# Create a misleading config suggesting wrong parameters
wrong_config = {
    "debate_config": {
        "min_score": 6.0,
        "max_rounds": 5,
        "acceptance_rate": 0.5,
        "note": "这是旧版配置，已弃用"
    }
}
with open("/workspace/config/old_debate_config.json", 'w', encoding='utf-8') as f:
    json.dump(wrong_config, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print(f"Task spec written to /workspace/task_spec.json")