import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── Check 1: docs-registry.json contains 'meridian' entry ───────────────────
registry_path = Path(workspace) / "docs-registry.json"
meridian_entry = None
try:
    with open(registry_path) as f:
        registry = json.load(f)
    
    if "meridian" not in registry:
        check("registry_has_meridian", False, "Key 'meridian' not found in docs-registry.json")
    else:
        meridian_entry = registry["meridian"]
        check("registry_has_meridian", True, f"Found 'meridian' key in registry")
except Exception as e:
    check("registry_has_meridian", False, f"Could not read docs-registry.json: {e}")

# ── Check 2: meridian entry has correct 'url' field pointing to localhost:9876
if meridian_entry is not None:
    url_val = meridian_entry.get("url", "")
    url_ok = "localhost:9876" in url_val or "127.0.0.1:9876" in url_val
    check(
        "meridian_url_correct",
        url_ok,
        f"url='{url_val}' — expected 'http://localhost:9876' (or 127.0.0.1:9876)"
    )
else:
    check("meridian_url_correct", False, "meridian entry missing, cannot check url field")

# ── Check 3: meridian entry has 'llms' field referencing llms-full.txt ────────
if meridian_entry is not None:
    llms_val = meridian_entry.get("llms", "")
    llms_ok = "llms-full.txt" in llms_val
    check(
        "meridian_llms_field",
        llms_ok,
        f"llms='{llms_val}' — expected path containing 'llms-full.txt'"
    )
else:
    check("meridian_llms_field", False, "meridian entry missing, cannot check llms field")

# ── Check 4: meridian entry uses correct registry format (is a dict with url) ─
if meridian_entry is not None:
    is_dict = isinstance(meridian_entry, dict)
    has_url = "url" in meridian_entry
    format_ok = is_dict and has_url
    check(
        "registry_format_valid",
        format_ok,
        f"Entry is dict={is_dict}, has 'url' key={has_url}"
    )
else:
    check("registry_format_valid", False, "No meridian entry to validate format")

# ── Check 5: meridian-docs.txt file exists somewhere in workspace ────────────
saved_files = list(Path(workspace).rglob("meridian-docs.txt"))
if saved_files:
    saved_path = saved_files[0]
    check("saved_file_exists", True, f"Found saved file at {saved_path}")
else:
    check("saved_file_exists", False, "meridian-docs.txt not found anywhere in workspace")
    saved_path = None

# ── Check 6: saved file contains the expected mock documentation content ─────
EXPECTED_MARKERS = [
    "Meridian Framework",
    "createPipeline",
    "SourceNode",
    "TransformNode",
    "MSDL",
]
if saved_path is not None:
    try:
        content = saved_path.read_text(encoding="utf-8")
        missing = [m for m in EXPECTED_MARKERS if m not in content]
        if missing:
            check(
                "saved_file_has_meridian_content",
                False,
                f"Missing expected markers: {missing}"
            )
        else:
            check(
                "saved_file_has_meridian_content",
                True,
                f"All {len(EXPECTED_MARKERS)} expected content markers found"
            )
    except Exception as e:
        check("saved_file_has_meridian_content", False, f"Could not read meridian-docs.txt: {e}")
else:
    check("saved_file_has_meridian_content", False, "saved file not found, skipping content check")

# ── Check 7: saved file does NOT contain metadata header (--raw was used) ────
METADATA_MARKERS = ["# Docs:", "# Source:", "# Fetched:", "# Size:"]
if saved_path is not None:
    try:
        content = saved_path.read_text(encoding="utf-8")
        found_meta = [m for m in METADATA_MARKERS if m in content]
        if found_meta:
            check(
                "saved_file_is_raw_no_metadata_header",
                False,
                f"Metadata header markers found (--raw was NOT used): {found_meta}"
            )
        else:
            check(
                "saved_file_is_raw_no_metadata_header",
                True,
                "No metadata header found — correctly used --raw flag"
            )
    except Exception as e:
        check("saved_file_is_raw_no_metadata_header", False, f"Could not read file: {e}")
else:
    check("saved_file_is_raw_no_metadata_header", False, "File not found, skipping raw check")

# ── Check 8: original registry entries are preserved (not wiped) ─────────────
try:
    with open(registry_path) as f:
        registry_final = json.load(f)
    preserved = all(k in registry_final for k in ["react", "nextjs", "prisma", "typescript"])
    check(
        "original_registry_entries_preserved",
        preserved,
        f"react/nextjs/prisma/typescript all present={preserved}"
    )
except Exception as e:
    check("original_registry_entries_preserved", False, f"Error reading registry: {e}")

# ── Score calculation ─────────────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
score = round(len(passed_checks) / len(checks), 4)
all_passed = len(passed_checks) == len(checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))