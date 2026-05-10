"""Pass@k-based task quality filtering using Terminus-2 style agent.

After build succeeds, run the terminus_2 agent multiple times
on each instance. Discard tasks where the model passes ALL trials (too easy)
or NONE of them (unsolvable).
"""

import sys
import io
import json
import uuid
import subprocess
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Literal

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

def run_single_trial_terminus(
    instance_dir: str,
    provider: Literal["openai", "claude"],
    model: str,
    api_base: str,
    api_key: str,
    image_tag: str, 
    trial_index: int,
    max_iterations: int = 30,
    verbose: bool = False,
) -> EvalResult:
    """Run one terminus_2 agent trial: create container -> run agent -> evaluate -> destroy."""
    from .terminus_runner import LLMClient, run_terminus_agent

    instance_dir = Path(instance_dir)
    sandbox = Sandbox()
    container_id = None

    try:
        container_id = sandbox.create(str(instance_dir))

        if verbose:
            print(f"    Trial {trial_index}: container {container_id[:12]} created")

        # Load task prompt
        task_json = json.loads((instance_dir / "task.json").read_text())
        task_prompt = task_json["prompt"]

        # Create LLM client
        llm_client = LLMClient(
            provider=provider,
            model=model,
            api_base=api_base,
            api_key=api_key,
        )

        log_buffer = io.StringIO()
        original_stdout = sys.stdout

        log_buffer = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = log_buffer

        try:
            print("="*60)
            print(f"Starting Terminus-2 style agent ({provider}) - Trial {trial_index}...")
            print("="*60)
            print(f"\nTASK: {task_prompt}\n")
            print("="*60)

            agent_trajectory = run_terminus_agent(
                instance_dir=str(instance_dir),  
                llm_client=llm_client,
                container_id=container_id,
                sandbox=sandbox,
                max_iterations=max_iterations,
                verbose=True,  
            )
            print("\n" + "="*60)
            print("Running evaluation...")
            print("="*60)
            result = evaluate_in_container(str(instance_dir), container_id, sandbox)
            print("\n" + "="*60)
            print("Running evaluation...")
            print("="*60)
            result = evaluate_in_container(str(instance_dir), container_id, sandbox)

            print(f"✅ Eval Passed: {result.passed}")
            print(f"📊 Eval Score: {result.score:.3f}")
            print("🔍 Eval Details:")
            if hasattr(result, 'details'):
                print(json.dumps(result.details, indent=2, ensure_ascii=False))
            else:
                print(str(result))
            print("="*60)

        finally:
            sys.stdout = original_stdout

            log_txt_path = instance_dir / f"filter_trial_{trial_index}_log.txt"
            log_txt_path.write_text(log_buffer.getvalue(), encoding="utf-8")

        if verbose:
            status = "PASS" if result.passed else "FAIL"
            print(f"    Trial {trial_index}: [{status}] score={result.score:.2f}")

        log_json_path = instance_dir / f"filter_trial_{trial_index}_history.json"
        log_json_path.write_text(json.dumps(agent_trajectory, indent=2, ensure_ascii=False))

        return result

    except Exception as e:
        if 'original_stdout' in locals() and sys.stdout != original_stdout:
            sys.stdout = original_stdout
            log_txt_path = instance_dir / f"filter_trial_{trial_index}_log.txt"
            log_txt_path.write_text(log_buffer.getvalue() + f"\n\nEXCEPTION: {e}", encoding="utf-8")

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


def filter_instance_terminus(
    instance_dir: str,
    provider: Literal["openai", "claude"],
    model: str,
    api_base: str,
    api_key: str = "",
    num_trials: int = 4, 
    concurrency: int = 4,
    max_iterations: int = 30,
    verbose: bool = True,
) -> FilterResult:
    """Run multiple terminus_2 agent trials sequentially and filter by results."""
    instance_dir_path = Path(instance_dir)
    instance_id = instance_dir_path.name

    if verbose:
        print(f"  Filtering {instance_id}: Up to {num_trials} sequential trials")

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

    results: list[EvalResult] = []
    
    for i in range(num_trials):
        try:
            result = run_single_trial_terminus(
                str(instance_dir),
                provider,
                model,
                api_base,
                api_key,
                image_tag,
                i,
                max_iterations,
                verbose,
            )
            results.append(result)
            
            if result.passed:
                if verbose:
                    print(f"    ✨ Instance {instance_id} PASSED at trial {i}. Stopping early.")
                break
                
        except Exception as e:
            if verbose:
                print(f"    Trial {i}: EXCEPTION - {e}")
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

    all_zero = False
    all_same = False
    if len(results) == num_trials:
        all_zero = all(s == 0 for s in trial_scores)
        all_same = len(set(trial_scores)) == 1

    # Decide verdict
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
        "provider": provider,
        "harness": "terminus_2",
        "all_zero": all_zero,       
        "all_same_score": all_same  
    }
    task_json_path.write_text(json.dumps(task_data, indent=2))

    if verbose:
        avg_score = sum(trial_scores) / len(trial_scores) if trial_scores else 0.0
        print(f"  Result: {verdict} "
              f"({num_passed}/{len(results)} passed, avg_score={avg_score:.3f})")
        if all_zero:
            print("4次尝试全部0分")
        elif all_same and not all_zero:
            print(f"4次尝试分数相同 ({trial_scores[0]:.3f})")

    return filter_result