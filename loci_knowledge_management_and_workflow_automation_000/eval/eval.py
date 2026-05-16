import json
import sys
import math
from pathlib import Path

def load_json(path):
    with open(path) as f:
        return json.load(f)

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    palace_path = workspace / "data" / "lab_palace.json"
    export_path = workspace / "output" / "palace_snapshot.md"
    status_path = workspace / "output" / "palace_status.txt"

    checks = []
    total_score = 0.0
    max_score = 0.0

    # ── Helper ───────────────────────────────────────────────────────────────
    def check(name, weight, passed, detail):
        nonlocal total_score, max_score
        max_score += weight
        if passed:
            total_score += weight
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # ── Load palace ───────────────────────────────────────────────────────────
    palace = None
    try:
        palace = load_json(palace_path)
        check("palace_file_exists", 0.5, True, f"Loaded palace from {palace_path}")
    except Exception as e:
        check("palace_file_exists", 0.5, False, f"Could not load palace: {e}")
        # Return early — all other checks depend on palace
        score = total_score / max(max_score, 1)
        return checks, score

    memories = palace.get("memories", {})
    domains_config = palace.get("config", {}).get("domains", {})

    # ── CHECK 1: Custom domain 'protocols' added ──────────────────────────────
    has_protocols = "protocols" in domains_config
    check(
        "custom_domain_protocols_added", 1.5,
        has_protocols,
        f"'protocols' domain present: {has_protocols}. Domains found: {list(domains_config.keys())}"
    )

    # ── CHECK 2: New memories stored in required domains ──────────────────────
    # Agent must store at least 3 new memories across work/knowledge/protocols/people/tools
    # We look for memories NOT in the original seed IDs
    SEED_IDS = {"aabbcc11", "aabbcc22", "aabbcc33", "ddee1122", "ddee3344"}
    new_memories = {mid: m for mid, m in memories.items() if mid not in SEED_IDS}
    check(
        "new_memories_stored_minimum_3",
        1.5,
        len(new_memories) >= 3,
        f"New memories stored: {len(new_memories)} (need ≥3). IDs: {list(new_memories.keys())}"
    )

    # ── CHECK 3: At least one new memory in 'protocols' domain ───────────────
    protocols_mems = [m for m in new_memories.values() if m.get("domain") == "protocols"]
    check(
        "memory_stored_in_protocols_domain",
        1.5,
        len(protocols_mems) >= 1,
        f"Memories in 'protocols' domain: {len(protocols_mems)}"
    )

    # ── CHECK 4: New memories have tags ──────────────────────────────────────
    tagged = [m for m in new_memories.values() if m.get("tags") and len(m["tags"]) > 0]
    check(
        "new_memories_have_tags",
        1.0,
        len(tagged) >= 2,
        f"New memories with tags: {len(tagged)} out of {len(new_memories)}"
    )

    # ── CHECK 5: At least one bidirectional link exists ───────────────────────
    # A bidirectional link: if memory A links to B, memory B must link to A
    link_found = False
    link_detail = "No bidirectional links found"
    all_ids = list(memories.keys())
    for mid, mem in memories.items():
        for linked_id in mem.get("links", []):
            if linked_id in memories:
                reverse = memories[linked_id].get("links", [])
                if mid in reverse:
                    link_found = True
                    link_detail = f"Bidirectional link: {mid} <-> {linked_id}"
                    break
        if link_found:
            break
    check("bidirectional_link_exists", 2.0, link_found, link_detail)

    # ── CHECK 6: Stale memories pruned (below threshold 0.3) ─────────────────
    STALE_IDS = {"aabbcc11", "aabbcc22", "aabbcc33"}
    remaining_stale = [sid for sid in STALE_IDS if sid in memories]
    pruned_stale = [sid for sid in STALE_IDS if sid not in memories]
    all_pruned = len(remaining_stale) == 0
    check(
        "stale_memories_pruned",
        2.5,
        all_pruned,
        f"Pruned stale IDs: {pruned_stale}. Still present (should be gone): {remaining_stale}"
    )

    # ── CHECK 7: Fresh memories NOT pruned ───────────────────────────────────
    FRESH_IDS = {"ddee1122", "ddee3344"}
    remaining_fresh = [fid for fid in FRESH_IDS if fid in memories]
    check(
        "fresh_memories_retained",
        2.0,
        len(remaining_fresh) == 2,
        f"Fresh memories retained: {remaining_fresh} (need both {list(FRESH_IDS)})"
    )

    # ── CHECK 8: Export markdown file exists and has content ──────────────────
    export_ok = False
    export_detail = "Export file not found"
    try:
        if not export_path.exists():
            # Also search workspace output dirs
            candidates = list(workspace.rglob("palace_snapshot.md"))
            if candidates:
                export_path = candidates[0]
        content = export_path.read_text()
        # Markdown export should have headers and memory content
        has_markdown = "#" in content and len(content) > 100
        export_ok = has_markdown
        export_detail = f"Export file at {export_path}, size={len(content)} chars, has_headers={has_markdown}"
    except Exception as e:
        export_detail = f"Error reading export: {e}"
    check("export_markdown_created", 2.0, export_ok, export_detail)

    # ── CHECK 9: Status output file exists ────────────────────────────────────
    status_ok = False
    status_detail = "Status file not found"
    try:
        if not status_path.exists():
            candidates = list(workspace.rglob("palace_status.txt"))
            if candidates:
                status_path = candidates[0]
        txt = status_path.read_text()
        # Status should mention domains or memories
        status_ok = len(txt) > 20 and any(kw in txt.lower() for kw in ["domain", "memor", "palace", "work", "knowledge"])
        status_detail = f"Status file at {status_path}, size={len(txt)} chars, content_ok={status_ok}"
    except Exception as e:
        status_detail = f"Error reading status: {e}"
    check("status_output_captured", 1.0, status_ok, status_detail)

    # ── CHECK 10: Correct --palace flag used (verified indirectly by palace location) ─
    # The palace is at /workspace/data/lab_palace.json (non-default).
    # If all earlier checks pass with data from that file, the agent used --palace correctly.
    # We add a structural sanity check: palace must still have the version field.
    has_version = "version" in palace
    check(
        "palace_flag_used_correctly",
        1.0,
        has_version and palace_path.exists(),
        f"Palace at non-default path {palace_path} is valid: version={palace.get('version')}"
    )

    # ── Final score ───────────────────────────────────────────────────────────
    final_score = round(total_score / max(max_score, 1), 4)
    return checks, final_score


def main():
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_checks(workspace_dir)
    except Exception as e:
        checks = [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        score = 0.0

    passed = score >= 0.70
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()