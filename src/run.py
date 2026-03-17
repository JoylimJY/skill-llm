"""CLI entry point for SkillBench: synthesize / build / evaluate."""

import argparse
import json
import sys
from pathlib import Path

from .synthesizer import synthesize_skill, load_skill, write_instance_dir
from .sandbox import Sandbox
from .evaluator import evaluate, evaluate_in_container
from .schema import InstanceSpec


def cmd_synthesize(args):
    """Synthesize task instances from a skill directory."""
    print(f"Synthesizing {args.num} instances from {args.skill_dir}...")
    paths = synthesize_skill(args.skill_dir, args.num, args.output_dir)
    print(f"\nDone. Generated {len(paths)} instances:")
    for p in paths:
        print(f"  {p}")


def cmd_build(args):
    """Build Docker image and create sandbox for an instance."""
    sandbox = Sandbox()
    instance_dir = args.instance

    print(f"Building Docker image for {instance_dir}...")
    tag = sandbox.build(instance_dir)
    print(f"  Image: {tag}")

    print("Creating container and running setup...")
    container_id = sandbox.create(instance_dir)
    print(f"  Container: {container_id}")

    # Save container ID for later use
    meta_path = Path(instance_dir) / "container.json"
    meta_path.write_text(json.dumps({"container_id": container_id, "image_tag": tag}))
    print(f"  Container info saved to {meta_path}")


def cmd_evaluate(args):
    """Run evaluation on a completed instance."""
    instance_dir = args.instance

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

    # Save result
    result_path = Path(instance_dir) / "result.json"
    result_path.write_text(result.to_json())
    print(f"\n  Result saved to {result_path}")


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


def cmd_all(args):
    """Full pipeline: synthesize + build + evaluate all instances."""
    # Step 1: Synthesize
    print(f"=== Step 1: Synthesize {args.num} instances from {args.skill_dir} ===")
    paths = synthesize_skill(args.skill_dir, args.num, args.output_dir)
    print(f"Generated {len(paths)} instances.\n")

    sandbox = Sandbox()
    results = []

    for instance_path in paths:
        instance_name = Path(instance_path).name
        print(f"=== Processing: {instance_name} ===")

        # Step 2: Build
        try:
            print("  Building...")
            tag = sandbox.build(instance_path)
            print(f"  Creating container...")
            container_id = sandbox.create(instance_path)

            # Save container info
            meta_path = Path(instance_path) / "container.json"
            meta_path.write_text(json.dumps({"container_id": container_id, "image_tag": tag}))

            # Step 3: Evaluate (against gen_inputs output, before any task execution)
            print("  Evaluating...")
            result = evaluate_in_container(instance_path, container_id, sandbox)
            results.append(result)

            status = "PASS" if result.passed else "FAIL"
            print(f"  Result: [{status}] score={result.score:.2f}")

            # Save result
            result_path = Path(instance_path) / "result.json"
            result_path.write_text(result.to_json())

            # Cleanup
            sandbox.destroy(container_id)
            meta_path.unlink(missing_ok=True)

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append(None)

        print()

    # Summary
    print("=== Summary ===")
    total = len(results)
    passed = sum(1 for r in results if r and r.passed)
    failed = sum(1 for r in results if r and not r.passed)
    errors = sum(1 for r in results if r is None)
    print(f"Total: {total}  Passed: {passed}  Failed: {failed}  Errors: {errors}")


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

    # destroy
    p_destroy = subparsers.add_parser("destroy", help="Destroy container for an instance")
    p_destroy.add_argument("--instance", required=True, help="Path to instance directory")

    # all
    p_all = subparsers.add_parser("all", help="Full pipeline: synthesize + build + evaluate")
    p_all.add_argument("--skill-dir", required=True, help="Path to skill directory")
    p_all.add_argument("--num", type=int, default=10, help="Number of instances to generate")
    p_all.add_argument("--output-dir", default="instances", help="Output directory")

    args = parser.parse_args()

    commands = {
        "synthesize": cmd_synthesize,
        "build": cmd_build,
        "evaluate": cmd_evaluate,
        "destroy": cmd_destroy,
        "all": cmd_all,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
