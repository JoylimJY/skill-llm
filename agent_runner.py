"""
Agent Runner: Use Qwen model via OpenAI-compatible API to complete tasks
in Docker sandbox through multi-turn interaction.

Usage:
    python agent_runner.py --instance instances/pdf_merge_easy_000 \
        --api-base http://localhost:8100/v1 \
        --model Qwen/Qwen3-8B
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from openai import OpenAI
from src.sandbox import Sandbox
from src.evaluator import evaluate_in_container

SYSTEM_PROMPT = """\
You are an expert programming assistant working inside a Docker container with a Linux environment.
Your working directory is /workspace, which contains input files for the task.

You can execute commands by writing them inside a code block. Use one of these formats:

```bash
<your shell command here>
```

```python
<your python script here>
```

Rules:
- Execute ONE command/script at a time, then wait for the output before deciding what to do next.
- You can list files, read files, write scripts, install packages, etc.
- When you are DONE with the task, say exactly: TASK_COMPLETE
- Always start by listing files in /workspace to understand what's available.
- Think step by step. First understand the input files, then plan your approach, then execute.
- If a command fails, analyze the error and try a different approach.
- Make sure output files are in /workspace unless specified otherwise.
"""

MAX_TURNS = 20
EXEC_TIMEOUT = 60


def extract_code_block(text: str) -> tuple[str, str] | None:
    """Extract the first code block from model output.
    Returns (language, code) or None.
    """
    # Match ```lang\n...\n```
    pattern = r"```(bash|python|sh|shell)\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        lang = match.group(1)
        code = match.group(2).strip()
        if lang in ("sh", "shell"):
            lang = "bash"
        return lang, code
    return None


def run_in_container(sandbox: Sandbox, container_id: str, lang: str, code: str) -> str:
    """Execute code in the Docker container and return output."""
    if lang == "python":
        # Write python script to container and execute
        # Escape single quotes for bash
        escaped_code = code.replace("'", "'\\''")
        cmd = f"python3 -c '{escaped_code}'"
        # If code is complex, write to a temp file instead
        if len(code) > 200 or "'" in code:
            import base64
            b64 = base64.b64encode(code.encode()).decode()
            cmd = f'echo "{b64}" | base64 -d > /tmp/_agent_script.py && python3 /tmp/_agent_script.py'
    else:
        cmd = code

    try:
        output, exit_code = sandbox.exec(container_id, cmd, timeout=EXEC_TIMEOUT)
        if exit_code != 0:
            return f"[EXIT CODE: {exit_code}]\n{output}"
        return output if output.strip() else "[Command completed successfully with no output]"
    except Exception as e:
        return f"[EXECUTION ERROR]: {str(e)}"


def run_agent(
    instance_dir: str,
    api_base: str,
    model: str,
    container_id: str,
    sandbox: Sandbox,
    verbose: bool = True,
) -> list[dict]:
    """Run agent loop: model generates commands, we execute them in the sandbox."""

    # Load task
    task_json = json.loads((Path(instance_dir) / "task.json").read_text())
    task_prompt = task_json["prompt"]

    client = OpenAI(base_url=api_base, api_key="nokey")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Here is your task:\n\n{task_prompt}\n\nPlease complete this task. Start by exploring the workspace."},
    ]

    if verbose:
        print(f"\n{'='*60}")
        print(f"TASK: {task_prompt}")
        print(f"{'='*60}\n")

    for turn in range(MAX_TURNS):
        if verbose:
            print(f"\n--- Turn {turn + 1}/{MAX_TURNS} ---")

        # Call the model
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=4096,
                temperature=0.7,
            )
        except Exception as e:
            print(f"[API ERROR]: {e}")
            time.sleep(2)
            continue

        assistant_msg = response.choices[0].message.content
        if not assistant_msg:
            print("[EMPTY RESPONSE]")
            continue

        messages.append({"role": "assistant", "content": assistant_msg})

        if verbose:
            print(f"\n[ASSISTANT]:\n{assistant_msg[:1000]}{'...' if len(assistant_msg) > 1000 else ''}")

        # Check if task is complete
        if "TASK_COMPLETE" in assistant_msg:
            if verbose:
                print("\n✅ Agent reported TASK_COMPLETE")
            break

        # Extract and execute code block
        code_block = extract_code_block(assistant_msg)
        if code_block is None:
            # No code block - prompt model to continue
            messages.append({
                "role": "user",
                "content": "Please provide a command to execute (in a ```bash or ```python code block), or say TASK_COMPLETE if done.",
            })
            continue

        lang, code = code_block
        if verbose:
            print(f"\n[EXECUTING {lang}]:\n{code}")

        output = run_in_container(sandbox, container_id, lang, code)
        if verbose:
            print(f"\n[OUTPUT]:\n{output[:2000]}{'...' if len(output) > 2000 else ''}")

        # Feed output back to the model
        messages.append({
            "role": "user",
            "content": f"Command output:\n```\n{output[:4000]}\n```\nContinue with the task. If done, say TASK_COMPLETE.",
        })

    else:
        if verbose:
            print(f"\n⚠️ Agent reached max turns ({MAX_TURNS})")

    return messages


def main():
    parser = argparse.ArgumentParser(description="Run Qwen agent on SkillBench tasks")
    parser.add_argument("--instance", required=True, help="Path to instance directory")
    parser.add_argument("--api-base", default="http://localhost:8100/v1", help="vLLM API base URL")
    parser.add_argument("--model", default="Qwen/Qwen3-8B", help="Model name")
    parser.add_argument("--max-turns", type=int, default=20, help="Maximum interaction turns")
    parser.add_argument("--no-eval", action="store_true", help="Skip evaluation after agent run")
    parser.add_argument("--verbose", action="store_true", default=True, help="Verbose output")
    args = parser.parse_args()

    global MAX_TURNS
    MAX_TURNS = args.max_turns

    instance_dir = args.instance
    sandbox = Sandbox()

    # Check if container already exists
    meta_path = Path(instance_dir) / "container.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        container_id = meta["container_id"]
        print(f"Using existing container: {container_id[:12]}")
    else:
        # Build and create
        print("Building Docker image...")
        tag = sandbox.build(instance_dir)
        print(f"Creating container...")
        container_id = sandbox.create(instance_dir)
        meta_path.write_text(json.dumps({"container_id": container_id, "image_tag": tag}))
        print(f"Container ready: {container_id[:12]}")

    # Verify container is running
    output, exit_code = sandbox.exec(container_id, "ls /workspace")
    print(f"Workspace files: {output.strip()}")

    # Run agent
    print("\n" + "="*60)
    print("Starting agent interaction...")
    print("="*60)

    messages = run_agent(
        instance_dir=instance_dir,
        api_base=args.api_base,
        model=args.model,
        container_id=container_id,
        sandbox=sandbox,
        verbose=args.verbose,
    )

    # Save conversation
    conv_path = Path(instance_dir) / "conversation.json"
    conv_path.write_text(json.dumps(messages, indent=2, ensure_ascii=False))
    print(f"\nConversation saved to {conv_path}")

    # Evaluate
    if not args.no_eval:
        print("\n" + "="*60)
        print("Running evaluation...")
        print("="*60)

        result = evaluate_in_container(instance_dir, container_id, sandbox)
        print(f"\nResults for {result.instance_id}:")
        print(f"  Passed: {result.passed}")
        print(f"  Score:  {result.score:.2f}")
        if result.details:
            print("  Checks:")
            for check in result.details:
                status = "✅" if check.get("passed") else "❌"
                print(f"    {status} {check.get('name', '?')}: {check.get('detail', '')}")

        result_path = Path(instance_dir) / "result.json"
        result_path.write_text(result.to_json())
        print(f"\nResult saved to {result_path}")


if __name__ == "__main__":
    main()
