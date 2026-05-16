import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "interview_system/tools",
    "interview_system/phases",
    "interview_system/data",
    "interview_system/logs",
    "interview_system/config",
    "archive/old_sessions",
    "archive/templates",
    "scripts/utils",
    "docs/internal",
    "tmp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "archive/old_sessions/session_2024_01.json": json.dumps({"session_id": "old_001", "scores": [55, 60, 70]}),
    "archive/old_sessions/session_2024_02.json": json.dumps({"session_id": "old_002", "scores": [80, 85, 90, 75, 70]}),
    "archive/templates/report_template_v1.txt": "Old template - DEPRECATED\nDo not use.\n",
    "archive/templates/report_template_v2.txt": "Total: {total}\nGrade: TBD\n",
    "scripts/utils/db_migrator.py": "# Legacy migration script\n# DO NOT RUN\n",
    "scripts/utils/score_exporter.py": "# Export scores to CSV\n# Incomplete\n",
    "docs/internal/architecture_notes.txt": "System uses L1/L2/L3 layered architecture.\nSee SKILL.md for details.\n",
    "docs/internal/todo.txt": "- Fix scorer weights\n- Add more questions\n- Test anonymous mode\n",
    "tmp/scratch/debug_output.txt": "KeyError at line 42\nFix pending\n",
    "tmp/scratch/test_run.log": "[2024-01-01] Test run failed: missing profile\n",
    "interview_system/config/settings.json": json.dumps({
        "version": "1.0.0",
        "max_questions": 5,
        "followup_limit": 3,
        "pass_threshold": 60,
        "scoring": {"keyword_weight": 0.7, "logic_weight": 0.3}
    }),
    "interview_system/logs/system.log": "[INFO] System initialized\n[WARN] No active session\n",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── Question Bank ─────────────────────────────────────────────────────────────
question_bank = [
    {
        "id": "q001",
        "topic": "LLM基础",
        "difficulty": "medium",
        "type": "八股题",
        "content": "请解释 Transformer 中 Attention 机制的核心原理，并说明为什么使用缩放点积注意力（Scaled Dot-Product Attention）？",
        "key_points": ["query", "key", "value", "softmax", "缩放", "梯度稳定", "点积"],
        "tags": ["attention", "transformer", "LLM基础"]
    },
    {
        "id": "q002",
        "topic": "LLM微调",
        "difficulty": "medium",
        "type": "八股题",
        "content": "LoRA（Low-Rank Adaptation）的核心思路是什么？相比全量微调有何优势？",
        "key_points": ["低秩分解", "参数高效", "rank", "A矩阵", "B矩阵", "冻结预训练", "显存"],
        "tags": ["LoRA", "微调", "PEFT"]
    },
    {
        "id": "q003",
        "topic": "推理优化",
        "difficulty": "hard",
        "type": "实战题",
        "content": "vLLM 的 PagedAttention 机制解决了什么问题？请描述其核心设计。",
        "key_points": ["KV Cache", "碎片化", "分页", "显存利用率", "吞吐量", "虚拟内存"],
        "tags": ["vLLM", "推理", "KV Cache"]
    },
    {
        "id": "q004",
        "topic": "强化学习",
        "difficulty": "medium",
        "type": "八股题",
        "content": "简述 RLHF（人类反馈强化学习）的三个主要训练阶段。",
        "key_points": ["SFT", "奖励模型", "PPO", "人类标注", "偏好数据", "策略优化"],
        "tags": ["RLHF", "PPO", "强化学习"]
    },
    {
        "id": "q005",
        "topic": "RAG",
        "difficulty": "medium",
        "type": "实战题",
        "content": "RAG（检索增强生成）架构中，如何提高检索质量？列举至少三种优化策略。",
        "key_points": ["向量检索", "重排序", "chunk策略", "混合检索", "查询扩展", "嵌入模型"],
        "tags": ["RAG", "检索", "向量数据库"]
    }
]

with open(os.path.join(workspace, "interview_system/data/question_bank.json"), "w", encoding="utf-8") as f:
    json.dump(question_bank, f, ensure_ascii=False, indent=2)

# ── Resume Database (pre-seeded with one existing user) ──────────────────────
resume_db = {
    "profiles": {
        "张伟": {
            "name": "张伟",
            "tags": ["Python", "PyTorch", "LLM基础", "LLM微调", "RAG"],
            "history": [],
            "created_at": "2024-01-15"
        }
    }
}

with open(os.path.join(workspace, "interview_system/data/resume_db.json"), "w", encoding="utf-8") as f:
    json.dump(resume_db, f, ensure_ascii=False, indent=2)

# ── Tool: tool_resume_db.py ───────────────────────────────────────────────────
tool_resume_db = '''#!/usr/bin/env python3
"""
tool_resume_db - User profile CRUD operations
"""
import json
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/resume_db.json")

def _load():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def query_name(name):
    """Query profile by name. Returns profile dict or None."""
    db = _load()
    return db["profiles"].get(name, None)

def create_profile(name, tags):
    """Create a new user profile."""
    db = _load()
    db["profiles"][name] = {
        "name": name,
        "tags": tags,
        "history": [],
        "created_at": "2024-01-01"
    }
    _save(db)
    return db["profiles"][name]

def update_feedback(name, session_data):
    """Update user profile with interview session data."""
    db = _load()
    if name not in db["profiles"]:
        return False
    db["profiles"][name]["history"].append(session_data)
    _save(db)
    return True

def list_profiles():
    """List all profile names."""
    db = _load()
    return list(db["profiles"].keys())

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "query":
        print(json.dumps(query_name(sys.argv[2])))
    elif cmd == "list":
        print(json.dumps(list_profiles()))
'''

with open(os.path.join(workspace, "interview_system/tools/tool_resume_db.py"), "w", encoding="utf-8") as f:
    f.write(tool_resume_db)

# ── Tool: tool_kb_search.py ───────────────────────────────────────────────────
tool_kb_search = '''#!/usr/bin/env python3
"""
tool_kb_search - Knowledge base question retrieval
"""
import json
import os
import sys
import random

KB_PATH = os.path.join(os.path.dirname(__file__), "../data/question_bank.json")

def search(tags=None, difficulty=None, count=1, exclude_ids=None):
    """
    Search knowledge base for questions matching tags/difficulty.
    Returns list of question dicts.
    """
    with open(KB_PATH, "r", encoding="utf-8") as f:
        bank = json.load(f)
    
    exclude_ids = exclude_ids or []
    results = [q for q in bank if q["id"] not in exclude_ids]
    
    if tags:
        scored = []
        for q in results:
            overlap = len(set(q.get("tags", [])) & set(tags))
            if overlap > 0:
                scored.append((overlap, q))
        scored.sort(key=lambda x: -x[0])
        results = [q for _, q in scored] if scored else results
    
    if difficulty:
        filtered = [q for q in results if q.get("difficulty") == difficulty]
        if filtered:
            results = filtered
    
    random.shuffle(results[:max(count*2, 5)])
    return results[:count]

if __name__ == "__main__":
    tags = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    difficulty = sys.argv[2] if len(sys.argv) > 2 else None
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    print(json.dumps(search(tags, difficulty, count), ensure_ascii=False))
'''

with open(os.path.join(workspace, "interview_system/tools/tool_kb_search.py"), "w", encoding="utf-8") as f:
    f.write(tool_kb_search)

# ── Tool: tool_scorer.py ─────────────────────────────────────────────────────
tool_scorer = '''#!/usr/bin/env python3
"""
tool_scorer - Real-time answer scoring
Scoring: 70% keyword matching + 30% logic assessment
Pass threshold: 60
"""
import json
import sys
import re

def score(key_points, answer, logic_score=None):
    """
    Score an answer against key points.
    
    Args:
        key_points: list of keywords/concepts to check
        answer: candidate's answer text
        logic_score: optional override for logic score (0-30)
    
    Returns:
        dict with keyword_score, logic_score, total_score, passed
    """
    if not answer or answer.strip().lower() in ["跳过", "skip", ""]:
        return {
            "keyword_score": 0,
            "logic_score": 0,
            "total_score": 0,
            "passed": False,
            "skipped": True
        }
    
    answer_lower = answer.lower()
    matched = 0
    matched_keywords = []
    missing_keywords = []
    
    for kp in key_points:
        kp_lower = kp.lower()
        if kp_lower in answer_lower:
            matched += 1
            matched_keywords.append(kp)
        else:
            missing_keywords.append(kp)
    
    keyword_ratio = matched / len(key_points) if key_points else 0
    # keyword component: 0-70 points
    kw_score = round(keyword_ratio * 70)
    
    # logic score: 0-30 points (if not provided, estimate from answer quality)
    if logic_score is None:
        word_count = len(answer.split())
        if word_count < 10:
            lg_score = 5
        elif word_count < 30:
            lg_score = 15
        elif word_count < 60:
            lg_score = 22
        else:
            lg_score = 28
    else:
        lg_score = max(0, min(30, int(logic_score)))
    
    total = kw_score + lg_score
    
    return {
        "keyword_score": kw_score,
        "logic_score": lg_score, 
        "total_score": total,
        "passed": total >= 60,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "skipped": False
    }

if __name__ == "__main__":
    key_points = json.loads(sys.argv[1])
    answer = sys.argv[2] if len(sys.argv) > 2 else ""
    logic_score = int(sys.argv[3]) if len(sys.argv) > 3 else None
    result = score(key_points, answer, logic_score)
    print(json.dumps(result, ensure_ascii=False))
'''

with open(os.path.join(workspace, "interview_system/tools/tool_scorer.py"), "w", encoding="utf-8") as f:
    f.write(tool_scorer)

# ── Tool: tool_jd_matcher.py ──────────────────────────────────────────────────
tool_jd_matcher = '''#!/usr/bin/env python3
"""
tool_jd_matcher - JD matching analysis
"""
import json
import sys
import re

def match_jd(resume_tags, jd_text):
    """
    Match user profile against job description.
    Returns match report.
    """
    jd_lower = jd_text.lower()
    matched = []
    unmatched = []
    
    for tag in resume_tags:
        if tag.lower() in jd_lower:
            matched.append(tag)
        else:
            unmatched.append(tag)
    
    match_score = round(len(matched) / max(len(resume_tags), 1) * 100)
    
    return {
        "match_score": match_score,
        "core_strengths": matched,
        "areas_to_improve": unmatched,
        "recommendation": "建议重点加强" + "、".join(unmatched[:3]) if unmatched else "技术栈高度匹配"
    }

if __name__ == "__main__":
    tags = json.loads(sys.argv[1])
    jd = sys.argv[2]
    print(json.dumps(match_jd(tags, jd), ensure_ascii=False))
'''

with open(os.path.join(workspace, "interview_system/tools/tool_jd_matcher.py"), "w", encoding="utf-8") as f:
    f.write(tool_jd_matcher)

# ── Tool: tool_summary_generator.py ──────────────────────────────────────────
tool_summary_generator = '''#!/usr/bin/env python3
"""
tool_summary_generator - Generate structured interview report
Grade: S(90-100), A(80-89), B(70-79), C(60-69), D(<60)
"""
import json
import sys

GRADE_THRESHOLDS = [
    (90, "S", "优秀"),
    (80, "A", "良好"),
    (70, "B", "中等"),
    (60, "C", "及格"),
    (0,  "D", "需努力"),
]

def get_grade(avg_score):
    for threshold, grade, desc in GRADE_THRESHOLDS:
        if avg_score >= threshold:
            return grade, desc
    return "D", "需努力"

def generate(scores, profile_name, tags=None):
    """
    Generate interview summary report.
    
    Args:
        scores: list of per-question scores (0-100 each, exactly 5)
        profile_name: candidate name
        tags: skill tags
    
    Returns:
        structured report dict
    """
    if len(scores) != 5:
        raise ValueError(f"Expected exactly 5 scores, got {len(scores)}")
    
    total = sum(scores)
    avg = round(total / 5)
    grade, grade_desc = get_grade(avg)
    
    # Identify strong/weak areas by score
    strong = [i+1 for i, s in enumerate(scores) if s >= 70]
    weak = [i+1 for i, s in enumerate(scores) if s < 60]
    
    return {
        "candidate": profile_name,
        "total_score": total,
        "avg_score": avg,
        "grade": grade,
        "grade_description": grade_desc,
        "per_question_scores": scores,
        "strong_questions": strong,
        "weak_questions": weak,
        "tags": tags or [],
        "status": "TERMINATE: 任务圆满完成"
    }

if __name__ == "__main__":
    scores = json.loads(sys.argv[1])
    name = sys.argv[2] if len(sys.argv) > 2 else "匿名"
    tags = json.loads(sys.argv[3]) if len(sys.argv) > 3 else []
    report = generate(scores, name, tags)
    print(json.dumps(report, ensure_ascii=False, indent=2))
'''

with open(os.path.join(workspace, "interview_system/tools/tool_summary_generator.py"), "w", encoding="utf-8") as f:
    f.write(tool_summary_generator)

# ── Test Scenario File ────────────────────────────────────────────────────────
# This is the "messy input" the agent must process.
# It describes a complete interview session to simulate.

test_scenario = {
    "scenario_id": "TEST_SCENARIO_001",
    "description": "Automated interview simulation for candidate evaluation pipeline testing",
    "candidate": {
        "name": "李明",
        "is_new_user": True,
        "tags": ["Python", "PyTorch", "Transformer", "LoRA", "RAG", "RLHF", "vLLM"]
    },
    "jd_text": "招聘LLM算法工程师，要求熟悉Transformer架构，有LoRA/PEFT微调经验，了解RLHF和RAG技术，熟悉vLLM等推理框架。",
    "skip_jd_matching": False,
    "interview_answers": [
        {
            "question_index": 1,
            "answer": "Transformer的Attention机制通过query、key、value三个矩阵来计算注意力权重。首先用query和key做点积，然后除以根号dk进行缩放，防止梯度消失，最后通过softmax归一化后与value相乘。缩放的目的是为了梯度稳定。",
            "logic_score_override": 25
        },
        {
            "question_index": 2,
            "answer": "LoRA通过低秩分解来实现参数高效的微调。将权重更新分解为两个低秩矩阵A矩阵和B矩阵的乘积，秩rank远小于原始维度。训练时冻结预训练参数，只训练A和B，大幅减少显存占用和计算量。",
            "logic_score_override": 26
        },
        {
            "question_index": 3,
            "answer": "跳过",
            "logic_score_override": None
        },
        {
            "question_index": 4,
            "answer": "RLHF包含三个阶段：首先是SFT监督微调阶段，用人类标注数据训练；然后训练奖励模型，基于人类偏好数据学习评分；最后用PPO算法进行策略优化，让模型输出更符合人类偏好。",
            "logic_score_override": 24
        },
        {
            "question_index": 5,
            "answer": "RAG可以通过以下策略提升检索质量：优化向量检索使用更好的嵌入模型，使用重排序reranker提升精度，改进chunk策略控制文档粒度，使用混合检索结合关键词和语义检索，以及查询扩展技术。",
            "logic_score_override": 27
        }
    ],
    "expected_output_file": "interview_report.json"
}

with open(os.path.join(workspace, "test_scenario.json"), "w", encoding="utf-8") as f:
    json.dump(test_scenario, f, ensure_ascii=False, indent=2)

# ── Phase scripts (stubs the agent must wire together) ──────────────────────
phase_resume_manager = '''#!/usr/bin/env python3
"""
phase_resume_manager - Phase 1: Resume/Profile Management
Output signal: SUCCESS: 画像已就绪
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import the tool
from tool_resume_db import query_name, create_profile

def run(name, tags=None):
    profile = query_name(name)
    if profile:
        print(f"[Phase1] Found existing profile for: {name}")
        print(f"[Phase1] Tags: {profile[\'tags\']}")
    else:
        if not tags:
            print(f"[Phase1] New user {name}, no tags provided, using empty profile")
            tags = []
        profile = create_profile(name, tags)
        print(f"[Phase1] Created new profile for: {name}")
    
    print("SUCCESS: 画像已就绪")
    return profile

if __name__ == "__main__":
    import json
    name = sys.argv[1] if len(sys.argv) > 1 else "匿名"
    tags = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
    run(name, tags)
'''

with open(os.path.join(workspace, "interview_system/tools/phase_resume_manager.py"), "w", encoding="utf-8") as f:
    f.write(phase_resume_manager)

phase_interview_engine = '''#!/usr/bin/env python3
"""
phase_interview_engine - Phase 3: Interview Loop (5 questions)
Output signal: SUCCESS: 5轮面试结束
Constraints:
  - Exactly 5 questions
  - Max 3 followups per question
  - "跳过" answer → score = 0
  - scoring: 70% keyword + 30% logic
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tool_scorer import score as tool_score
from tool_kb_search import search as kb_search

def run_interview(candidate_answers, tags=None):
    """
    Simulate interview loop with provided answers.
    Returns list of 5 per-question scores.
    """
    # Get questions from KB
    questions = kb_search(tags=tags, count=5)
    # Ensure we have exactly 5 (pad if needed)
    all_q = kb_search(count=10)
    seen_ids = set()
    final_questions = []
    for q in questions:
        if q["id"] not in seen_ids:
            final_questions.append(q)
            seen_ids.add(q["id"])
    for q in all_q:
        if len(final_questions) >= 5:
            break
        if q["id"] not in seen_ids:
            final_questions.append(q)
            seen_ids.add(q["id"])
    final_questions = final_questions[:5]
    
    scores = []
    print("=" * 50)
    print("面试实战循环开始")
    print("=" * 50)
    
    for i, q in enumerate(final_questions):
        current = i + 1
        print(f"\\n🎯 第 {current}/5 题")
        print(f"【题目类型】{q.get(\'type\', \'未知\')}")
        print(f"【题目】{q[\'content\']}")
        
        # Get the answer for this question
        answer_data = candidate_answers[i] if i < len(candidate_answers) else {"answer": "跳过"}
        answer_text = answer_data.get("answer", "跳过")
        logic_override = answer_data.get("logic_score_override")
        
        # Detect skip
        if answer_text.strip() in ["跳过", "skip"]:
            result = {"keyword_score": 0, "logic_score": 0, "total_score": 0, "passed": False, "skipped": True}
            print(f"[跳过] 第{current}题跳过，记0分")
        else:
            result = tool_score(q["key_points"], answer_text, logic_override)
        
        q_score = result["total_score"]
        scores.append(q_score)
        
        print(f"\\n📊 本轮评分：")
        print(f"关键词得分: {result[\'keyword_score\']}/70")
        print(f"思路得分: {result[\'logic_score\']}/30")
        print(f"总分: {q_score}/100")
    
    print("\\nSUCCESS: 5轮面试结束")
    return scores

if __name__ == "__main__":
    answers = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    tags = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
    scores = run_interview(answers, tags)
    print(json.dumps(scores))
'''

with open(os.path.join(workspace, "interview_system/tools/phase_interview_engine.py"), "w", encoding="utf-8") as f:
    f.write(phase_interview_engine)

# ── Main orchestrator (deliberately incomplete / not wired) ──────────────────
# This is intentionally missing the full pipeline wiring;
# the agent must implement run_full_pipeline() by reading the SKILL.md.
main_orchestrator = '''#!/usr/bin/env python3
"""
main_orchestrator.py - L1 Total Dispatcher
Coordinates all phases of the interview simulation.

Usage:
    python main_orchestrator.py <scenario_file> <output_report_file>

Expected output:
    - JSON report saved to <output_report_file>
    - Console logs showing phase transitions with proper signals
    - Final signal: TERMINATE: 任务圆满完成
"""
import json
import sys
import os

# Add tools directory to path
TOOLS_DIR = os.path.join(os.path.dirname(__file__), "interview_system/tools")
sys.path.insert(0, TOOLS_DIR)

def run_full_pipeline(scenario_path, output_path):
    """
    Execute the full interview pipeline:
    Phase 1 -> (Phase 2 optional) -> Phase 3 -> Phase 4
    
    This function must:
    1. Load scenario from scenario_path
    2. Run Phase 1: Profile management (query or create user)
    3. Optionally run Phase 2: JD matching
    4. Run Phase 3: 5-question interview loop with proper scoring
       - 70% keyword + 30% logic scoring
       - "跳过" answers must score 0
       - Max 3 followups (already handled by engine)
    5. Run Phase 4: Generate summary report using tool_summary_generator
       - Use correct grade thresholds: S>=90, A>=80, B>=70, C>=60, D<60
       - Update resume DB with session data
    6. Save report to output_path
    7. Print TERMINATE: 任务圆满完成
    """
    # TODO: Implement the full pipeline
    pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main_orchestrator.py <scenario_file> <output_report_file>")
        sys.exit(1)
    
    scenario_file = sys.argv[1]
    output_file = sys.argv[2]
    run_full_pipeline(scenario_file, output_file)
'''

with open(os.path.join(workspace, "main_orchestrator.py"), "w", encoding="utf-8") as f:
    f.write(main_orchestrator)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")

# List all files
for root, dirs, files in os.walk(workspace):
    for file in files:
        full = os.path.join(root, file)
        rel = os.path.relpath(full, workspace)
        print(f"  {rel}")