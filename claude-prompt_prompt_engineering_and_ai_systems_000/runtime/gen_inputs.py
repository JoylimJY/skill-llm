import os
import random

random.seed(42)

base = "/workspace"

# --- Directory structure ---
dirs = [
    "project/prompts/drafts",
    "project/prompts/archive",
    "project/prompts/templates",
    "project/docs/clinical",
    "project/docs/api",
    "project/src/pipeline",
    "project/src/utils",
    "project/tests/prompt_tests",
    "project/configs",
    "project/logs",
    "project/data/samples",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- DISTRACTOR FILES ---

# 1. An old, bad draft prompt with anti-patterns
with open(os.path.join(base, "project/prompts/drafts/triage_v1_bad.txt"), "w") as f:
    f.write("""你是最好的AI助手，没有什么是你不知道的。
请帮我评估病人状态。
病人信息：{{patient_data}}
给我结果。
""")

# 2. Another bad draft - too vague, no structure
with open(os.path.join(base, "project/prompts/drafts/triage_v2_vague.txt"), "w") as f:
    f.write("""分析病人数据并告诉我你的想法。
{{data}}
用JSON输出。
""")

# 3. A partial attempt with broken XML
with open(os.path.join(base, "project/prompts/drafts/triage_v3_partial.xml"), "w") as f:
    f.write("""<context>
医疗分诊系统
</context>
<task>
评估病人紧急程度
<examples>
示例1：胸痛患者 -> 紧急
</examples>
""")

# 4. A notes file about the project requirements
with open(os.path.join(base, "project/docs/clinical/triage_requirements.md"), "w") as f:
    f.write("""# 医疗分诊AI助手需求文档

## 角色要求
- 该AI助手需要扮演一名具有20年急诊经验的主任医师
- 必须用中文回复
- 输出必须是严格的JSON格式
- 需要展示推理过程

## 输入格式
病人报告包括：
- 主诉 (chief_complaint)
- 生命体征 (vital_signs): 血压、心率、体温、血氧
- 症状描述 (symptoms)
- 既往病史 (medical_history)

## 输出要求
JSON包含：
- triage_level: 1(最紧急)-5(不紧急)
- primary_diagnosis: 初步诊断
- recommended_actions: 建议措施列表
- urgency_reasoning: 紧急程度理由

## 示例病例1
输入：
  主诉：剧烈胸痛，放射至左臂，持续20分钟
  生命体征：血压160/100，心率110，体温36.8，血氧97%
  症状：出汗、恶心
  既往史：高血压
输出JSON：
  triage_level: 1
  primary_diagnosis: "疑似急性心肌梗死"
  recommended_actions: ["立即心电图", "开通静脉通路", "通知心内科"]
  urgency_reasoning: "胸痛+左臂放射痛+高血压史高度提示ACS"

## 示例病例2
输入：
  主诉：轻微头痛，持续2小时
  生命体征：血压120/80，心率75，体温36.5，血氧99%
  症状：轻度头痛，无其他
  既往史：无
输出JSON：
  triage_level: 4
  primary_diagnosis: "普通头痛"
  recommended_actions: ["观察", "对症处理"]
  urgency_reasoning: "生命体征正常，症状轻微，无危险因素"
""")

# 5. API integration docs (distractor)
with open(os.path.join(base, "project/docs/api/claude_api_notes.md"), "w") as f:
    f.write("""# Claude API 集成笔记

API endpoint: https://api.anthropic.com/v1/messages
Model: claude-3-5-sonnet-20241022
Max tokens: 4096

## 消息结构
messages = [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}  # prefill
]

注意：system参数单独传入，不在messages数组里。
""")

# 6. A pipeline script (distractor)
with open(os.path.join(base, "project/src/pipeline/triage_pipeline.py"), "w") as f:
    f.write("""import json
import anthropic

def run_triage(patient_data: dict, prompt_template: str) -> dict:
    client = anthropic.Anthropic()
    # Load system prompt from template file
    with open('project/prompts/templates/triage_system_prompt.txt') as f:
        system_prompt = f.read()
    # Load full prompt template
    user_message = prompt_template.format(**patient_data)
    messages = [
        {"role": "user", "content": user_message}
    ]
    # Add prefill if defined in prompt_template_prefill.json
    try:
        with open('project/prompts/templates/triage_prefill.json') as pf:
            prefill = json.load(pf)
            messages.append(prefill)
    except FileNotFoundError:
        pass
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        system=system_prompt,
        messages=messages
    )
    return response
""")

# 7. Utility scripts (distractor)
with open(os.path.join(base, "project/src/utils/validator.py"), "w") as f:
    f.write("""def validate_triage_output(output: dict) -> bool:
    required_keys = ['triage_level', 'primary_diagnosis', 'recommended_actions', 'urgency_reasoning']
    return all(k in output for k in required_keys)
""")

# 8. Old archived prompt (distractor)
with open(os.path.join(base, "project/prompts/archive/v0_system.txt"), "w") as f:
    f.write("""You are a helpful medical assistant. Please help with patient triage.
Be accurate and helpful at all times.
""")

# 9. Test file (distractor)
with open(os.path.join(base, "project/tests/prompt_tests/test_cases.json"), "w") as f:
    import json
    json.dump([
        {"id": 1, "input": {"chief_complaint": "胸痛", "vital_signs": {"bp": "160/100", "hr": 110, "temp": 36.8, "spo2": 97}}, "expected_level": 1},
        {"id": 2, "input": {"chief_complaint": "头痛", "vital_signs": {"bp": "120/80", "hr": 75, "temp": 36.5, "spo2": 99}}, "expected_level": 4},
    ], f, ensure_ascii=False, indent=2)

# 10. Config file (distractor)
with open(os.path.join(base, "project/configs/model_config.json"), "w") as f:
    json.dump({"model": "claude-3-5-sonnet-20241022", "max_tokens": 4096, "temperature": 0}, f)

# 11. Log file (distractor)
with open(os.path.join(base, "project/logs/evaluation_log.txt"), "w") as f:
    f.write("2024-01-15 10:23:01 - Triage prompt v1 tested - accuracy: 62%\n")
    f.write("2024-01-16 14:05:33 - Triage prompt v2 tested - accuracy: 71%\n")
    f.write("2024-01-17 09:11:20 - Need better structured prompt with examples and reasoning\n")

# 12. Sample patient data (distractor)
with open(os.path.join(base, "project/data/samples/patient_sample.json"), "w") as f:
    json.dump({
        "chief_complaint": "{{chief_complaint}}",
        "vital_signs": "{{vital_signs}}",
        "symptoms": "{{symptoms}}",
        "medical_history": "{{medical_history}}"
    }, f, ensure_ascii=False, indent=2)

# 13. A note file explicitly stating what needs to be built
with open(os.path.join(base, "project/prompts/templates/BUILD_THIS.md"), "w") as f:
    f.write("""# 待构建

需要在此目录创建以下文件：
1. triage_system_prompt.txt  - 系统提示词
2. triage_user_template.txt  - 用户消息模板（含XML标签结构）
3. triage_prefill.json       - 预填充JSON

这些文件将被 pipeline 代码自动加载。
""")

print("Workspace generated successfully.")