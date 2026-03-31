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
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from src.sandbox import Sandbox
from src.evaluator import evaluate_in_container
from src.schema import RunSummary
from src.prompts import load_prompt

SYSTEM_PROMPT = load_prompt("agent_system")

MAX_TURNS = 20
EXEC_TIMEOUT = 60
MAX_CONTEXT_TOKENS = 28000  # Leave room for generation within 32k context
MAX_OUTPUT_CHARS = 2000  # Truncate command output to avoid blowing context


def estimate_tokens(messages: list[dict]) -> int:
    """Rough token estimate: ~4 chars per token."""
    return sum(len(m.get("content", "")) for m in messages) // 4


def trim_messages(messages: list[dict], max_tokens: int) -> list[dict]:
    """Keep system + first user message + trim older turns from the middle."""
    if estimate_tokens(messages) <= max_tokens:
        return messages
    # Always keep: system (0), first user (1), and last 4 messages
    keep_start = messages[:2]
    keep_end = messages[-4:]
    trimmed = keep_start + [{"role": "user", "content": "[Earlier conversation trimmed to save context]"}] + keep_end
    # If still too long, truncate individual message contents
    while estimate_tokens(trimmed) > max_tokens and len(trimmed) > 3:
        trimmed.pop(2)  # Remove from middle
    return trimmed


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

        # Trim context if needed
        api_messages = trim_messages(messages, MAX_CONTEXT_TOKENS)

        # Call the model
        try:
            response = client.chat.completions.create(
                model=model,
                messages=api_messages,
                max_tokens=2048,
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

        # Feed output back to the model (truncated to avoid context overflow)
        truncated_output = output[:MAX_OUTPUT_CHARS]
        if len(output) > MAX_OUTPUT_CHARS:
            truncated_output += f"\n... [truncated, {len(output)} chars total]"
        messages.append({
            "role": "user",
            "content": f"Command output:\n```\n{truncated_output}\n```\nContinue with the task. If done, say TASK_COMPLETE.",
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
    parser.add_argument("--run-dir", help="Directory to save results (default: results/{model}_{timestamp})")
    parser.add_argument("--no-eval", action="store_true", help="Skip evaluation after agent run")
    parser.add_argument("--cleanup", action="store_true", help="Destroy container after evaluation")
    parser.add_argument("--verbose", action="store_true", default=True, help="Verbose output")
    args = parser.parse_args()

    global MAX_TURNS
    MAX_TURNS = args.max_turns

    # Resolve run output directory
    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_slug = args.model.replace("/", "_")
        run_dir = Path("results") / f"{model_slug}_{ts}"

    instance_dir = args.instance
    instance_id = Path(instance_dir).name

    # Check build_status — skip failed instances
    task_json_path = Path(instance_dir) / "task.json"
    if task_json_path.exists():
        task_data = json.loads(task_json_path.read_text())
        if task_data.get("build_status") == "failed":
            print(f"Skipping {instance_id}: build_status is 'failed'")
            sys.exit(0)
        # Skip filtered-out instances
        filter_status = task_data.get("filter_status", "")
        if filter_status in ("too_easy", "unsolvable"):
            print(f"Skipping {instance_id}: filter_status is '{filter_status}'")
            sys.exit(0)

    run_instance_dir = run_dir / instance_id
    run_instance_dir.mkdir(parents=True, exist_ok=True)

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

    # Save conversation to run directory
    conv_path = run_instance_dir / "conversation.json"
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

        # Save result to run directory
        result_path = run_instance_dir / "result.json"
        result_path.write_text(result.to_json())
        print(f"\nResult saved to {result_path}")

        # Update run summary
        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            summary = RunSummary.load(str(summary_path))
        else:
            summary = RunSummary(
                run_name=run_dir.name,
                model=args.model,
                api_base=args.api_base,
            )
        summary.update_from_result(result)
        summary.save(str(summary_path))
        print(f"Summary updated: {summary_path} (total={summary.total}, passed={summary.passed}, avg={summary.avg_score:.2f})")

    # Cleanup container if requested
    if args.cleanup:
        print(f"\nCleaning up container {container_id[:12]}...")
        sandbox.destroy(container_id)
        meta_path.unlink(missing_ok=True)
        print("Container removed.")


if __name__ == "__main__":
    main()
