import sys
import json
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace).resolve()
    checks = []
    passed_all = True

    # ── Locate audit_manifest.txt anywhere in workspace ──────────────
    candidates = list(ws.rglob("audit_manifest.txt"))

    def fail(name, detail):
        nonlocal passed_all
        passed_all = False
        checks.append({"name": name, "passed": False, "detail": detail})

    def ok(name, detail):
        checks.append({"name": name, "passed": True, "detail": detail})

    if not candidates:
        fail("file_exists", "audit_manifest.txt not found anywhere in workspace")
        return passed_all, checks

    manifest_path = candidates[0]
    ok("file_exists", f"Found at {manifest_path}")

    # ── Read content ──────────────────────────────────────────────────
    try:
        raw = manifest_path.read_text().strip()
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
    except Exception as e:
        fail("file_readable", f"Could not read manifest: {e}")
        return passed_all, checks

    if not lines:
        fail("file_not_empty", "audit_manifest.txt is empty")
        return passed_all, checks
    ok("file_not_empty", f"{len(lines)} lines found")

    # ── Derive expected targets using fd directly (ground truth) ──────
    # The ground truth: .tmp files, including gitignored (-I),
    # changed within 4d and before 1d, size under 100k, type file, absolute paths
    try:
        result = subprocess.run(
            [
                "fd",
                "--type", "f",
                "--extension", "tmp",
                "--changed-within", "4d",
                "--changed-before", "1d",
                "--size", "-100k",
                "--absolute-path",
                "--no-ignore",   # same as -I: include gitignored
                ".",
                str(ws),
            ],
            capture_output=True, text=True, check=True
        )
        expected_paths = sorted(
            p.strip() for p in result.stdout.splitlines() if p.strip()
        )
    except Exception as e:
        fail("ground_truth_computation", f"Could not run fd to compute expected: {e}")
        return passed_all, checks

    if not expected_paths:
        fail("ground_truth_nonempty", "Ground truth produced zero files — check workspace setup")
        return passed_all, checks

    ok("ground_truth_computed", f"Expected {len(expected_paths)} files: {expected_paths}")

    # ── Check: all paths are absolute ────────────────────────────────
    non_absolute = [l for l in lines if not l.startswith("/")]
    if non_absolute:
        fail("absolute_paths", f"Non-absolute paths found: {non_absolute[:5]}")
    else:
        ok("absolute_paths", "All paths are absolute")

    # ── Check: correct set of files ───────────────────────────────────
    agent_set = set(lines)
    expected_set = set(expected_paths)

    missing = sorted(expected_set - agent_set)
    extra   = sorted(agent_set - expected_set)

    if missing:
        fail("no_missing_files", f"Missing {len(missing)} expected file(s): {missing}")
    else:
        ok("no_missing_files", "All expected files are present")

    if extra:
        fail("no_extra_files", f"Extra {len(extra)} unexpected file(s): {extra}")
    else:
        ok("no_extra_files", "No extra files included")

    # ── Check: sorted order ───────────────────────────────────────────
    if lines == sorted(lines):
        ok("sorted_order", "Lines are sorted alphabetically")
    else:
        fail("sorted_order", f"Lines are not sorted. Got: {lines[:5]}, expected: {sorted(lines)[:5]}")

    # ── Check: gitignored files ARE included (key trap) ───────────────
    gitignored_keywords = ["build/", "cache/"]
    found_gitignored = any(
        any(kw in l for kw in gitignored_keywords) for l in lines
    )
    if found_gitignored:
        ok("includes_gitignored", "Manifest includes files from gitignored directories (correct -I usage)")
    else:
        fail("includes_gitignored", "No files from gitignored dirs (build/, cache/) found — agent likely forgot -I / --no-ignore flag")

    # ── Check: size constraint respected (no >100k files) ─────────────
    oversized = []
    for l in lines:
        try:
            sz = Path(l).stat().st_size
            if sz >= 100_000:
                oversized.append((l, sz))
        except Exception:
            pass
    if oversized:
        fail("size_constraint", f"Files exceeding 100k found: {oversized}")
    else:
        ok("size_constraint", "All listed files are under 100k")

    # ── Check: extension constraint (.tmp only) ────────────────────────
    wrong_ext = [l for l in lines if not l.endswith(".tmp")]
    if wrong_ext:
        fail("extension_constraint", f"Non-.tmp files found: {wrong_ext}")
    else:
        ok("extension_constraint", "All listed files have .tmp extension")

    return passed_all, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        passed_all, checks = run_checks(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }))
        return

    n = len(checks)
    n_passed = sum(1 for c in checks if c["passed"])
    score = round(n_passed / n, 4) if n > 0 else 0.0

    print(json.dumps({
        "passed": passed_all,
        "score": score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    main()