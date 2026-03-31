"""Pass@k-based task quality filtering.

After build succeeds, run a small model (e.g. Qwen3.5-27B) multiple times
on each instance. Discard tasks where the model passes ALL trials (too easy)
or NONE of them (unsolvable).
"""

import json
import uuid
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .sandbox import Sandbox
from .evaluator import evaluate_in_container
from .schema import EvalResult, FilterResult


def apply_filter(num_passed: int, num_trials: int) -> str:
    """Decide verdict: keep, too_easy, or unsolvable.

    - All trials pass  → too_easy
    - No trials pass   → unsolvable
    - Otherwise        → kept
    """
    if num_trials == 0:
        return "unsolvable"
    if num_passed == num_trials:
        return "too_easy"
    if num_passed == 0:
        return "unsolvable"
    return "kept"


def _create_container_from_image(image_tag: str) -> str:
    """Create a new container from an existing image, return container_id."""
    result = subprocess.run(
        [
            "docker", "run", "-d",
            "--name", f"sb-filter-{uuid.uuid4().hex[:12]}",
            "-w", "/workspace",
            image_tag,
            "tail", "-f", "/dev/null",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"docker run failed:\n{result.stderr}")
    return result.stdout.strip()


def _init_container(instance_dir: Path, container_id: str, sandbox: Sandbox):
    """Copy workspace files, run gen_inputs.py and setup.sh inside container."""
    runtime_dir = instance_dir / "runtime"

    # Copy workspace files
    workspace_dir = runtime_dir / "workspace"
    if workspace_dir.exists() and any(workspace_dir.iterdir()):
        subprocess.run(
            ["docker", "cp", f"{workspace_dir}/.", f"{container_id}:/workspace/"],
            check=True, capture_output=True, text=True,
        )

    # Copy and run gen_inputs.py
    gen_inputs = runtime_dir / "gen_inputs.py"
    if gen_inputs.exists():
        subprocess.run(
            ["docker", "cp", str(gen_inputs), f"{container_id}:/workspace/gen_inputs.py"],
            check=True, capture_output=True, text=True,
        )
        output, exit_code = sandbox.exec(container_id, "python3 /workspace/gen_inputs.py")
        if exit_code != 0:
            raise RuntimeError(f"gen_inputs.py failed (exit {exit_code}):\n{output}")

    # Copy and run setup.sh
    setup_sh = runtime_dir / "setup.sh"
    if setup_sh.exists():
        subprocess.run(
            ["docker", "cp", str(setup_sh), f"{container_id}:/workspace/setup.sh"],
            check=True, capture_output=True, text=True,
        )
        output, exit_code = sandbox.exec(
            container_id, "chmod +x /workspace/setup.sh && /workspace/setup.sh"
        )
        if exit_code != 0:
            raise RuntimeError(f"setup.sh failed (exit {exit_code}):\n{output}")


def run_single_trial(
    instance_dir: str,
    api_base: str,
    model: str,
    image_tag: str,
    trial_index: int,
    verbose: bool = False,
) -> EvalResult:
    """Run one agent trial: create container -> run agent -> evaluate -> destroy.

    Each trial gets a fresh container from the pre-built image.
    """
    from .agent_runner_lib import run_agent_in_container

    instance_dir = Path(instance_dir)
    sandbox = Sandbox()
    container_id = None

    try:
        # Create fresh container from existing image
        container_id = _create_container_from_image(image_tag)
        _init_container(instance_dir, container_id, sandbox)

        if verbose:
            print(f"    Trial {trial_index}: container {container_id[:12]} created")

        # Run agent
        run_agent_in_container(
            instance_dir=str(instance_dir),
            api_base=api_base,
            model=model,
            container_id=container_id,
            sandbox=sandbox,
            verbose=False,
        )

        # Evaluate
        result = evaluate_in_container(str(instance_dir), container_id, sandbox)

        if verbose:
            status = "PASS" if result.passed else "FAIL"
            print(f"    Trial {trial_index}: [{status}] score={result.score:.2f}")

        return result

    except Exception as e:
        if verbose:
            print(f"    Trial {trial_index}: ERROR - {e}")
        return EvalResult(
            instance_id=instance_dir.name,
            passed=False,
            score=0.0,
            details=[{"name": "trial_error", "passed": False, "detail": str(e)}],
        )

    finally:
        if container_id:
            try:
                sandbox.destroy(container_id)
            except Exception:
                pass


def filter_instance(
    instance_dir: str,
    api_base: str,
    model: str,
    num_trials: int = 16,
    concurrency: int = 4,
    verbose: bool = True,
) -> FilterResult:
    """Run multiple agent trials on an instance and filter by results.

    Discard if ALL trials pass (too easy) or NONE pass (unsolvable).

    1. Build image if not already built
    2. Run num_trials agent trials in parallel (each with fresh container)
    3. Count passes and apply filter
    4. Write results to task.json

    Returns FilterResult with verdict.
    """
    instance_dir_path = Path(instance_dir)
    instance_id = instance_dir_path.name

    if verbose:
        print(f"  Filtering {instance_id}: {num_trials} trials, concurrency={concurrency}")

    # Get or build image tag
    image_tag = f"skillbench-{instance_id}".lower().replace(" ", "-")

    # Verify image exists
    check = subprocess.run(
        ["docker", "image", "inspect", image_tag],
        capture_output=True, text=True,
    )
    if check.returncode != 0:
        if verbose:
            print(f"  Image {image_tag} not found, building...")
        sandbox = Sandbox()
        sandbox.build(str(instance_dir))

    # Run trials in parallel
    results: list[EvalResult] = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(
                run_single_trial,
                str(instance_dir),
                api_base,
                model,
                image_tag,
                i,
                verbose,
            ): i
            for i in range(num_trials)
        }

        for future in as_completed(futures):
            trial_idx = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                if verbose:
                    print(f"    Trial {trial_idx}: EXCEPTION - {e}")
                results.append(EvalResult(
                    instance_id=instance_id,
                    passed=False,
                    score=0.0,
                    details=[{"name": "trial_exception", "passed": False, "detail": str(e)}],
                ))

    # Compute statistics
    num_passed = sum(1 for r in results if r.passed)
    pass_rate = num_passed / len(results) if results else 0.0
    trial_scores = [r.score for r in results]

    verdict = apply_filter(num_passed, len(results))

    filter_result = FilterResult(
        instance_id=instance_id,
        num_trials=len(results),
        num_passed=num_passed,
        pass_rate=pass_rate,
        verdict=verdict,
        trial_scores=trial_scores,
    )

    # Write filter results to task.json
    task_json_path = instance_dir_path / "task.json"
    if task_json_path.exists():
        task_data = json.loads(task_json_path.read_text())
    else:
        task_data = {}

    task_data["filter_status"] = verdict
    task_data["filter_details"] = {
        "num_trials": filter_result.num_trials,
        "num_passed": filter_result.num_passed,
        "pass_rate": filter_result.pass_rate,
        "trial_scores": filter_result.trial_scores,
        "model": model,
    }
    task_json_path.write_text(json.dumps(task_data, indent=2))

    if verbose:
        avg_score = sum(trial_scores) / len(trial_scores) if trial_scores else 0.0
        print(f"  Result: {verdict} "
              f"({num_passed}/{len(results)} passed, avg_score={avg_score:.3f})")

    return filter_result
