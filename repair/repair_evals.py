import json
import os
import re
import sys
import subprocess
from pathlib import Path
from openai import OpenAI

# ================= 配置区 =================
# 配置你的 Qwen3.5-27B 接口信息
API_BASE = "http://localhost:8300/v1"
MODEL_NAME = "Qwen3.5-27B"
API_KEY = "EMPTY"  # 如果是本地部署如vLLM，填EMPTY即可；如果有真实Key请替换

# 【关键修改】：将执行器替换为 agent_runner_terminus.py，并对齐其专属参数
# 1. 替换脚本绝对路径
# 2. 补充 --provider openai
# 3. 补充 --api-key 传参
# 4. 将 --max-turns 改为 terminus 支持的 --max-iterations
RUNNER_CMD_TEMPLATE = (
    'python /home/test/test12/shixuanwei/skill-llm-master_new/agent_runner_terminus.py '
    '--instance "{instance_dir}" '
    '--provider openai '
    '--api-base {api_base} '
    '--model {model} '
    f'--api-key {API_KEY} '
    '--max-iterations 30 '
    '--cleanup'
)

INSTANCES_DIR = Path("instances-openclaw-Browser-fix")
MAX_REPAIR_ATTEMPTS = 3 
# ==========================================

client = OpenAI(base_url=API_BASE, api_key=API_KEY)

REPAIR_SYSTEM_PROMPT = """
You are a Senior Benchmark Architect. Your goal is to make benchmark tasks robust and fair.

### DIAGNOSTIC HYPOTHESIS:
Analyze the "Failed Run Log" to find the ROOT CAUSE:
1. **Eval is too brittle?** (e.g., exact string matching, case sensitivity, rigid path checks).
2. **Prompt is ambiguous?** (e.g., missing filenames, JSON keys, or target directory).

### MANDATORY REPAIR RULES:
- If the Agent's logic was correct but the check failed -> **PRIORITIZE FIXING EVAL.PY**.
- Use `re.search(..., re.IGNORECASE)` and fuzzy matching in `eval.py`. 
- Only update the Prompt if there was a technical constraint the Agent couldn't have known.
- **NEVER** add hints about the solution logic to the Prompt.

### OUTPUT FORMAT:
<REASONING>
Briefly explain why you are fixing Eval, Prompt, or both.
</REASONING>

<PROMPT>
[Full updated prompt]
</PROMPT>

<EVAL>
[Full fixed eval.py code - RAW code only]
</EVAL>
"""

def extract_repair_data(text: str):
    if not text:
        return "", ""
    prompt_match = re.search(r"<PROMPT>\s*(.*?)\s*</PROMPT>", text, re.DOTALL | re.IGNORECASE)
    eval_match = re.search(r"<EVAL>\s*(.*?)\s*</EVAL>", text, re.DOTALL | re.IGNORECASE)
    reason_match = re.search(r"<REASONING>\s*(.*?)\s*</REASONING>", text, re.DOTALL | re.IGNORECASE)
    
    if reason_match:
        print(f"    🧠 分析结果: {reason_match.group(1).strip()}")
        
    new_prompt = prompt_match.group(1).strip() if prompt_match else ""
    new_eval = eval_match.group(1).strip() if eval_match else ""
    
    new_eval = re.sub(r"^```python\n?", "", new_eval)
    new_eval = re.sub(r"\n?```$", "", new_eval)
    return new_prompt, new_eval.strip()

def run_agent_and_get_log(instance_dir: Path) -> str:
    cmd = RUNNER_CMD_TEMPLATE.format(instance_dir=str(instance_dir), api_base=API_BASE, model=MODEL_NAME)
    print(f"    ▶ 运行测试...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=500)
        return result.stdout + "\n" + result.stderr
    except Exception as e:
        return f"Error: {e}"

def main():
    if not INSTANCES_DIR.exists():
        print("❌ 找不到 instances 目录")
        return

    # 1. 严格过滤：在最开始就剔除所有非 unsolvable 的实例
    all_dirs = [d for d in INSTANCES_DIR.iterdir() if d.is_dir() and (d / "task.json").exists()]
    unsolvable_instances = []
    
    for d in all_dirs:
        try:
            with open(d / "task.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get("filter_status") == "unsolvable":
                    unsolvable_instances.append(d)
        except:
            continue

    print(f"🔍 扫描完毕。总计 {len(all_dirs)} 个实例，其中 {len(unsolvable_instances)} 个为待修复状态。")

    for i, instance_dir in enumerate(unsolvable_instances, 1):
        print(f"[{i}/{len(unsolvable_instances)}] 抢救中: {instance_dir.name}")
        
        task_json_path = instance_dir / "task.json"
        eval_py_path = instance_dir / "eval" / "eval.py"
        
        with open(task_json_path, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
        
        # 2. 安全检查：如果状态在运行中变了，立即跳过
        if task_data.get("filter_status") != "unsolvable":
            print(f"    ⏭️ 跳过已修复实例。")
            continue

        # 3. 时光倒流（仅对 unsolvable 执行）
        backup_prompt_path = instance_dir / "prompt.bak.txt"
        backup_eval_path = instance_dir / "eval" / "eval.py.bak"

        if backup_eval_path.exists():
            eval_py_path.write_text(backup_eval_path.read_text(encoding="utf-8"), encoding="utf-8")
        if backup_prompt_path.exists():
            task_data["prompt"] = backup_prompt_path.read_text(encoding="utf-8")
        
        task_data["repair_attempts"] = 0
        task_json_path.write_text(json.dumps(task_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # 开始修复循环
        for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
            print(f"    🔄 Attempt {attempt}/{MAX_REPAIR_ATTEMPTS}")
            
            run_log = run_agent_and_get_log(instance_dir)
            (instance_dir / f"repair_run_trace_v{attempt}.log").write_text(run_log, encoding="utf-8", errors="replace")

            if re.search(r"Passed:\s*True", run_log, re.IGNORECASE):
                print("    🎉 [SUCCESS] 通过！状态 -> kept")
                task_data["filter_status"] = "kept"
                task_data["repair_attempts"] = attempt
                task_json_path.write_text(json.dumps(task_data, indent=2, ensure_ascii=False), encoding="utf-8")
                break 

            if attempt == MAX_REPAIR_ATTEMPTS:
                print("    ⚠️ [FAILED] 达到最大次数。")
                task_data["repair_attempts"] = attempt
                task_json_path.write_text(json.dumps(task_data, indent=2, ensure_ascii=False), encoding="utf-8")
                break

            # 准备双向修复
            old_eval_code = eval_py_path.read_text(encoding="utf-8")
            current_prompt = task_data.get("prompt", "")
            current_temp = min(0.1 + (attempt - 1) * 0.1, 0.6)
            
            # --- 日志截断逻辑 ---
            # Qwen 27B 的上下文通常只有 16k，如果日志太长会报错。
            # 采用“保留头尾”的策略：保留前 4000 字符和后 5000 字符。
            display_log = run_log
            if len(display_log) > 9000:
                display_log = display_log[:4000] + "\n\n...[MIDDLE LOG TRUNCATED TO PREVENT CONTEXT OVERFLOW]...\n\n" + display_log[-5000:]
            
            print(f"    🧠 模型双向诊断中 (Temp: {current_temp:.1f})...")
            
            user_msg = f"Failed Log:\n{display_log}\n\nPrompt:\n{current_prompt}\n\nEval.py:\n{old_eval_code}"
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "system", "content": REPAIR_SYSTEM_PROMPT}, {"role": "user", "content": user_msg}],
                    temperature=current_temp
                )
                new_prompt, new_eval = extract_repair_data(response.choices[0].message.content)
                
                if new_eval and new_prompt:
                    # 备份原始（仅首次）
                    if not backup_prompt_path.exists(): backup_prompt_path.write_text(current_prompt, encoding="utf-8")
                    if not backup_eval_path.exists(): backup_eval_path.write_text(old_eval_code, encoding="utf-8")
                    
                    # 物理写入
                    eval_py_path.write_text(new_eval, encoding="utf-8")
                    task_data["prompt"] = new_prompt
                    task_data["repair_attempts"] = attempt
                    task_json_path.write_text(json.dumps(task_data, indent=2, ensure_ascii=False), encoding="utf-8")
                    print("    ✅ 已同步更新 Prompt 和 Eval.py")
            except Exception as e:
                print(f"    ❌ 修复过程出错: {e}")
                continue
            
        print("=" * 60)

if __name__ == "__main__":
    main()