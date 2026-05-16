import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Create deeply nested distractor structure ---
distractor_dirs = [
    "project/src/models",
    "project/src/utils",
    "project/tests/unit",
    "project/tests/integration",
    "project/config/prod",
    "project/config/dev",
    "project/docs/internal",
    "project/data/raw",
    "project/data/processed",
    "project/scripts/deploy",
    "project/logs/archive",
    "project/i18n/zh",
    "project/i18n/en",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractor_files = {
    "project/src/models/dialogue_model.py": '# Placeholder model\nclass DialogueModel:\n    pass\n',
    "project/src/utils/tokenizer.py": '# Chinese tokenizer utility\ndef tokenize(text): return list(text)\n',
    "project/src/utils/formatter.py": '# Response formatter\ndef format_response(r): return r.strip()\n',
    "project/tests/unit/test_dialogue.py": 'def test_placeholder(): assert True\n',
    "project/tests/integration/test_api.py": '# Integration tests\ndef test_api(): pass\n',
    "project/config/prod/settings.json": json.dumps({"env": "prod", "lang": "zh", "mode": "roleplay"}, ensure_ascii=False, indent=2),
    "project/config/dev/settings.json": json.dumps({"env": "dev", "debug": True, "lang": "zh"}, ensure_ascii=False, indent=2),
    "project/docs/internal/style_notes.txt": "Internal notes: dialogue style for product.\nSee QA team for current active specs.\n",
    "project/data/raw/sample_dialogues.txt": "Sample raw dialogues for training.\nNot for QA use.\n",
    "project/data/processed/cleaned_dialogues.jsonl": '{"role":"user","content":"你好"}\n{"role":"assistant","content":"你好！"}\n',
    "project/scripts/deploy/run.sh": "#!/bin/bash\necho 'Deploy script'\n",
    "project/logs/archive/run_2024_01.log": "2024-01-01 INFO: Service started\n2024-01-01 INFO: Dialogue module loaded\n",
    "project/i18n/zh/strings.json": json.dumps({"greeting": "你好", "farewell": "再见"}, ensure_ascii=False, indent=2),
    "project/i18n/en/strings.json": json.dumps({"greeting": "Hello", "farewell": "Goodbye"}, indent=2),
    "project/src/models/response_shaper.py": (
        "# Shapes assistant responses for different modes\n"
        "MODES = ['normal', 'formal', 'roleplay']\n"
        "def shape(text, mode='normal'): return text\n"
    ),
}

for path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- Core task input file ---
# A multi-turn conversation log the agent must respond to.
# Each turn has an ID, the user's message, and a hint about what the correct response type should look like.
# Deliberately messy: uses real-world varied phrasing.

conversation_turns = [
    {
        "turn_id": 1,
        "user": "朕今日心情甚好，你来告诉朕，如何提升团队的工作效率？",
        "context_note": "User initiated imperial mode via 朕. Expects a minister-style advisory answer in Chinese."
    },
    {
        "turn_id": 2,
        "user": "朕要看当前项目的状态，给朕一份JSON，字段包括：project_name, status, priority。project_name是'凤凰计划', status是'进行中', priority是'高'。只要JSON。",
        "context_note": "Still in imperial mode. But the user explicitly requests ONLY a JSON object. No extra text."
    },
    {
        "turn_id": 3,
        "user": "朕想知道，遇到下属犯错时，朕该如何处置？",
        "context_note": "Still in imperial mode. Advisory answer expected. Do NOT use forbidden words like 您, 奴才, 平身, 宣."
    },
    {
        "turn_id": 4,
        "user": "朕命你速速汇报：团队士气如何？",
        "context_note": "Still in imperial mode. The user uses '汇报' directed at the assistant, but the assistant must NOT frame the response as if the emperor is reporting TO the minister. The minister reports to the emperor."
    },
    {
        "turn_id": 5,
        "user": "好了，不要这个模式了，正常说话吧，帮我列出三个提升团队士气的方法。",
        "context_note": "User exits imperial mode. Response must be plain normal assistant Chinese. No 臣, no 陛下."
    }
]

task_input_path = os.path.join(WORKSPACE, "conversation_turns.json")
with open(task_input_path, "w", encoding="utf-8") as f:
    json.dump(conversation_turns, f, ensure_ascii=False, indent=2)

# Also write a plain text version for readability
task_input_txt_path = os.path.join(WORKSPACE, "conversation_turns.txt")
with open(task_input_txt_path, "w", encoding="utf-8") as f:
    for turn in conversation_turns:
        f.write(f"=== Turn {turn['turn_id']} ===\n")
        f.write(f"User: {turn['user']}\n")
        f.write(f"Note: {turn['context_note']}\n\n")

# Write a task briefing file (business context only, no rules)
briefing_path = os.path.join(WORKSPACE, "task_briefing.txt")
with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(
        "Task Briefing — Dialogue QA Module\n"
        "===================================\n\n"
        "Our AI assistant product includes a specialized Chinese dialogue mode\n"
        "triggered by certain user cues. The QA team needs verified sample\n"
        "responses for the 5 conversation turns in conversation_turns.json.\n\n"
        "You must play the role of the AI assistant and produce one response\n"
        "per turn. Save all responses to a file named response_log.json in\n"
        "the following format:\n\n"
        "[\n"
        "  {\"turn_id\": 1, \"response\": \"...\"},\n"
        "  {\"turn_id\": 2, \"response\": \"...\"},\n"
        "  ...\n"
        "]\n\n"
        "The assistant has a detailed internal style guide (SKILL.md) that\n"
        "governs exactly how it should respond in each scenario. Consult it.\n"
        "The QA eval will strictly check conformance to that guide.\n"
    )

print("Workspace initialized successfully.")
print(f"Files created: conversation_turns.json, conversation_turns.txt, task_briefing.txt")
print(f"Distractor files: {len(distractor_files)}")