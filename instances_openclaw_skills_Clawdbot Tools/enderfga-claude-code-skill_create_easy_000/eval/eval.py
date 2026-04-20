import json
import os
import re
import sys
from pathlib import Path


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[\s\W_]+", " ", text)
    return text.strip()


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    try:
        target = workspace / "mcp_quickstart.md"
        if target.exists():
            try:
                text = target.read_text(encoding="utf-8")
                ntext = normalize(text)
                has_init = "initialize mcpsystem" in ntext or "initialize mcp system" in ntext or "initialize all configured servers" in ntext
                has_persist = "state persistence" in ntext or "createpersiststore" in ntext or "indexeddbstorage" in ntext or "localstorage" in ntext
                has_example = "example" in ntext or "```" in text
                passed = bool(has_init and has_persist and has_example)
                detail = "Contains required MCP initialization and persistence references." if passed else "Missing one or more required concepts: initialization, persistence, or example formatting."
            except Exception as e:
                passed = False
                detail = f"Could not read or parse mcp_quickstart.md: {e}"
        else:
            passed = False
            detail = "mcp_quickstart.md is missing."
        checks.append({"name": "markdown_created_with_required_content", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "markdown_created_with_required_content", "passed": False, "detail": f"Unexpected error: {e}"})

    try:
        marker = workspace / "skill_marker.txt"
        if marker.exists():
            try:
                text = marker.read_text(encoding="utf-8")
                passed = "MARKER_OPENCLAW_2025_01" in text
                detail = "Marker content verified." if passed else "Marker text not found in generated file."
            except Exception as e:
                passed = False
                detail = f"Could not read skill_marker.txt: {e}"
        else:
            passed = False
            detail = "skill_marker.txt is missing."
        checks.append({"name": "input_marker_present", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "input_marker_present", "passed": False, "detail": f"Unexpected error: {e}"})

    try:
        total = len(checks)
        passed_count = sum(1 for c in checks if c.get("passed"))
        score = (passed_count / total) if total else 0.0
        passed = all(c.get("passed") for c in checks) if checks else False
        print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
    except Exception:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}, ensure_ascii=False))


if __name__ == "__main__":
    main()
