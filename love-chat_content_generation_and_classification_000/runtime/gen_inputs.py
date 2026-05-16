import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Deep distractor directory structure ──────────────────────────────────────
distractor_dirs = [
    "app/frontend/components",
    "app/backend/models",
    "app/backend/routes",
    "config/env",
    "docs/api",
    "scripts/migrations",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/processed",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = {
    "app/frontend/components/ChatBubble.jsx": "// placeholder component\nexport default function ChatBubble() { return null; }",
    "app/frontend/components/ProfileCard.jsx": "// placeholder\nexport default function ProfileCard() {}",
    "app/backend/models/User.py": "class User:\n    pass\n",
    "app/backend/models/Conversation.py": "class Conversation:\n    pass\n",
    "app/backend/routes/auth.py": "# auth routes placeholder",
    "app/backend/routes/coaching.py": "# coaching routes placeholder",
    "config/env/.env.example": "DATABASE_URL=\nSECRET_KEY=\nOPENAI_API_KEY=",
    "config/env/settings.py": "DEBUG = False\nALLOWED_HOSTS = ['*']",
    "docs/api/openapi.yaml": "openapi: 3.0.0\ninfo:\n  title: Coaching API\n  version: 1.0.0",
    "scripts/migrations/001_create_users.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT);",
    "scripts/migrations/002_create_conversations.sql": "CREATE TABLE conversations (id SERIAL PRIMARY KEY, user_id INTEGER);",
    "tests/unit/test_models.py": "def test_placeholder(): assert True",
    "tests/integration/test_api.py": "def test_placeholder(): assert True",
    "data/raw/sample_export.csv": "id,name,age\n1,Alice,22\n2,Bob,25",
    "data/processed/cleaned.jsonl": '{"id":1,"name":"Alice"}\n{"id":2,"name":"Bob"}',
}
for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── Core scenario files (messy, realistic user inputs) ────────────────────────
# Scenario 1: 分手挽回 — user is 外向 学生党, in 分手/挽回 stage
scenario_1 = {
    "user_info": {
        "name": "小明",
        "age": 21,
        "identity": "在校大学生",
        "personality_notes": "喜欢开玩笑，话很多，朋友圈很活跃，很爱social",
        "gender": "male"
    },
    "target_info": {
        "name": "小美",
        "age": 20,
        "identity_notes": "同班同学",
        "personality_notes": "平时挺感性的，喜欢看言情小说，容易被感动"
    },
    "relationship_description": "我们交往了8个月，上周她说觉得我们不合适提了分手，我想把她追回来",
    "chat_log_excerpt": [
        {"from": "target", "msg": "我觉得我们在一起压力很大，还是分开吧"},
        {"from": "user", "msg": "为什么？我哪里做的不好"},
        {"from": "target", "msg": "没有什么特别的原因，就是感觉不对了"},
        {"from": "user", "msg": "你能给我一次机会吗"},
        {"from": "target", "msg": "……我需要冷静一下"}
    ],
    "user_question": "我要怎么把她追回来？我现在每天都在给她发消息",
    "extra_context": "分手三天了，对方已读不回"
}

# Scenario 2: 暧昧期 — user is 理性 职场老手, target is 内向
scenario_2 = {
    "user_info": {
        "name": "James",
        "age": 31,
        "identity": "互联网大厂高级工程师，工作五年",
        "personality_notes": "逻辑性很强，说话直接，做事有条理，但不太擅长表达情感",
        "gender": "male"
    },
    "target_info": {
        "name": "晓雯",
        "age": 28,
        "identity_notes": "同公司产品经理",
        "personality_notes": "性格比较内敛，不喜欢被催，需要慢慢升温，喜欢有深度的对话"
    },
    "relationship_description": "认识三个月了，一起吃过两次饭，感觉有点暧昧但还没挑明",
    "chat_log_excerpt": [
        {"from": "user", "msg": "今天那个需求评审你说的那个点很有意思"},
        {"from": "target", "msg": "哈哈谢谢，我也觉得那个逻辑可以优化"},
        {"from": "user", "msg": "你平时周末一般做什么"},
        {"from": "target", "msg": "宅在家看书或者出去走走，你呢"},
        {"from": "user", "msg": "我一般打球或者看技术博客"}
    ],
    "user_question": "感觉关系一直停在这个程度，怎么推进到约会阶段",
    "extra_context": "想约她周末出去但不知道怎么开口"
}

# Scenario 3: 搭讪 + 认识期 — user is 内向 学生党, complete cold-approach context
scenario_3 = {
    "user_info": {
        "name": "阿杰",
        "age": 19,
        "identity": "大一新生，刚进大学",
        "personality_notes": "比较内向，不太会主动，但很真诚，喜欢读书和听音乐",
        "gender": "male"
    },
    "target_info": {
        "name": "未知",
        "age": None,
        "identity_notes": "图书馆遇到的女生，一直在看同一本哲学书",
        "personality_notes": "看起来文静，专注，应该是个爱读书的人"
    },
    "relationship_description": "完全不认识，在图书馆见过三次，想要开口搭讪",
    "chat_log_excerpt": [],
    "user_question": "我想在图书馆搭讪她，但我不知道说什么，我比较内向，怕冷场",
    "extra_context": "我们都在看哲学类书籍，她今天在看加缪的《局外人》"
}

# Save scenario files (messy naming, in data/raw)
scenarios = {
    "data/raw/user_case_breakup_001.json": scenario_1,
    "data/raw/user_case_ambiguous_002.json": scenario_2,
    "data/raw/user_case_pickup_003.json": scenario_3,
}

for rel_path, data in scenarios.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── Task instruction file ────────────────────────────────────────────────────
task_instruction = {
    "task": "coaching_content_generation",
    "description": (
        "我们的恋爱coaching应用需要为以下三个真实用户案例生成结构化的指导内容。"
        "请读取 data/raw/ 目录下的三个案例文件，"
        "为每个案例生成专业的恋爱指导内容，并将所有结果保存到 coaching_responses.json 文件中。"
        "每个案例的响应结构必须与案例的实际情况（关系阶段、性格、需求类型）完全匹配。"
    ),
    "input_files": [
        "data/raw/user_case_breakup_001.json",
        "data/raw/user_case_ambiguous_002.json",
        "data/raw/user_case_pickup_003.json"
    ],
    "output_file": "coaching_responses.json",
    "notes": "请参考工作区中的 SKILL.md 来了解所需的内容结构和分类体系。"
}

with open(os.path.join(workspace, "task.json"), "w", encoding="utf-8") as f:
    json.dump(task_instruction, f, ensure_ascii=False, indent=2)

print("Workspace generation complete.")
print(f"Created {len(distractor_files)} distractor files across {len(distractor_dirs)} directories.")
print("Created 3 scenario files and 1 task.json.")