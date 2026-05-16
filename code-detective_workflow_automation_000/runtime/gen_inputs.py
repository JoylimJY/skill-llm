import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep distractor directory structure ---
dirs = [
    "workspace/bot_engine/core",
    "workspace/bot_engine/handlers",
    "workspace/bot_engine/middleware",
    "workspace/renderer/templates",
    "workspace/renderer/tests/fixtures/old",
    "workspace/renderer/tests/snapshots",
    "workspace/qa/reference_data",
    "workspace/qa/scripts",
    "workspace/docs/internal",
    "workspace/logs/sessions",
    "workspace/config",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor: old broken fixture (wrong format)
old_fixture = {
    "session": "game_001",
    "messages": [
        {"text": "найди баг!", "from": "user"},
        {"text": "Выбери сложность", "from": "bot", "keyboard": ["Легко", "Средне", "Сложно"]},
    ]
}
with open("workspace/renderer/tests/fixtures/old/game_session_v1.json", "w") as f:
    json.dump(old_fixture, f, ensure_ascii=False, indent=2)

# Distractor: partial config
config = {
    "bot_name": "CodeDetective",
    "version": "2.1.0",
    "channels": ["telegram", "slack"],
    "scoring": {"base_points": 10, "bonus_multiplier": 1.5}
}
with open("workspace/config/bot_config.json", "w") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

# Distractor: renderer template (not what we want)
with open("workspace/renderer/templates/question_template.txt", "w") as f:
    f.write("🐛 Найди баг (вопрос {n}/{total}):\n\n```{lang}\n{code}\n```\n\n{question_text}")

# Distractor: snapshot from easy difficulty (to confuse)
easy_snapshot = {
    "action": "send",
    "channel": "telegram",
    "target": "user_12345",
    "message": "🐛 Найди баг (вопрос 1/3):\n\n```python\nx = 10\ny = 0\nresult = x / y\nprint(result)\n```\n\nЧто не так?",
    "buttons": [
        [{"text": "💡 Подсказка", "callback_data": "hint:q1"}],
        [{"text": "🔄 Пропустить", "callback_data": "skip:q1"}]
    ]
}
with open("workspace/renderer/tests/snapshots/easy_q1_snapshot.json", "w") as f:
    json.dump(easy_snapshot, f, ensure_ascii=False, indent=2)

# Distractor: incorrect scoring notes
with open("workspace/docs/internal/scoring_notes.txt", "w") as f:
    f.write("""DRAFT SCORING NOTES (NOT FINAL):
- Easy: +10 pts per bug
- Medium: +20 pts per bug  
- Hard: +30 pts per bug
XP = bugs_found * 150

NOTE: These are placeholder values, confirm with SKILL.md
""")

# Distractor: handler pseudocode
with open("workspace/bot_engine/handlers/game_handler.py", "w") as f:
    f.write("""# Placeholder - not implemented
def handle_difficulty_selection(user_id, difficulty):
    # TODO: implement
    pass

def handle_answer(user_id, answer_text):
    # TODO: implement  
    pass
""")

# Distractor: middleware stub
with open("workspace/bot_engine/middleware/auth.py", "w") as f:
    f.write("# Auth middleware stub\ndef check_user(uid): return True\n")

# Distractor: logs
with open("workspace/logs/sessions/session_20240101.log", "w") as f:
    f.write("[2024-01-01 10:00:00] user_99 started game EASY\n")
    f.write("[2024-01-01 10:01:00] user_99 answered q1: correct\n")
    f.write("[2024-01-01 10:02:00] user_99 game ended 3/3\n")

# Distractor: QA script (wrong approach)
with open("workspace/qa/scripts/validate_old.py", "w") as f:
    f.write("""import json
# OLD validation script - checks v1 format only
def validate(filepath):
    with open(filepath) as fp:
        data = json.load(fp)
    assert 'session' in data
    assert 'messages' in data
""")

# Distractor: another JSON with flat buttons (WRONG format - trap)
wrong_format_example = {
    "action": "send",
    "channel": "telegram", 
    "target": "user_99999",
    "message": "Example with wrong button format",
    "buttons": [
        {"text": "Button 1", "callback_data": "cb1"},
        {"text": "Button 2", "callback_data": "cb2"}
    ]
}
with open("workspace/qa/reference_data/wrong_format_example.json", "w") as f:
    json.dump(wrong_format_example, f, ensure_ascii=False, indent=2)

# Distractor: core engine file
with open("workspace/bot_engine/core/engine.py", "w") as f:
    f.write("""class BotEngine:
    def __init__(self, config):
        self.config = config
    
    def dispatch(self, event):
        raise NotImplementedError
""")

# THE ACTUAL TASK SPECIFICATION FILE - tells agent what to produce
task_spec = {
    "task": "generate_game_session_fixture",
    "description": "Generate a complete reference fixture JSON file for a 'Medium' difficulty Code Detective game session. The fixture will be used by the renderer QA pipeline to validate message rendering.",
    "requirements": {
        "difficulty": "medium",
        "total_questions": 3,
        "user_id": "user_77042",
        "scenario": "Player answers question 1 correctly, requests a hint on question 2 then answers correctly, and skips question 3 (answers wrong). Game ends.",
        "bugs_found": 2,
        "output_file": "medium_session_fixture.json"
    },
    "note": "The fixture must represent the full sequence of bot messages sent during the session, in order."
}
with open("workspace/qa/reference_data/task_spec.json", "w") as f:
    json.dump(task_spec, f, ensure_ascii=False, indent=2)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("workspace"):
    for file in files:
        print(f"  {os.path.join(root, file)}")