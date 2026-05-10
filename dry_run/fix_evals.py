import os
import re
import json
import argparse
import sys
import textwrap
from pathlib import Path
from openai import OpenAI
from datetime import datetime 

# 导入项目核心组件
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.sandbox import Sandbox
from src.evaluator import evaluate_in_container

# 升级版 Prompt，强制要求输出诊断和推理过程
SYSTEM_PROMPT = """You are an expert QA Engineer. Your goal is to fix a vulnerable `eval.py` that either mistakenly gives >0 scores during an "empty run", OR crashes and returns a -1.0 score.

REPAIR PROTOCOL:
1. Analyze the "Empty Run Log":
   - IF SCORE > 0: Identify which checks are leaking points and tighten the scoring logic.
   - IF SCORE == -1.0: Look for [Detail Error] or Tracebacks. The script crashed (e.g., FileNotFoundError). Your priority shifts to making it CRASH-PROOF.
2. CRASH PREVENTION (CRITICAL RULES):
   - ALWAYS use `os.path.exists()` before opening any file. If missing, cleanly output a 0.0 score JSON and `sys.exit(0)`.
   - Wrap the main evaluation logic in a massive `try...except Exception as e:` block. If ANY error occurs, catch it and return 0.0, putting `str(e)` in the details.
   - NEVER let the script print Python tracebacks to stdout. It MUST always output valid JSON and exit with code 0.
3. Keep the original proportional scoring logic (`passed_checks/total`) intact unless it's fundamentally flawed. Just wrap it in safe checks!

You MUST structure your response EXACTLY in the following format:

### ANALYSIS
(Explain why it got >0, or why it crashed and got -1.0)

### REASONING
(Explain how you are patching the loophole or preventing the crash)

### CODE
```python
(Your fully rewritten, crash-proof eval.py code goes here)
```
"""

def parse_llm_response(text: str):
    """使用正则分别提取：诊断分析、修复理由、Python代码"""
    code_pattern = r"```python\n(.*?)\n```"
    code_match = re.search(code_pattern, text, re.DOTALL)
    code = code_match.group(1).strip() if code_match else text.strip()

    analysis_pattern = r"### ANALYSIS\n(.*?)(?=### REASONING|### CODE)"
    analysis_match = re.search(analysis_pattern, text, re.DOTALL)
    analysis = analysis_match.group(1).strip() if analysis_match else "No analysis provided."

    reasoning_pattern = r"### REASONING\n(.*?)(?=### CODE)"
    reasoning_match = re.search(reasoning_pattern, text, re.DOTALL)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided."

    return analysis, reasoning, code

def run_empty_test(instance_dir: Path):
    """在沙箱中执行空载测试并返回详细日志和得分。增强了报错信息的抓取。"""
    sandbox = Sandbox()
    container_id = None
    try:
        # ✨ 核心改动 1：单独捕获 build 阶段的错误
        try:
            sandbox.build(str(instance_dir))
        except Exception as e:
            # 如果 build 失败，返回特有的 -2.0 分
            return f"Docker Build Failed: {e}", -2.0 
            
        container_id = sandbox.create(str(instance_dir))
        result = evaluate_in_container(str(instance_dir), container_id, sandbox)
        
        details = []
        if hasattr(result, 'details') and isinstance(result.details, list):
            for check in result.details:
                name = check.get('name') if isinstance(check, dict) else getattr(check, 'name', 'unknown')
                passed = check.get('passed') if isinstance(check, dict) else getattr(check, 'passed', False)
                detail = check.get('detail') if isinstance(check, dict) else getattr(check, 'detail', '')
                
                status = "❌ MISTAKENLY PASSED" if passed else "✅ FAILED"
                check_log = f"- {name}: {status}"
                if detail:
                    check_log += f"\n    [Detail Error]: {detail}"
                details.append(check_log)
        
        log = f"Empty Run Score: {result.score:.2f}\n" + "\n".join(details)
        return log, result.score
    except Exception as e:
        # 这个是运行阶段（比如 evaluate_in_container）的崩溃，保持 -1.0 分
        return f"Sandbox Framework Error: {e}", -1.0
    finally:
        if container_id:
            try: sandbox.destroy(container_id)
            except: pass

def fix_instance_with_retry(instance_dir: Path, client: OpenAI, model: str, max_attempts=3):
    instance_id = instance_dir.name
    eval_path = instance_dir / "eval" / "eval.py"
    task_path = instance_dir / "task.json"
    gen_input_path = instance_dir / "gen_inputs.py"
    thoughts_path = instance_dir / "eval" / "llm_thoughts.txt"
    orig_eval_path = instance_dir / "eval" / "eval.py.orig"

    if thoughts_path.exists():
        thoughts_path.unlink()

    print(f"\n🔍 [{instance_id}] 初始空载体检...")
    current_log, current_score = run_empty_test(instance_dir)
    
    # 1. 如果是 0 分，直接跳过
    if current_score == -2.0:
        print(f"  💀 Docker 环境构建失败 (依赖/系统问题)，直接放弃。")
        return "BUILD_FAILED"
        
    if current_score == 0.0:
        print(f"  ✅ 已经是 0 分，无需修复。")
        return "SKIPPED"
        
    # 💡 附加选项：如果你觉得一开始就是 -1 的原始脚本根本不值得修，可以取消下面两行的注释直接跳过
    # if current_score == -1.0:
    #     print(f"  💀 初始评测即崩溃 (-1分)，放弃修复。")
    #     return "SKIPPED_CRASH"

    # 2. 准备“读档”：确保存在 .orig 备份
    if not orig_eval_path.exists():
        original_eval = eval_path.read_text(encoding="utf-8", errors="ignore")
        orig_eval_path.write_text(original_eval)
        
    task_content = task_path.read_text(encoding="utf-8", errors="ignore")
    gen_input_content = gen_input_path.read_text(encoding="utf-8", errors="ignore") if gen_input_path.exists() else "None"

    history = []
    for attempt in range(1, max_attempts + 1):
        print(f"  🛠️ 第 {attempt} 次呼叫大模型开处方...")
        
        # ✨ 核心改动：每次让大模型开处方前，都强制把代码回滚到最原始的 eval.py
        # 这样它就不会在自己上一次瞎改（导致报错）的代码基础上继续错下去了
        if attempt > 1:
            print("  ♻️ 正在回滚到原始 eval.py 代码进行重新思考...")
        current_eval_code = orig_eval_path.read_text(encoding="utf-8", errors="ignore")
        
        user_prompt = f"""
Instance: {instance_id}
Task Goal: {task_content}
Existing Files: {gen_input_content}
Current Error Log (Score must be 0.0, but got {current_score}):
{current_log}

Original eval.py code (Needs fixing based on the error above):
{current_eval_code}
"""
        if history:
            user_prompt += f"\nNote: Previous attempts failed. The recent error was:\n{history[-1]}\nPlease analyze the Detail Error carefully and fix the original code."

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}],
                temperature=0.1
            )
            
            raw_content = response.choices[0].message.content
            analysis, reasoning, new_code = parse_llm_response(raw_content)
            
            print("\n" + "="*50)
            print("🩺 【AI 故障诊断】")
            print(textwrap.fill(analysis, width=80, initial_indent="    ", subsequent_indent="    "))
            print("\n💊 【AI 修复药方】")
            print(textwrap.fill(reasoning, width=80, initial_indent="    ", subsequent_indent="    "))
            print("="*50 + "\n")
            
            with open(thoughts_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*20} Attempt {attempt} {'='*20}\n")
                f.write(raw_content)
                f.write("\n")

            # 覆盖写入大模型给出的新代码
            eval_path.write_text(new_code, encoding="utf-8")
            
            print(f"  🧪 修复代码已写入，正在沙箱回测验证...")
            current_log, current_score = run_empty_test(instance_dir)
            
            if current_score == 0.0:
                print(f"  ✨ 验证通过！空载得分为 0.0。修复成功。")
                return "FIXED"
            else:
                print(f"  ⚠️ 修复不彻底，回测得分仍为 {current_score:.2f}。准备重试...")
                # 记录这次失败的日志，留给下一次 attempt 作为提示
                history.append(current_log)
                
        except Exception as e:
            print(f"  ❌ 修复过程出错: {e}")
            break

    # 超过最大次数还没修好，为了不污染原始环境，最后强行回滚回去
    print(f"  💀 达到最大尝试次数 ({max_attempts})，修复失败，回滚原始代码。")
    eval_path.write_text(orig_eval_path.read_text(encoding="utf-8", errors="ignore"))
    return "FAILED"

# ⚠️ 注意：记得确保文件最上面（import os 的地方）有这行：
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target_dir", type=str)
    parser.add_argument("--limit", type=int, default=0)
    # 新增：允许用户自定义日志文件名
    parser.add_argument("--log_file", type=str, default="repair_report.txt", 
                        help="日志文件名，将自动保存在 target_dir 目录下")
    args = parser.parse_args()

    client = OpenAI(api_key=os.environ.get("TERMINUS_FILTER_API_KEY"), 
                    base_url=os.environ.get("TERMINUS_FILTER_API_BASE"))
    model = os.environ.get("TERMINUS_FILTER_MODEL", "gpt-4o")

    stats = {"SKIPPED": 0, "FIXED": 0, "FAILED": 0, "BUILD_FAILED": 0}
    
    # ✨ 补上漏掉的这行！用来存具体每个实例跑成了什么样
    detailed_results = [] 
    
    target_path = Path(args.target_dir)

    for i, d in enumerate(sorted(target_path.iterdir())):
        if not d.is_dir(): continue
        if args.limit > 0 and i >= args.limit: break
        
        res = fix_instance_with_retry(d, client, model)
        stats[res] += 1
        
        # ✨ 补上这行！把结果存进列表里
        detailed_results.append(f"{d.name}: {res}")

    print(f"\n=== 批量修复任务报告 ===")
    print(f"总计处理: {sum(stats.values())} 个")
    print(f"✅ 成功修复: {stats['FIXED']} 个")
    print(f"⏭️ 已经是 0 分跳过: {stats['SKIPPED']} 个")
    print(f"💥 环境损坏跳过: {stats['BUILD_FAILED']} 个") 
    print(f"❌ 修复失败: {stats['FAILED']} 个")

    log_path = target_path / args.log_file
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=== Eval Repair Detailed Report ===\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model used: {model}\n")
            f.write("-" * 40 + "\n")
            f.write("\n".join(detailed_results))
            f.write("\n\n" + "-" * 40 + "\n")
            f.write(f"Summary: FIXED={stats['FIXED']}, SKIPPED={stats['SKIPPED']}, BUILD_FAILED={stats['BUILD_FAILED']}, FAILED={stats['FAILED']}\n")
        
        print(f"\n📝 详细名单已保存至: {log_path.absolute()}")
    except Exception as e:
        print(f"\n❌ 保存日志文件失败: {e}")

if __name__ == "__main__":
    main()