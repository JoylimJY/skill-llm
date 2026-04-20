"""
Terminus-2 Adapter for SkillLLM Docker Sandbox

This module provides a TmuxSession-like interface that wraps the SkillLLM Docker sandbox,
allowing terminus_2 agent logic to work with the existing Docker-based evaluation system.

Key differences from original terminus_2:
- Original: Uses tmux sessions inside a Docker container (requires tmux installed)
- This adapter: Simulates tmux behavior using docker exec directly
- Prompt format: JSON with {analysis, plan, commands, task_complete}

Prompts are loaded from prompts/terminus_*.txt files via src.prompts.load_prompt().
"""

import re
import time
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from .sandbox import Sandbox
from .prompts import load_prompt


@dataclass
class ParsedCommand:
    """Represents a parsed command from the LLM response."""
    keystrokes: str
    duration: float


@dataclass
class ParseResult:
    """Result of parsing a terminus JSON response."""
    commands: list[ParsedCommand]
    is_task_complete: bool
    error: str
    warning: str


class TerminusJSONParser:
    """Parser for terminus JSON plain response format."""

    def __init__(self):
        self.required_fields = ["analysis", "plan", "commands"]

    def parse_response(self, response: str) -> ParseResult:
        """Parse a terminus JSON plain response and extract commands."""
        import json

        # Try normal parsing first
        result = self._try_parse_response(response)

        if result.error:
            # Try auto-fixes in order until one works
            for fix_name, fix_function in self._get_auto_fixes():
                corrected_response, was_fixed = fix_function(response, result.error)
                if was_fixed:
                    corrected_result = self._try_parse_response(corrected_response)
                    if corrected_result.error == "":
                        auto_warning = (
                            f"AUTO-CORRECTED: {fix_name} - "
                            "please fix this in future responses"
                        )
                        corrected_result.warning = self._combine_warnings(
                            auto_warning, corrected_result.warning
                        )
                        return corrected_result

        return result

    def _try_parse_response(self, response: str) -> ParseResult:
        import json
        warnings = []

        # Extract JSON content
        json_content, extra_text_warnings = self._extract_json_content(response)
        warnings.extend(extra_text_warnings)

        if not json_content:
            return ParseResult(
                [], False, "No valid JSON found in response",
                "- " + "\n- ".join(warnings) if warnings else "",
            )

        # Parse JSON
        try:
            parsed_data = json.loads(json_content)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {str(e)}"
            if len(json_content) < 200:
                error_msg += f" | Content: {repr(json_content)}"
            else:
                error_msg += f" | Content preview: {repr(json_content[:100])}..."
            return ParseResult(
                [], False, error_msg,
                "- " + "\n- ".join(warnings) if warnings else "",
            )

        # Validate structure
        validation_error = self._validate_json_structure(parsed_data, json_content, warnings)
        if validation_error:
            return ParseResult(
                [], False, validation_error,
                "- " + "\n- ".join(warnings) if warnings else "",
            )

        # Check if task is complete
        is_complete = parsed_data.get("task_complete", False)
        if isinstance(is_complete, str):
            is_complete = is_complete.lower() in ("true", "1", "yes")

        # Parse commands
        commands_data = parsed_data.get("commands", [])
        commands, parse_error = self._parse_commands(commands_data, warnings)
        if parse_error:
            if is_complete:
                warnings.append(parse_error)
                return ParseResult([], True, "", "- " + "\n- ".join(warnings) if warnings else "")
            return ParseResult([], False, parse_error, "- " + "\n- ".join(warnings) if warnings else "")

        return ParseResult(commands, is_complete, "", "- " + "\n- ".join(warnings) if warnings else "")

    def _extract_json_content(self, response: str) -> tuple[str, list[str]]:
        """Extract JSON content from response, handling extra text."""
        warnings = []

        # Find JSON object boundaries
        json_start = -1
        json_end = -1
        brace_count = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(response):
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if not in_string:
                if char == "{":
                    if brace_count == 0:
                        json_start = i
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0 and json_start != -1:
                        json_end = i + 1
                        break

        if json_start == -1 or json_end == -1:
            return "", ["No valid JSON object found"]

        before_text = response[:json_start].strip()
        after_text = response[json_end:].strip()

        if before_text:
            warnings.append("Extra text detected before JSON object")
        if after_text:
            warnings.append("Extra text detected after JSON object")

        return response[json_start:json_end], warnings

    def _validate_json_structure(self, data: dict, json_content: str, warnings: list[str]) -> str:
        if not isinstance(data, dict):
            return "Response must be a JSON object"

        missing_fields = [f for f in self.required_fields if f not in data]
        if missing_fields:
            return f"Missing required fields: {', '.join(missing_fields)}"

        if not isinstance(data.get("analysis", ""), str):
            warnings.append("Field 'analysis' should be a string")
        if not isinstance(data.get("plan", ""), str):
            warnings.append("Field 'plan' should be a string")

        commands = data.get("commands", [])
        if not isinstance(commands, list):
            return "Field 'commands' must be an array"

        return ""

    def _parse_commands(self, commands_data: list, warnings: list[str]) -> tuple[list[ParsedCommand], str]:
        commands = []

        for i, cmd_data in enumerate(commands_data):
            if not isinstance(cmd_data, dict):
                return [], f"Command {i + 1} must be an object"

            if "keystrokes" not in cmd_data:
                return [], f"Command {i + 1} missing required 'keystrokes' field"

            keystrokes = cmd_data["keystrokes"]
            if not isinstance(keystrokes, str):
                return [], f"Command {i + 1} 'keystrokes' must be a string"

            duration = cmd_data.get("duration", 1.0)
            if not isinstance(duration, (int, float)):
                warnings.append(f"Command {i + 1}: Invalid duration, using default 1.0")
                duration = 1.0

            commands.append(ParsedCommand(keystrokes=keystrokes, duration=float(duration)))

        return commands, ""

    def _get_auto_fixes(self):
        return [
            ("Fixed incomplete JSON by adding missing closing brace", self._fix_incomplete_json),
            ("Extracted JSON from mixed content", self._fix_mixed_content),
        ]

    def _fix_incomplete_json(self, response: str, error: str) -> tuple[str, bool]:
        if "Invalid JSON" in error or "Expecting" in error or "Unterminated" in error or "No valid JSON found" in error:
            brace_count = response.count("{") - response.count("}")
            if brace_count > 0:
                fixed = response + "}" * brace_count
                return fixed, True
        return response, False

    def _fix_mixed_content(self, response: str, error: str) -> tuple[str, bool]:
        import json
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.findall(json_pattern, response, re.DOTALL)

        for match in matches:
            try:
                json.loads(match)
                return match, True
            except json.JSONDecodeError:
                continue
        return response, False

    def _combine_warnings(self, auto_warning: str, existing_warning: str) -> str:
        if existing_warning:
            return f"- {auto_warning}\n{existing_warning}"
        return f"- {auto_warning}"


class DockerTmuxAdapter:
    """
    Adapter that provides a TmuxSession-like interface over Docker exec.

    This allows terminus_2 agent logic to work with the existing SkillLLM sandbox
    without requiring tmux to be installed in the container.

    Key adaptations:
    - send_keys() -> docker exec (keystrokes converted to shell commands)
    - capture_pane() -> docker exec (pwd + last command output)
    - get_incremental_output() -> tracks output buffer between calls
    """

    def __init__(self, sandbox: Sandbox, container_id: str, session_name: str = "terminus"):
        self._sandbox = sandbox
        self._container_id = container_id
        self._session_name = session_name
        self._output_buffer = ""
        self._previous_buffer: Optional[str] = None
        self._last_command_output = ""
        self._current_dir = "/workspace"

    def start(self) -> None:
        """Initialize the session (no-op for Docker, already started)."""
        # Container is already running from Sandbox.create()
        pass

    def stop(self) -> None:
        """Stop the session (handled by Sandbox.destroy())."""
        pass

    def send_keys(
        self,
        keys: str | list[str],
        block: bool = False,
        min_timeout_sec: float = 0.0,
        max_timeout_sec: float = 180.0,
    ) -> None:
        """
        Execute keystrokes as shell commands in the container.

        Args:
            keys: Keystrokes to send (string or list of strings)
            block: Whether to wait for command completion (always True in Docker)
            min_timeout_sec: Minimum wait time
            max_timeout_sec: Maximum wait time (used as exec timeout)
        """
        if isinstance(keys, str):
            keys = [keys]

        # Process keystrokes
        for key in keys:
            self._process_keystroke(key, timeout=max_timeout_sec)

        # Apply min_timeout
        if min_timeout_sec > 0:
            time.sleep(min_timeout_sec)

    def _process_keystroke(self, key: str, timeout: float = 180.0) -> None:
        """Process a single keystroke or command."""
        key = key.replace("\\n", "\n").replace("\\r", "\r")
        # Handle special keys
        if key == "C-c":
            # Send Ctrl+C - we can't really interrupt in docker exec
            # Instead, we start a fresh shell context
            return
        elif key == "C-d":
            # EOF signal
            return
        elif key == "Enter":
            # Just a newline, ignore
            return

        # If it's a regular command (ends with newline), execute it
        if key.endswith("\n"):
            cmd = key.rstrip("\n")
            if cmd.strip():
                self._execute_command(cmd, timeout)
        else:
            # Partial input - just accumulate (rare in terminus format)
            self._output_buffer += key

    def _execute_command(self, cmd: str, timeout: float) -> None:
        """Execute a shell command in the container."""
        # Track directory changes
        cmd_stripped = cmd.strip()

        # Handle cd commands specially
        if cmd_stripped.startswith("cd "):
            target_dir = cmd_stripped[3:].strip()
            if target_dir == "..":
                self._current_dir = str(Path(self._current_dir).parent)
            elif target_dir.startswith("/"):
                self._current_dir = target_dir
            else:
                self._current_dir = str(Path(self._current_dir) / target_dir)

        # Execute in container
        full_cmd = f"cd {self._current_dir} && {cmd}"
        output, exit_code = self._sandbox.exec(
            self._container_id,
            full_cmd,
            timeout=int(timeout)
        )

        self._last_command_output = output
        self._output_buffer += output + "\n"

    def capture_pane(self, capture_entire: bool = False) -> str:
        """
        Capture terminal pane content.

        In Docker mode, this returns the last command output plus current directory info.
        """
        if capture_entire:
            # Return accumulated output
            return self._output_buffer

        # Return last output + current state
        state_cmd = f"cd {self._current_dir} && echo \"[PWD: $(pwd)]\" && ls -la 2>/dev/null || true"
        state_output, _ = self._sandbox.exec(self._container_id, state_cmd, timeout=10)

        return self._last_command_output + "\n" + state_output

    def get_incremental_output(self) -> str:
        """
        Get new terminal output since last call.

        Returns formatted output with either new content or current screen.
        """
        current_buffer = self.capture_pane(capture_entire=True)

        if self._previous_buffer is None:
            self._previous_buffer = current_buffer
            return f"Current Terminal Screen:\n{self.capture_pane(capture_entire=False)}"

        # Find new content
        new_content = self._find_new_content(current_buffer)
        self._previous_buffer = current_buffer

        if new_content and new_content.strip():
            return f"New Terminal Output:\n{new_content}"
        else:
            return f"Current Terminal Screen:\n{self.capture_pane(capture_entire=False)}"

    def _find_new_content(self, current_buffer: str) -> Optional[str]:
        """Find new content by comparing with previous buffer."""
        if self._previous_buffer is None:
            return None

        pb = self._previous_buffer.strip()
        if pb and pb in current_buffer:
            idx = current_buffer.index(pb)
            return current_buffer[idx + len(pb):]

        return None

    def is_session_alive(self) -> bool:
        """Check if the container is still running."""
        import subprocess
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", self._container_id],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip() == "true"

    def clear_history(self) -> None:
        """Clear the output buffer."""
        self._output_buffer = ""
        self._last_command_output = ""


class Terminus2Runner:
    """
    Main runner that integrates terminus_2 agent logic with SkillLLM sandbox.

    Usage:
        sandbox = Sandbox()
        container_id = sandbox.create(instance_dir)
        runner = Terminus2Runner(sandbox, container_id, llm_client)
        result = runner.run(task_instruction)

    Prompts are loaded from:
        - prompts/terminus_system.txt (system prompt / prompt template)
        - prompts/terminus_timeout.txt (timeout handling)
        - prompts/terminus_task.txt (task formatting)
    """

    @staticmethod
    def _get_prompt_template() -> str:
        """Load prompt template from prompts/terminus_system.txt"""
        return load_prompt("terminus_system")

    @staticmethod
    def _get_timeout_template() -> str:
        """Load timeout template from prompts/terminus_timeout.txt"""
        return load_prompt("terminus_timeout")

    def __init__(
        self,
        sandbox: Sandbox,
        container_id: str,
        llm_client,
        max_iterations: int = 100,
        max_tokens: int = 128000,
        verbose: bool = True,
    ):
        """
        Initialize the Terminus-2 runner.

        Args:
            sandbox: SkillLLM Sandbox instance
            container_id: Docker container ID
            llm_client: LLM client with .chat() method (compatible with your synthesizer)
            max_iterations: Maximum agent iterations before stopping
            max_tokens: Context window limit for the LLM
            verbose: Whether to print debug information
        """
        self.sandbox = sandbox
        self.container_id = container_id
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.verbose = verbose

        self.tmux = DockerTmuxAdapter(sandbox, container_id)
        self.parser = TerminusJSONParser()

        # Tracking state
        self._iteration_count = 0
        self._task_complete_count = 0  # Double-confirm mechanism
        self._history = []

    def run(self, instruction: str) -> dict:
        """
        Run the agent to complete the given task.

        Args:
            instruction: Task description/instruction

        Returns:
            dict with keys: success, iterations, history, final_output
        """
        self.tmux.start()

        try:
            terminal_state = self.tmux.capture_pane(capture_entire=False)

            for iteration in range(self.max_iterations):
                self._iteration_count = iteration + 1

                if self.verbose:
                    print(f"\n=== Iteration {self._iteration_count} ===")

                # Build prompt
                prompt = self._build_prompt(instruction, terminal_state)

                # Call LLM
                response = self._call_llm(prompt)

                if self.verbose:
                    print(f"LLM Response:\n{response[:500]}...")

                # Parse response
                parse_result = self.parser.parse_response(response)

                if parse_result.error:
                    if self.verbose:
                        print(f"Parse error: {parse_result.error}")
                    terminal_state = self._format_error_state(parse_result.error, parse_result.warning)
                    continue

                if parse_result.warning and self.verbose:
                    print(f"Warnings: {parse_result.warning}")

                # Check for task completion (double-confirm)
                if parse_result.is_task_complete:
                    self._task_complete_count += 1
                    if self._task_complete_count >= 2:
                        if self.verbose:
                            print("Task marked as complete (confirmed twice)")
                        return {
                            "success": True,
                            "iterations": self._iteration_count,
                            "history": self._history,
                            "final_output": terminal_state,
                        }
                    if self.verbose:
                        print("Task marked as complete (first confirmation)")
                else:
                    self._task_complete_count = 0

                # Execute commands
                if parse_result.commands:
                    terminal_state = self._execute_commands(parse_result.commands)
                else:
                    # Empty commands = wait
                    time.sleep(1.0)
                    terminal_state = self.tmux.get_incremental_output()

                # Record history
                self._history.append({
                    "iteration": self._iteration_count,
                    "response": response,
                    "commands": [(c.keystrokes, c.duration) for c in parse_result.commands],
                    "terminal_state": terminal_state,
                })

            # Max iterations reached
            return {
                "success": False,
                "iterations": self.max_iterations,
                "history": self._history,
                "final_output": terminal_state,
                "error": "Max iterations reached",
            }

        finally:
            self.tmux.stop()

    def _build_prompt(self, instruction: str, terminal_state: str) -> str:
        """Build the prompt for the LLM using prompts/terminus_task.txt template."""
        return load_prompt(
            "terminus_task",
            instruction=instruction,
            terminal_state=terminal_state or "(empty terminal)",
            additional_instruction=""
        )

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM and return the response."""
        system_prompt = self._get_prompt_template()
        
        # Check if llm_client has the new interface (chat with messages + system_prompt)
        if hasattr(self.llm_client, 'chat'):
            # Try the new interface first
            try:
                return self.llm_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt=system_prompt,
                )
            except TypeError:
                # Fall back to old interface (single prompt argument)
                combined_prompt = f"{system_prompt}\n\n{prompt}"
                return self.llm_client.chat(combined_prompt)
        elif hasattr(self.llm_client, 'generate'):
            combined_prompt = f"{system_prompt}\n\n{prompt}"
            return self.llm_client.generate(combined_prompt)
        else:
            raise ValueError("LLM client must have 'chat' or 'generate' method")

    def _execute_commands(self, commands: list[ParsedCommand]) -> str:
        """Execute parsed commands and return terminal output."""
        outputs = []

        for cmd in commands:
            if self.verbose:
                print(f"Executing: {repr(cmd.keystrokes[:100])}")

            try:
                self.tmux.send_keys(
                    cmd.keystrokes,
                    min_timeout_sec=min(cmd.duration, 60.0),  # Cap at 60s
                )
                time.sleep(cmd.duration)
            except Exception as e:
                outputs.append(f"ERROR: {str(e)}")
                continue

            # Get output
            output = self.tmux.get_incremental_output()
            outputs.append(output)

        return "\n".join(outputs)

    def _format_error_state(self, error: str, warning: str = "") -> str:
        """Format an error state for the next prompt."""
        state = f"ERROR: {error}\n\n"
        if warning:
            state += f"Warnings:\n{warning}\n\n"
        state += "Please fix the error and try again. Make sure your response is valid JSON."
        return state
