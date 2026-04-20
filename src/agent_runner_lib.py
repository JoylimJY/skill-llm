"""Library wrapper around agent_runner for use by src.filter.

Re-exports the core run_agent function so filter.py can call it
without importing the top-level agent_runner.py (which has module-level
side effects like loading prompts at import time).
"""

import json
import re
import time
import base64
from pathlib import Path

from openai import OpenAI

from .sandbox import Sandbox
from .prompts import load_prompt

_SYSTEM_PROMPT = None

MAX_TURNS = 20
EXEC_TIMEOUT = 60
MAX_CONTEXT_TOKENS = 28000
MAX_OUTPUT_CHARS = 2000


def _get_system_prompt() -> str:
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        _SYSTEM_PROMPT = load_prompt("agent_system")
    return _SYSTEM_PROMPT


def _estimate_tokens(messages: list[dict]) -> int:
    return sum(len(m.get("content", "")) for m in messages) // 4


def _trim_messages(messages: list[dict], max_tokens: int) -> list[dict]:
    if _estimate_tokens(messages) <= max_tokens:
        return messages
    keep_start = messages[:2]
    keep_end = messages[-4:]
    trimmed = keep_start + [{"role": "user", "content": "[Earlier conversation trimmed to save context]"}] + keep_end
    while _estimate_tokens(trimmed) > max_tokens and len(trimmed) > 3:
        trimmed.pop(2)
    return trimmed


def _extract_code_block(text: str) -> tuple[str, str] | None:
    pattern = r"```(bash|python|sh|shell)\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        lang = match.group(1)
        code = match.group(2).strip()
        if lang in ("sh", "shell"):
            lang = "bash"
        return lang, code
    return None


def _run_in_container(sandbox: Sandbox, container_id: str, lang: str, code: str) -> str:
    if lang == "python":
        if len(code) > 200 or "'" in code:
            b64 = base64.b64encode(code.encode()).decode()
            cmd = f'echo "{b64}" | base64 -d > /tmp/_agent_script.py && python3 /tmp/_agent_script.py'
        else:
            escaped_code = code.replace("'", "'\\''")
            cmd = f"python3 -c '{escaped_code}'"
    else:
        cmd = code

    try:
        output, exit_code = sandbox.exec(container_id, cmd, timeout=EXEC_TIMEOUT)
        if exit_code != 0:
            return f"[EXIT CODE: {exit_code}]\n{output}"
        return output if output.strip() else "[Command completed successfully with no output]"
    except Exception as e:
        return f"[EXECUTION ERROR]: {str(e)}"


def run_agent_in_container(
    instance_dir: str,
    api_base: str,
    model: str,
    container_id: str,
    sandbox: Sandbox,
    verbose: bool = False,
    max_turns: int = MAX_TURNS,
) -> list[dict]:
    """Run agent loop in a container. Returns conversation messages."""
    task_json = json.loads((Path(instance_dir) / "task.json").read_text())
    task_prompt = task_json["prompt"]

    client = OpenAI(base_url=api_base, api_key="nokey")

    messages = [
        {"role": "system", "content": _get_system_prompt()},
        {"role": "user", "content": f"Here is your task:\n\n{task_prompt}\n\nPlease complete this task. Start by exploring the workspace."},
    ]

    for turn in range(max_turns):
        api_messages = _trim_messages(messages, MAX_CONTEXT_TOKENS)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=api_messages,
                max_tokens=2048,
                temperature=0.7,
            )
        except Exception as e:
            if verbose:
                print(f"[API ERROR]: {e}")
            time.sleep(2)
            continue

        assistant_msg = response.choices[0].message.content
        if not assistant_msg:
            continue

        messages.append({"role": "assistant", "content": assistant_msg})

        # 1. 优先提取并执行代码块
        code_block = _extract_code_block(assistant_msg)
        if code_block:
            lang, code = code_block
            output = _run_in_container(sandbox, container_id, lang, code)

            truncated_output = output[:MAX_OUTPUT_CHARS]
            if len(output) > MAX_OUTPUT_CHARS:
                truncated_output += f"\n... [truncated, {len(output)} chars total]"
            
            messages.append({
                "role": "user",
                "content": f"Command output:\n```\n{truncated_output}\n```\nContinue with the task. If done, say TASK_COMPLETE.",
            })

        # 2. 代码执行完后，再检查是否需要结束任务
        if "TASK_COMPLETE" in assistant_msg:
            break

        # 3. 如果既没给代码，也没说完成，提醒模型
        if code_block is None and "TASK_COMPLETE" not in assistant_msg:
            messages.append({
                "role": "user",
                "content": "Please provide a command to execute (in a ```bash or ```python code block), or say TASK_COMPLETE if done.",
            })
            continue

    return messages