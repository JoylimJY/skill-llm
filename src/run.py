"""CLI entry point for SkillBench: synthesize / build / evaluate."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .synthesizer import synthesize_skill, load_skill, write_instance_dir
from .sandbox import Sandbox, BuildFailedError
from .evaluator import evaluate, evaluate_in_container
from .filter import filter_instance
from .filter_terminus import filter_instance_terminus
from .schema import InstanceSpec, RunSummary


def resolve_run_dir(args) -> Path:
    """Resolve the run output directory from --run-dir or generate a default."""
    if hasattr(args, "run_dir") and args.run_dir:
        return Path(args.run_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("results") / f"run_{ts}"


def save_result_to_run(result, instance_dir: str, run_dir: Path):
    """Save evaluation result to the run directory."""
    instance_id = Path(instance_dir).name
    out = run_dir / instance_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(result.to_json())
    return out


def cmd_synthesize(args):
    """Synthesize task instances from a skill directory."""
    print(f"Synthesizing {args.num} instances from {args.skill_dir}...")
    paths = synthesize_skill(args.skill_dir, args.num, args.output_dir)
    print(f"\nDone. Generated {len(paths)} instances:")
    for p in paths:
        print(f"  {p}")


def cmd_build(args):
    """Build Docker image and create sandbox for an instance (with LLM retry)."""
    sandbox = Sandbox()
    instance_dir = args.instance

    print(f"Building Docker image for {instance_dir}...")
    try:
        tag, container_id = sandbox.build_with_retry(instance_dir)
        print(f"  Image: {tag}")
        print(f"  Container: {container_id}")

        # Mark success in task.json
        task_json_path = Path(instance_dir) / "task.json"
        if task_json_path.exists():
            task_data = json.loads(task_json_path.read_text())
            task_data["build_status"] = "success"
            task_json_path.write_text(json.dumps(task_data, indent=2))

        # Save container ID for later use
        meta_path = Path(instance_dir) / "container.json"
        meta_path.write_text(json.dumps({"container_id": container_id, "image_tag": tag}))
        print(f"  Container info saved to {meta_path}")

    except BuildFailedError as e:
        print(f"  BUILD FAILED after retries: {e}")
        sys.exit(1)


def cmd_evaluate(args):
    """Run evaluation on a completed instance."""
    instance_dir = args.instance
    run_dir = resolve_run_dir(args)

    # Check build_status — skip failed instances
    task_json_path = Path(instance_dir) / "task.json"
    if task_json_path.exists():
        task_data = json.loads(task_json_path.read_text())
        if task_data.get("build_status") == "failed":
            print(f"Skipping {instance_dir}: build_status is 'failed'")
            return
        # Skip filtered-out instances
        filter_status = task_data.get("filter_status", "")
        if filter_status in ("too_easy", "unsolvable"):
            print(f"Skipping {instance_dir}: filter_status is '{filter_status}'")
            return

    # Check if there's a running container
    meta_path = Path(instance_dir) / "container.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        container_id = meta["container_id"]
        sandbox = Sandbox()
        print(f"Evaluating in container {container_id[:12]}...")
        result = evaluate_in_container(instance_dir, container_id, sandbox)
    elif args.workspace:
        print(f"Evaluating workspace {args.workspace}...")
        result = evaluate(instance_dir, args.workspace)
    else:
        print("Error: No container found and no --workspace specified.", file=sys.stderr)
        sys.exit(1)

    print(f"\nResults for {result.instance_id}:")
    print(f"  Passed: {result.passed}")
    print(f"  Score:  {result.score:.2f}")
    if result.details:
        print("  Checks:")
        for check in result.details:
            status = "PASS" if check.get("passed") else "FAIL"
            print(f"    [{status}] {check.get('name', '?')}: {check.get('detail', '')}")

    # Save result to run directory
    out = save_result_to_run(result, instance_dir, run_dir)
    print(f"\n  Result saved to {out / 'result.json'}")


def cmd_destroy(args):
    """Destroy a container for an instance."""
    instance_dir = args.instance
    meta_path = Path(instance_dir) / "container.json"

    if not meta_path.exists():
        print("No container found for this instance.", file=sys.stderr)
        sys.exit(1)

    meta = json.loads(meta_path.read_text())
    container_id = meta["container_id"]

    sandbox = Sandbox()
    print(f"Destroying container {container_id[:12]}...")
    sandbox.destroy(container_id)
    meta_path.unlink()
    print("Done.")


def cmd_cleanup(args):
    """Clean up all skillbench containers."""
    sandbox = Sandbox()
    containers = sandbox.list_containers(all=True)

    if not containers:
        print("No skillbench containers found.")
        return

    print(f"Found {len(containers)} skillbench container(s):")
    for c in containers:
        print(f"  {c['id'][:12]}  {c['name']}  [{c['status']}]  {c['image']}")

    count = sandbox.cleanup_all()
    print(f"\nCleaned up {count} container(s).")

    # Also clean up stale container.json files in instances/
    instances_dir = Path("instances")
    if instances_dir.exists():
        for meta in instances_dir.glob("*/container.json"):
            meta.unlink()
            print(f"  Removed {meta}")


def cmd_filter(args):
    """Run pass@k filtering on built instances to discard too-easy or unsolvable tasks."""
    output_dir = Path(args.output_dir)

    # Collect instances to filter
    if args.instance:
        instance_dirs = [Path(args.instance)]
    else:
        # Filter all built instances in output_dir
        instance_dirs = sorted(
            d for d in output_dir.iterdir()
            if d.is_dir() and (d / "task.json").exists()
        )

    kept = 0
    too_easy = 0
    unsolvable = 0
    skipped = 0

    for inst_dir in instance_dirs:
        task_json_path = inst_dir / "task.json"
        task_data = json.loads(task_json_path.read_text())

        # Only filter successfully built instances
        if task_data.get("build_status") != "success":
            print(f"SKIP (not built): {inst_dir.name}")
            skipped += 1
            continue

        # Skip already-filtered instances unless --force
        if task_data.get("filter_status") and not args.force:
            verdict = task_data["filter_status"]
            print(f"SKIP (already filtered: {verdict}): {inst_dir.name}")
            if verdict == "kept":
                kept += 1
            elif verdict == "too_easy":
                too_easy += 1
            else:
                unsolvable += 1
            continue

        print(f"\n=== Filtering: {inst_dir.name} ===")
        try:
            result = filter_instance(
                instance_dir=str(inst_dir),
                api_base=args.api_base,
                model=args.model,
                num_trials=args.num_trials,
                concurrency=args.concurrency,
                verbose=True,
            )

            if result.verdict == "kept":
                kept += 1
            elif result.verdict == "too_easy":
                too_easy += 1
            else:
                unsolvable += 1

        except Exception as e:
            print(f"  ERROR: {e}")
            skipped += 1

    total = kept + too_easy + unsolvable
    print(f"\n=== Filter Summary ===")
    print(f"Total filtered: {total}  Kept: {kept}  Too easy: {too_easy}  Unsolvable: {unsolvable}  Skipped: {skipped}")


def cmd_filter_terminus(args):
    """Run pass@k filtering using Terminus-2 style agent."""
    output_dir = Path(args.output_dir)

    # Collect instances to filter
    if args.instance:
        instance_dirs = [Path(args.instance)]
    else:
        # Filter all built instances in output_dir
        instance_dirs = sorted(
            d for d in output_dir.iterdir()
            if d.is_dir() and (d / "task.json").exists()
        )

    kept = 0
    too_easy = 0
    unsolvable = 0
    skipped = 0

    for inst_dir in instance_dirs:
        task_json_path = inst_dir / "task.json"
        task_data = json.loads(task_json_path.read_text())

        # Only filter successfully built instances
        if task_data.get("build_status") != "success":
            print(f"SKIP (not built): {inst_dir.name}")
            skipped += 1
            continue

        # Skip already-filtered instances unless --force
        if task_data.get("filter_status") and not args.force:
            verdict = task_data["filter_status"]
            print(f"SKIP (already filtered: {verdict}): {inst_dir.name}")
            if verdict == "kept":
                kept += 1
            elif verdict == "too_easy":
                too_easy += 1
            else:
                unsolvable += 1
            continue

        print(f"\n=== Filtering (Terminus-2): {inst_dir.name} ===")
        try:
            result = filter_instance_terminus(
                instance_dir=str(inst_dir),
                provider=args.provider,
                model=args.model,
                api_base=args.api_base,
                api_key=args.api_key or "",
                num_trials=args.num_trials,
                concurrency=args.concurrency,
                max_iterations=args.max_iterations,
                verbose=True,
            )

            if result.verdict == "kept":
                kept += 1
            elif result.verdict == "too_easy":
                too_easy += 1
            else:
                unsolvable += 1

        except Exception as e:
            print(f"  ERROR: {e}")
            skipped += 1

    total = kept + too_easy + unsolvable
    print(f"\n=== Filter Summary (Terminus-2) ===")
    print(f"Total filtered: {total}  Kept: {kept}  Too easy: {too_easy}  Unsolvable: {unsolvable}  Skipped: {skipped}")


def cmd_all(args):
    """Full pipeline: synthesize + build + filter + evaluate all instances."""
    run_dir = resolve_run_dir(args)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Synthesize
    print(f"=== Step 1: Synthesize {args.num} instances from {args.skill_dir} ===")
    paths = synthesize_skill(args.skill_dir, args.num, args.output_dir)
    print(f"Generated {len(paths)} instances.\n")

    sandbox = Sandbox()

    # Step 2: Build all instances
    built_paths = []
    for instance_path in paths:
        instance_name = Path(instance_path).name
        print(f"=== Building: {instance_name} ===")

        task_json_path = Path(instance_path) / "task.json"
        if task_json_path.exists():
            task_data = json.loads(task_json_path.read_text())
            if task_data.get("build_status") == "failed":
                print(f"  Skipping: build_status is 'failed'\n")
                continue

        try:
            print("  Building (with LLM retry)...")
            tag, container_id = sandbox.build_with_retry(instance_path)

            # Mark success
            if task_json_path.exists():
                task_data = json.loads(task_json_path.read_text())
            else:
                task_data = {}
            task_data["build_status"] = "success"
            task_json_path.write_text(json.dumps(task_data, indent=2))

            # Destroy build container (filter will create fresh ones)
            sandbox.destroy(container_id)
            meta_path = Path(instance_path) / "container.json"
            meta_path.unlink(missing_ok=True)

            built_paths.append(instance_path)
            print(f"  Build OK.\n")

        except Exception as e:
            print(f"  BUILD ERROR: {e}\n")

    # Step 3: Filter (if api_base and model are provided)
    if hasattr(args, "filter_api_base") and args.filter_api_base:
        print(f"\n=== Step 3: Filter with {args.filter_model} ({args.filter_num_trials} trials) ===")
        kept_paths = []
        for instance_path in built_paths:
            instance_name = Path(instance_path).name
            print(f"\n--- Filtering: {instance_name} ---")
            try:
                result = filter_instance(
                    instance_dir=instance_path,
                    api_base=args.filter_api_base,
                    model=args.filter_model,
                    num_trials=args.filter_num_trials,
                    concurrency=args.filter_concurrency,
                )
                if result.verdict == "kept":
                    kept_paths.append(instance_path)
                else:
                    print(f"  FILTERED OUT: {result.verdict}")
            except Exception as e:
                print(f"  FILTER ERROR: {e}")
                kept_paths.append(instance_path)  # keep on error

        print(f"\nFilter: {len(kept_paths)}/{len(built_paths)} instances kept.\n")
    else:
        print("\n=== Step 3: Filter SKIPPED (no --filter-api-base provided) ===\n")
        kept_paths = built_paths

    # Step 4: Evaluate kept instances
    summary = RunSummary(run_name=run_dir.name, model="eval-only")

    for instance_path in kept_paths:
        instance_name = Path(instance_path).name
        print(f"=== Evaluating: {instance_name} ===")

        try:
            # Image already built (cached), just create a fresh container
            container_id = sandbox.create(instance_path)
            tag = f"skillbench-{instance_name}".lower().replace(" ", "-")

            meta_path = Path(instance_path) / "container.json"
            meta_path.write_text(json.dumps({"container_id": container_id, "image_tag": tag}))

            result = evaluate_in_container(instance_path, container_id, sandbox)

            status = "PASS" if result.passed else "FAIL"
            print(f"  Result: [{status}] score={result.score:.2f}")

            save_result_to_run(result, instance_path, run_dir)
            summary.update_from_result(result)

            sandbox.destroy(container_id)
            meta_path.unlink(missing_ok=True)

        except Exception as e:
            print(f"  ERROR: {e}")

        print()

    # Save and print summary
    summary.save(str(run_dir / "summary.json"))
    print(f"=== Summary ({run_dir}) ===")
    print(f"Total: {summary.total}  Passed: {summary.passed}  Failed: {summary.failed}  Avg Score: {summary.avg_score:.2f}")


def main():
    parser = argparse.ArgumentParser(description="SkillBench: Skill Task Synthesis + Evaluation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # synthesize
    p_syn = subparsers.add_parser("synthesize", help="Synthesize task instances from a skill")
    p_syn.add_argument("--skill-dir", required=True, help="Path to skill directory")
    p_syn.add_argument("--num", type=int, default=10, help="Number of instances to generate")
    p_syn.add_argument("--output-dir", default="instances", help="Output directory")

    # build
    p_build = subparsers.add_parser("build", help="Build Docker sandbox for an instance")
    p_build.add_argument("--instance", required=True, help="Path to instance directory")

    # evaluate
    p_eval = subparsers.add_parser("evaluate", help="Evaluate a completed instance")
    p_eval.add_argument("--instance", required=True, help="Path to instance directory")
    p_eval.add_argument("--workspace", help="Path to workspace directory (if not using container)")
    p_eval.add_argument("--run-dir", help="Directory to save results (default: results/run_{timestamp})")

    # destroy
    p_destroy = subparsers.add_parser("destroy", help="Destroy container for an instance")
    p_destroy.add_argument("--instance", required=True, help="Path to instance directory")

    # cleanup
    subparsers.add_parser("cleanup", help="Remove all skillbench containers and stale container.json files")

    # filter
    p_filter = subparsers.add_parser("filter", help="Filter out too-easy (all pass) and unsolvable (none pass) tasks")
    p_filter.add_argument("--instance", help="Path to a single instance directory (omit for batch mode)")
    p_filter.add_argument("--output-dir", default="instances", help="Directory containing instances (batch mode)")
    p_filter.add_argument("--api-base", required=True, help="vLLM/OpenAI-compatible API base URL")
    p_filter.add_argument("--model", required=True, help="Model name for agent trials")
    p_filter.add_argument("--num-trials", type=int, default=16, help="Number of agent trials per instance")
    p_filter.add_argument("--concurrency", type=int, default=4, help="Number of parallel agent trials")
    p_filter.add_argument("--force", action="store_true", help="Re-filter already filtered instances")

    # filter_terminus
    p_filter_terminus = subparsers.add_parser("filter_terminus", help="Filter tasks using Terminus-2 style agent")
    p_filter_terminus.add_argument("--instance", help="Path to a single instance directory (omit for batch mode)")
    p_filter_terminus.add_argument("--output-dir", default="instances", help="Directory containing instances (batch mode)")
    p_filter_terminus.add_argument("--provider", choices=["openai", "claude"], default="openai", help="LLM provider")
    p_filter_terminus.add_argument("--model", required=True, help="Model name for agent trials")
    p_filter_terminus.add_argument("--api-base", help="API base URL (for OpenAI-compatible APIs)")
    p_filter_terminus.add_argument("--api-key", help="API key (or set ANTHROPIC_AUTH_TOKEN for Claude)")
    p_filter_terminus.add_argument("--num-trials", type=int, default=16, help="Number of agent trials per instance")
    p_filter_terminus.add_argument("--concurrency", type=int, default=4, help="Number of parallel agent trials")
    p_filter_terminus.add_argument("--max-iterations", type=int, default=30, help="Max iterations per trial")
    p_filter_terminus.add_argument("--force", action="store_true", help="Re-filter already filtered instances")

    # all
    p_all = subparsers.add_parser("all", help="Full pipeline: synthesize + build + filter + evaluate")
    p_all.add_argument("--skill-dir", required=True, help="Path to skill directory")
    p_all.add_argument("--num", type=int, default=10, help="Number of instances to generate")
    p_all.add_argument("--output-dir", default="instances", help="Output directory")
    p_all.add_argument("--run-dir", help="Directory to save results (default: results/run_{timestamp})")
    p_all.add_argument("--filter-api-base", help="API base URL for filter agent (omit to skip filtering)")
    p_all.add_argument("--filter-model", default="Qwen3.5-27B", help="Model for filter agent trials")
    p_all.add_argument("--filter-num-trials", type=int, default=16, help="Number of filter trials per instance")
    p_all.add_argument("--filter-concurrency", type=int, default=4, help="Parallel filter trials")

    args = parser.parse_args()

    commands = {
        "synthesize": cmd_synthesize,
        "build": cmd_build,
        "evaluate": cmd_evaluate,
        "destroy": cmd_destroy,
        "cleanup": cmd_cleanup,
        "filter": cmd_filter,
        "filter_terminus": cmd_filter_terminus,
        "all": cmd_all,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
