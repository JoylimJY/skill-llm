import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    expected_files = ["optimization_plan.txt"]
    for fname in expected_files:
        fpath = workspace / fname
        try:
            exists = fpath.exists()
            checks.append({
                "name": f"file_exists:{fname}",
                "passed": bool(exists),
                "detail": "found" if exists else "missing"
            })
        except Exception as e:
            checks.append({
                "name": f"file_exists:{fname}",
                "passed": False,
                "detail": f"error checking existence: {e}"
            })

    text = None
    try:
        text = (workspace / "optimization_plan.txt").read_text(encoding="utf-8")
        lowered = re.sub(r"\s+", " ", text.lower())
        has_bottleneck = any(k in lowered for k in ["bottleneck", "coordination overhead", "latency"])
        has_two_recommendations = len(re.findall(r"\b(?:recommend|change|optimi[sz]e|parallel|cache|batch)\b", lowered)) >= 2
        has_risk = any(k in lowered for k in ["risk", "regression", "tradeoff"])
        checks.append({"name": "content_bottleneck", "passed": has_bottleneck, "detail": "mentions bottleneck/latency" if has_bottleneck else "missing expected bottleneck language"})
        checks.append({"name": "content_recommendations", "passed": has_two_recommendations, "detail": "contains at least two optimization-related recommendations" if has_two_recommendations else "insufficient recommendations"})
        checks.append({"name": "content_risk_note", "passed": has_risk, "detail": "contains a risk note" if has_risk else "missing risk/tradeoff note"})
    except Exception as e:
        checks.append({"name": "content_bottleneck", "passed": False, "detail": f"could not read output: {e}"})
        checks.append({"name": "content_recommendations", "passed": False, "detail": f"could not read output: {e}"})
        checks.append({"name": "content_risk_note", "passed": False, "detail": f"could not read output: {e}"})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get("passed"))
    result = {
        "passed": passed_count == total,
        "score": (passed_count / total) if total else 0.0,
        "checks": checks
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
