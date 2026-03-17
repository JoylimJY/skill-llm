"""Run eval.py against a completed workspace and parse results."""

import json
import subprocess
import tempfile
import shutil
from pathlib import Path

from .schema import EvalResult


def evaluate(instance_dir: str, workspace_dir: str) -> EvalResult:
    """Run evaluation for a completed task instance.

    1. Locate eval/eval.py in the instance directory
    2. Run: python eval.py {workspace_dir}
    3. Parse stdout as JSON
    4. Return EvalResult
    """
    instance_dir = Path(instance_dir)
    eval_script = instance_dir / "eval" / "eval.py"

    if not eval_script.exists():
        raise FileNotFoundError(f"eval.py not found at {eval_script}")

    workspace_dir = str(Path(workspace_dir).resolve())

    # Copy eval script to a temp location to avoid path issues
    with tempfile.TemporaryDirectory() as tmp:
        tmp_eval = Path(tmp) / "eval.py"
        shutil.copy2(eval_script, tmp_eval)

        result = subprocess.run(
            ["python", str(tmp_eval), workspace_dir],
            capture_output=True,
            text=True,
            timeout=120,
        )

    if result.returncode != 0:
        # Eval script crashed — treat as failure
        return EvalResult(
            instance_id=instance_dir.name,
            passed=False,
            score=0.0,
            details=[{
                "name": "eval_execution",
                "passed": False,
                "detail": f"eval.py failed (exit {result.returncode}): {result.stderr.strip()}",
            }],
        )

    # Parse JSON output
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return EvalResult(
            instance_id=instance_dir.name,
            passed=False,
            score=0.0,
            details=[{
                "name": "eval_output_parse",
                "passed": False,
                "detail": f"eval.py produced invalid JSON: {stdout[:500]}",
            }],
        )

    return EvalResult(
        instance_id=instance_dir.name,
        passed=data.get("passed", False),
        score=float(data.get("score", 0.0)),
        details=data.get("checks", []),
    )


def evaluate_in_container(instance_dir: str, container_id: str, sandbox) -> EvalResult:
    """Run evaluation inside the Docker container.

    Copies eval.py into the container and runs it against /workspace.
    """
    instance_dir = Path(instance_dir)
    eval_script = instance_dir / "eval" / "eval.py"

    if not eval_script.exists():
        raise FileNotFoundError(f"eval.py not found at {eval_script}")

    # Copy eval script into container
    subprocess.run(
        ["docker", "cp", str(eval_script), f"{container_id}:/eval.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    # Run eval
    output, exit_code = sandbox.exec(container_id, "python /eval.py /workspace")

    if exit_code != 0:
        return EvalResult(
            instance_id=instance_dir.name,
            passed=False,
            score=0.0,
            details=[{
                "name": "eval_execution",
                "passed": False,
                "detail": f"eval.py failed (exit {exit_code}): {output.strip()}",
            }],
        )

    # Parse the last JSON object from output (eval may print debug info before it)
    try:
        # Try parsing the full output first
        data = json.loads(output.strip())
    except json.JSONDecodeError:
        # Try to find the last JSON-like line
        lines = output.strip().split("\n")
        data = None
        for line in reversed(lines):
            line = line.strip()
            if line.startswith("{"):
                try:
                    data = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
        if data is None:
            return EvalResult(
                instance_id=instance_dir.name,
                passed=False,
                score=0.0,
                details=[{
                    "name": "eval_output_parse",
                    "passed": False,
                    "detail": f"eval.py produced invalid JSON: {output[:500]}",
                }],
            )

    return EvalResult(
        instance_id=instance_dir.name,
        passed=data.get("passed", False),
        score=float(data.get("score", 0.0)),
        details=data.get("checks", []),
    )
