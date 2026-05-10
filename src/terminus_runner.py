"""
Terminus-2 Style Agent Runner for SkillLLM

This agent uses the terminus_2 strategy:
- JSON-format output with {analysis, plan, commands, task_complete}
- Keystroke-based command execution simulation
- Double-confirm task completion mechanism
- Better structured reasoning through analysis/plan fields

Supports multiple LLM providers:
- OpenAI-compatible API (vLLM, Ollama, etc.)
- Anthropic Claude API

Usage:
    # OpenAI-compatible API
    python agent_runner_terminus.py --instance instances/pdf_merge_easy_000 \
        --api-base http://localhost:8100/v1 \
        --model Qwen/Qwen3-8B

    # Anthropic Claude API
    python agent_runner_terminus.py --instance instances/pdf_merge_easy_000 \
        --provider claude \
        --model claude-sonnet-4-20250514

This can be used as a drop-in replacement for agent_runner.py to compare
different agent strategies on the same benchmark.
"""

import argparse
import json
import os
import sys
import time
import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

from .sandbox import Sandbox
from .evaluator import evaluate_in_container
from .schema import RunSummary
from .prompts import load_prompt


# ============================================================================
# JSON Parser (simplified from terminus_2)
# ============================================================================

def parse_terminus_response(response: str) -> dict:
    """
    Parse terminus JSON response with error recovery.
    
    Returns dict with keys:
        - analysis: str
        - plan: str
        - commands: list of (keystrokes, duration) tuples
        - task_complete: bool
        - error: str or None
        - warning: str or None
    """
    result = {
        "analysis": "",
        "plan": "",
        "commands": [],
        "task_complete": False,
        "error": None,
        "warning": None,
    }
    
    # Extract JSON object
    json_start = response.find("{")
    json_end = response.rfind("}") + 1
    
    if json_start == -1 or json_end == 0:
        result["error"] = "No JSON object found in response"
        return result
    
    json_str = response[json_start:json_end]
    
    # Try to parse
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        # Try to fix common issues
        # 1. Missing closing braces
        brace_diff = json_str.count("{") - json_str.count("}")
        if brace_diff > 0:
            json_str += "}" * brace_diff
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                result["error"] = f"Invalid JSON: {e}"
                return result
        else:
            result["error"] = f"Invalid JSON: {e}"
            return result
    
    # Validate required fields
    if "analysis" not in data:
        result["warning"] = "Missing 'analysis' field"
    else:
        result["analysis"] = data["analysis"]
    
    if "plan" not in data:
        result["warning"] = (result["warning"] + "; " if result["warning"] else "") + "Missing 'plan' field"
    else:
        result["plan"] = data["plan"]
    
    if "commands" not in data:
        result["error"] = "Missing required 'commands' field"
        return result
    
    # Parse commands
    commands_data = data.get("commands", [])
    if not isinstance(commands_data, list):
        result["error"] = "'commands' must be an array"
        return result
    
    for i, cmd in enumerate(commands_data):
        if not isinstance(cmd, dict):
            result["warning"] = (result["warning"] + "; " if result["warning"] else "") + f"Command {i+1} is not an object"
            continue
        if "keystrokes" not in cmd:
            result["warning"] = (result["warning"] + "; " if result["warning"] else "") + f"Command {i+1} missing 'keystrokes'"
            continue
        
        keystrokes = cmd["keystrokes"]
        duration = cmd.get("duration", 1.0)
        
        if not isinstance(duration, (int, float)):
            duration = 1.0
        
        result["commands"].append((keystrokes, float(duration)))
    
    # Parse task_complete
    task_complete = data.get("task_complete", False)
    if isinstance(task_complete, str):
        task_complete = task_complete.lower() in ("true", "1", "yes")
    result["task_complete"] = bool(task_complete)
    
    return result


# ============================================================================
# Terminal State Manager (Docker-based, no tmux)
# ============================================================================

class DockerTerminal:
    """
    Simulates a terminal session over Docker exec.
    
    Key differences from tmux-based approach:
    - No tmux installation required in container
    - Each command runs in fresh shell context
    - We track current directory manually
    """
    
    def __init__(self, sandbox: Sandbox, container_id: str):
        self.sandbox = sandbox
        self.container_id = container_id
        self.current_dir = "/workspace"
        self.history = []  # List of (command, output) tuples
        self.last_output = ""
    
    def execute(self, keystrokes: str, duration: float = 1.0, timeout: int = 60) -> str:
        """
        Execute keystrokes as a shell command.
        
        Args:
            keystrokes: Command to execute (may end with \n)
            duration: Suggested wait time (used as timeout hint)
            timeout: Max execution time in seconds
        
        Returns:
            Command output
        """
        # Strip trailing newline if present (we'll add it back via bash -c)
        cmd = keystrokes.replace("\\n", "\n").replace("\\r", "\r")
        cmd = cmd.rstrip("\n\r")
        
        # Handle special keys
        if cmd in ("C-c", "C-d"):
            # Can't really send Ctrl+C/Ctrl+D via docker exec
            # Just return current state
            return self._get_state()
        
        # Track directory changes
        cmd_stripped = cmd.strip()
        if cmd_stripped.startswith("cd "):
            target = cmd_stripped[3:].strip()
            if target == "..":
                self.current_dir = str(Path(self.current_dir).parent)
            elif target.startswith("/"):
                self.current_dir = target
            else:
                self.current_dir = str(Path(self.current_dir) / target)
            # Execute cd and verify
            output, exit_code = self.sandbox.exec(
                self.container_id,
                f"cd {self.current_dir} && pwd",
                timeout=timeout
            )
            if exit_code == 0:
                output = f"[Changed to {self.current_dir}]\n{output}"
        else:
            # Execute command in current directory
            full_cmd = f"cd {self.current_dir} && {cmd}"
            output, exit_code = self.sandbox.exec(
                self.container_id,
                full_cmd,
                timeout=max(timeout, int(duration) + 10)
            )
            if exit_code != 0:
                output = f"[EXIT CODE: {exit_code}]\n{output}"
        
        self.last_output = output
        self.history.append((cmd, output))
        
        return output
    
    def _get_state(self) -> str:
        """Get current terminal state (pwd + recent files)."""
        output, _ = self.sandbox.exec(
            self.container_id,
            f"cd {self.current_dir} && echo '[PWD: $(pwd)]' && ls -la 2>/dev/null || true",
            timeout=10
        )
        return output
    
    def get_terminal_state(self, include_last_output: bool = True) -> str:
        """
        Get formatted terminal state for the LLM prompt.
        """
        parts = []
        
        if include_last_output and self.last_output:
            parts.append(f"Last command output:\n```\n{self.last_output[:3000]}\n```")
        
        parts.append(f"\nCurrent directory: {self.current_dir}")
        
        # Get file listing
        files_output, _ = self.sandbox.exec(
            self.container_id,
            f"cd {self.current_dir} && ls -la",
            timeout=10
        )
        parts.append(f"\nFiles:\n```\n{files_output[:1000]}\n```")
        
        return "\n".join(parts)


# ============================================================================
# LLM Client Abstraction
# ============================================================================

class LLMClient:
    """Unified LLM client interface supporting multiple providers."""
    
    def __init__(
        self,
        provider: Literal["openai", "claude"],
        model: str,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = provider
        self.model = model
        
        if provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(
                base_url=api_base or "http://localhost:8100/v1",
                api_key="***REMOVED***" or "nokey",
                http_client=httpx.Client(verify=False)
            )
        elif provider == "claude":
            from anthropic import Anthropic
            api_key = api_key or os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
            if not api_key:
                raise ValueError("Claude API key required. Set ANTHROPIC_AUTH_TOKEN or pass --api-key.")
            self._client = Anthropic(
                api_key=api_key,
                base_url=api_base or os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Call the LLM and return the response text."""
        
        if self.provider == "openai":
            # OpenAI-style: system message in messages list
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            response = self._client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        
        elif self.provider == "claude":
            # Claude-style: system prompt is separate, messages must alternate user/assistant
            claude_messages = self._prepare_claude_messages(messages)
            response = self._client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=claude_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.content[0].text or ""
        
        raise ValueError(f"Unknown provider: {self.provider}")
    
    def _prepare_claude_messages(self, messages: list[dict]) -> list[dict]:
        """
        Prepare messages for Claude API.
        
        Claude requires:
        - First message must be user
        - Roles must alternate between user and assistant
        """
        # Filter out system messages (handled separately)
        filtered = [m for m in messages if m["role"] != "system"]
        
        if not filtered:
            return filtered
        
        # Ensure first message is user
        if filtered[0]["role"] != "user":
            filtered = [{"role": "user", "content": "[Conversation start]"}] + filtered
        
        # Merge consecutive same-role messages
        result = []
        for msg in filtered:
            if result and result[-1]["role"] == msg["role"]:
                # Merge with previous message
                result[-1]["content"] += f"\n\n{msg['content']}"
            else:
                result.append(msg)
        
        # Ensure alternating roles
        final = []
        for msg in result:
            if final and final[-1]["role"] == msg["role"]:
                # Insert a placeholder message to alternate
                if msg["role"] == "user":
                    final.append({"role": "assistant", "content": "[Continuing...]"})
                else:
                    final.append({"role": "user", "content": "[Continuing...]"})
            final.append(msg)
        
        return final


# ============================================================================
# Main Agent Loop
# ============================================================================

MAX_ITERATIONS = 30
MAX_CONTEXT_TOKENS = 11000  # For OpenAI-compatible
MAX_CONTEXT_TOKENS_CLAUDE = 80000  # Claude has larger context


def estimate_tokens(messages: list[dict]) -> int:
    """Rough token estimate: ~4 chars per token."""
    return sum(len(str(m.get("content", ""))) for m in messages) // 4


def trim_messages(messages: list[dict], max_tokens: int) -> list[dict]:
    """Trim older messages to stay within token limit."""
    if estimate_tokens(messages) <= max_tokens:
        return messages
    
    # Keep system + first user + last 6 messages
    keep_start = messages[:2]
    keep_end = messages[-6:]
    
    trimmed = keep_start + [
        {"role": "user", "content": "[Earlier conversation trimmed to save context]"}
    ] + keep_end
    
    return trimmed


def run_terminus_agent(
    instance_dir: str,
    llm_client: LLMClient,
    container_id: str,
    sandbox: Sandbox,
    max_iterations: int = MAX_ITERATIONS,
    verbose: bool = True,
) -> list[dict]:
    """
    Run the terminus_2 style agent loop.
    
    Key differences from standard agent_runner:
    1. JSON output format with analysis/plan/commands
    2. Double-confirm task completion (must be True twice)
    3. Keystroke-based command execution
    """
    
    # Load task
    task_json = json.loads((Path(instance_dir) / "task.json").read_text())
    task_prompt = task_json["prompt"]
    
    terminal = DockerTerminal(sandbox, container_id)
    
    # Load prompts from unified prompt files
    system_prompt = load_prompt("terminus_system")
    
    # Build initial message using template
    initial_state = terminal.get_terminal_state(include_last_output=False)
    initial_message = load_prompt(
        "terminus_task",
        instruction=task_prompt,
        # The code `terminal_state` in Python is creating a variable named `terminal_state`. This
        # variable can be used to store a value or object that represents the state of a terminal in a
        # program or system.
        terminal_state=initial_state,
        additional_instruction="Please complete this task. Start by exploring the workspace and understanding what needs to be done. Remember to format your response as JSON with analysis, plan, commands, and task_complete fields."
    )
    
    messages = [
        {"role": "user", "content": initial_message},
    ]
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"TASK: {task_prompt}")
        print(f"{'='*60}\n")
    
    task_complete_count = 0
    max_tokens = MAX_CONTEXT_TOKENS_CLAUDE if llm_client.provider == "claude" else MAX_CONTEXT_TOKENS
    
    for iteration in range(max_iterations):
        if verbose:
            print(f"\n--- Iteration {iteration + 1}/{max_iterations} ---")
        
        # Trim context
        api_messages = trim_messages(messages, max_tokens)
        
        # Call LLM
        try:
            assistant_msg = llm_client.chat(
                messages=api_messages,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.7,
            )
        except Exception as e:
            print(f"[API ERROR]: {e}")
            time.sleep(2)
            continue
        
        if not assistant_msg:
            print("[EMPTY RESPONSE]")
            continue
        
        messages.append({"role": "assistant", "content": assistant_msg})
        
        if verbose:
            # Print parsed analysis/plan if available
            preview = assistant_msg[:500]
            print(f"\n[ASSISTANT]:\n{preview}{'...' if len(assistant_msg) > 500 else ''}")
        
        # Parse response
        parsed = parse_terminus_response(assistant_msg)
        
        if parsed["error"]:
            if verbose:
                print(f"[PARSE ERROR]: {parsed['error']}")
            messages.append({
                "role": "user",
                "content": f"Your response had a JSON parsing error: {parsed['error']}\n\nPlease fix your JSON format and try again. Remember to include 'analysis', 'plan', and 'commands' fields."
            })
            continue
        
        if parsed["warning"] and verbose:
            print(f"[WARNING]: {parsed['warning']}")
        
        # Check task completion (double-confirm)
        if parsed["task_complete"]:
            task_complete_count += 1
            if task_complete_count >= 2:
                if verbose:
                    print("\n✅ Task marked as complete (confirmed twice)")
                break
            if verbose:
                print("✓ Task marked as complete (first confirmation)")
        else:
            task_complete_count = 0
        
        # Show analysis and plan
        if verbose and parsed["analysis"]:
            print(f"\n[ANALYSIS]: {parsed['analysis'][:200]}...")
        if verbose and parsed["plan"]:
            print(f"[PLAN]: {parsed['plan'][:200]}...")
        
        # Execute commands
        if not parsed["commands"]:
            # No commands = wait and get state
            time.sleep(1.0)
            state = terminal.get_terminal_state()
            messages.append({
                "role": "user",
                "content": f"No commands to execute.\n\n{state}"
            })
            continue
        
        outputs = []
        for keystrokes, duration in parsed["commands"]:
            if verbose:
                cmd_preview = keystrokes.rstrip("\n")[:80]
                print(f"\n[EXECUTING]: {cmd_preview}{'...' if len(keystrokes) > 80 else ''}")
            
            output = terminal.execute(keystrokes, duration)
            outputs.append(output)
            
            if verbose:
                out_preview = output[:500]
                print(f"[OUTPUT]:\n{out_preview}{'...' if len(output) > 500 else ''}")
        
        # Feed output back
        combined_output = "\n".join(outputs)
        if len(combined_output) > 2000:
            combined_output = combined_output[:2000] + f"\n... [truncated, {len(combined_output)} chars total]"
        
        state = terminal.get_terminal_state(include_last_output=False)
        messages.append({
            "role": "user",
            "content": f"Command output:\n```\n{combined_output}\n```\n\n{state}\n\nContinue with the task. If fully complete, set task_complete to true."
        })
    
    else:
        if verbose:
            print(f"\n⚠️ Agent reached max iterations ({max_iterations})")
    
    # Return with system prompt for logging
    return [{"role": "system", "content": system_prompt}] + messages


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Run Terminus-2 style agent on SkillBench tasks")
    parser.add_argument("--instance", required=True, help="Path to instance directory")
    parser.add_argument(
        "--provider",
        choices=["openai", "claude"],
        default="openai",
        help="LLM provider (default: openai)"
    )
    parser.add_argument("--model", default="Qwen/Qwen3-8B", help="Model name")
    parser.add_argument("--api-base", help="API base URL (for OpenAI-compatible APIs)")
    parser.add_argument("--api-key", help="API key (or set ANTHROPIC_AUTH_TOKEN for Claude)")
    parser.add_argument("--max-iterations", type=int, default=50, help="Maximum iterations")
    parser.add_argument("--run-dir", help="Directory to save results")
    parser.add_argument("--no-eval", action="store_true", help="Skip evaluation after agent run")
    parser.add_argument("--cleanup", action="store_true", help="Destroy container after evaluation")
    parser.add_argument("--verbose", action="store_true", default=True, help="Verbose output")
    args = parser.parse_args()
    
    # Resolve run output directory
    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_slug = args.model.replace("/", "_").replace(":", "_")
        run_dir = Path("results") / f"terminus_{model_slug}_{ts}"
    
    instance_dir = args.instance
    instance_id = Path(instance_dir).name
    
    # Check build_status
    task_json_path = Path(instance_dir) / "task.json"
    if task_json_path.exists():
        task_data = json.loads(task_json_path.read_text())
        if task_data.get("build_status") == "failed":
            print(f"Skipping {instance_id}: build_status is 'failed'")
            sys.exit(0)
        filter_status = task_data.get("filter_status", "")
        if filter_status in ("too_easy", "unsolvable"):
            print(f"Skipping {instance_id}: filter_status is '{filter_status}'")
            sys.exit(0)
    
    run_instance_dir = run_dir / instance_id
    run_instance_dir.mkdir(parents=True, exist_ok=True)
    
    sandbox = Sandbox()
    
    # Check for existing container
    meta_path = Path(instance_dir) / "container.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        container_id = meta["container_id"]
        print(f"Using existing container: {container_id[:12]}")
    else:
        print("Building Docker image...")
        tag = sandbox.build(instance_dir)
        print(f"Creating container...")
        container_id = sandbox.create(instance_dir)
        meta_path.write_text(json.dumps({"container_id": container_id, "image_tag": tag}))
        print(f"Container ready: {container_id[:12]}")
    
    # Create LLM client
    try:
        llm_client = LLMClient(
            provider=args.provider,
            model=args.model,
            api_base=args.api_base,
            api_key=args.api_key,
        )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Run agent
    print("\n" + "="*60)
    print(f"Starting Terminus-2 style agent ({args.provider})...")
    print("="*60)
    
    messages = run_terminus_agent(
        instance_dir=instance_dir,
        llm_client=llm_client,
        container_id=container_id,
        sandbox=sandbox,
        max_iterations=args.max_iterations,
        verbose=args.verbose,
    )
    
    # Save conversation
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
        
        result_path = run_instance_dir / "result.json"
        result_path.write_text(result.to_json())
        print(f"\nResult saved to {result_path}")
        
        # Update summary
        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            summary = RunSummary.load(str(summary_path))
        else:
            summary = RunSummary(
                run_name=run_dir.name,
                model=args.model,
                api_base=args.api_base or "",
            )
        summary.update_from_result(result)
        summary.save(str(summary_path))
        print(f"Summary: {summary_path}")
    
    # Cleanup
    if args.cleanup:
        print(f"\nCleaning up container {container_id[:12]}...")
        sandbox.destroy(container_id)
        meta_path.unlink(missing_ok=True)
        print("Container removed.")


if __name__ == "__main__":
    main()
