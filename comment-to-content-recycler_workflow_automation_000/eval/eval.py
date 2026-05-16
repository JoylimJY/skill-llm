import sys
import json
import re
from pathlib import Path

def load_output(workspace):
    """Find content_backlog.json anywhere in the workspace."""
    candidates = list(Path(workspace).rglob("content_backlog.json"))
    if not candidates:
        return None, "content_backlog.json not found anywhere in workspace"
    # Prefer the most recently created one if multiple
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    try:
        with open(candidates[0]) as f:
            data = json.load(f)
        return data, str(candidates[0])
    except Exception as e:
        return None, f"Failed to parse JSON: {e}"

def run_eval(workspace):
    checks = []
    data, location = load_output(workspace)

    # CHECK 0: File exists and is valid JSON
    file_exists = data is not None
    checks.append({
        "name": "output_file_exists_and_valid_json",
        "passed": file_exists,
        "detail": location
    })
    if not file_exists:
        return checks

    # ---- CHECK 1: Contains required top-level sections ----
    # Must have clusters (or similar key) and close_the_loop section
    data_str = json.dumps(data).lower()

    has_clusters = any(k in data for k in ["clusters", "intent_clusters", "content_clusters", "prioritized_clusters", "backlog"])
    checks.append({
        "name": "has_clusters_or_backlog_section",
        "passed": has_clusters,
        "detail": f"Top-level keys found: {list(data.keys())}"
    })

    has_close_loop = any(k in data for k in ["close_the_loop", "close_loop", "loop_closure", "follow_up", "next_steps"])
    checks.append({
        "name": "has_close_the_loop_section",
        "passed": has_close_loop,
        "detail": f"Top-level keys found: {list(data.keys())}"
    })

    # ---- CHECK 2: All 5 required intent cluster types present ----
    required_intents = ["how-to", "comparison", "troubleshooting", "buying concerns", "objections"]
    # Also allow slight variations
    intent_aliases = {
        "how-to": ["how-to", "how_to", "howto", "how to"],
        "comparison": ["comparison", "compare", "vs"],
        "troubleshooting": ["troubleshooting", "trouble shooting", "troubleshoot"],
        "buying concerns": ["buying concerns", "buying_concerns", "purchase concerns", "buying"],
        "objections": ["objections", "objections/myths", "myths", "objection"]
    }

    clusters_section = None
    for k in ["clusters", "intent_clusters", "content_clusters", "prioritized_clusters", "backlog"]:
        if k in data:
            clusters_section = data[k]
            break

    found_intents = set()
    if clusters_section:
        clusters_list = clusters_section if isinstance(clusters_section, list) else list(clusters_section.values())
        for cluster in clusters_list:
            cluster_str = json.dumps(cluster).lower()
            for intent, aliases in intent_aliases.items():
                if any(alias in cluster_str for alias in aliases):
                    found_intents.add(intent)

    all_intents_present = len(found_intents) >= 5
    checks.append({
        "name": "all_5_intent_cluster_types_present",
        "passed": all_intents_present,
        "detail": f"Found intent types: {list(found_intents)} (need all 5: {required_intents})"
    })

    # ---- CHECK 3: Scoring dimensions present ----
    # Must see all 4: frequency, urgency, monetization relevance, ease of production
    scoring_dims = ["frequency", "urgency", "monetization", "ease"]
    dims_found = [dim for dim in scoring_dims if dim in data_str]
    all_dims_present = len(dims_found) >= 4
    checks.append({
        "name": "all_4_scoring_dimensions_present",
        "passed": all_dims_present,
        "detail": f"Scoring dimensions found in output: {dims_found} (need: {scoring_dims})"
    })

    # ---- CHECK 4: Clusters are ranked/prioritized ----
    ranked = False
    if clusters_section and isinstance(clusters_section, list) and len(clusters_section) > 1:
        # Check if any cluster has a rank, priority, or score field
        rank_keywords = ["rank", "priority", "score", "order", "position"]
        for cluster in clusters_section:
            cluster_str_lower = json.dumps(cluster).lower()
            if any(kw in cluster_str_lower for kw in rank_keywords):
                ranked = True
                break
    # Also check if the list itself appears to be ordered (has ranking commentary)
    if "ranked" in data_str or "top cluster" in data_str or "rank" in data_str or "priority" in data_str:
        ranked = True
    checks.append({
        "name": "clusters_are_ranked_or_prioritized",
        "passed": ranked,
        "detail": f"Ranking found: {ranked}"
    })

    # ---- CHECK 5: Top clusters have exactly 3 hook options ----
    hooks_found = []
    three_hooks_count = 0
    if clusters_section:
        clusters_list = clusters_section if isinstance(clusters_section, list) else list(clusters_section.values())
        for cluster in clusters_list:
            cluster_str_lower = json.dumps(cluster).lower()
            # Look for hooks array/list
            if isinstance(cluster, dict):
                for k, v in cluster.items():
                    if "hook" in k.lower() and isinstance(v, list):
                        hooks_found.append(len(v))
                        if len(v) == 3:
                            three_hooks_count += 1

    # At least 1 top cluster should have exactly 3 hooks
    has_three_hooks = three_hooks_count >= 1 or ("hook" in data_str and data_str.count('"hook') >= 3)
    # More lenient: look for "hooks" array with 3 items across the entire document
    if not has_three_hooks:
        # Try to find any list of 3 hooks somewhere
        full_str = json.dumps(data)
        hook_lists = re.findall(r'"hooks"\s*:\s*\[([^\]]+)\]', full_str, re.IGNORECASE)
        for hl in hook_lists:
            # Count items (rough: count quoted strings)
            items = re.findall(r'"[^"]{5,}"', hl)
            if len(items) >= 3:
                has_three_hooks = True
                break
    checks.append({
        "name": "top_clusters_have_3_hook_options",
        "passed": has_three_hooks,
        "detail": f"Hook lists with exactly 3 items found in clusters: {three_hooks_count}. Hook lengths seen: {hooks_found}"
    })

    # ---- CHECK 6: Script angle present for top clusters ----
    has_script_angle = "script" in data_str and ("angle" in data_str or "script_angle" in data_str or "script angle" in data_str)
    checks.append({
        "name": "script_angle_present",
        "passed": has_script_angle,
        "detail": f"'script angle' or 'script_angle' found in output: {has_script_angle}"
    })

    # ---- CHECK 7: CTA tied to audience language ----
    has_cta = "cta" in data_str or "call to action" in data_str or "call_to_action" in data_str
    checks.append({
        "name": "cta_present",
        "passed": has_cta,
        "detail": f"CTA field found: {has_cta}"
    })

    # ---- CHECK 8: Audience language preserved (real phrases from comments) ----
    # Check that some actual phrases from the raw comments appear in output
    audience_phrases = [
        "google home", "zigbee", "sunrise", "wifi", "home assistant",
        "hubitat", "$129", "philips hue", "monthly", "gimmick",
        "hacked", "listening", "local processing", "non-tech",
        "3am", "daylight", "timezone", "pairing", "reset"
    ]
    phrases_found = [p for p in audience_phrases if p.lower() in data_str.lower()]
    audience_language_preserved = len(phrases_found) >= 4
    checks.append({
        "name": "audience_language_preserved_in_output",
        "passed": audience_language_preserved,
        "detail": f"Audience phrases preserved: {phrases_found} ({len(phrases_found)}/20)"
    })

    # ---- CHECK 9: Close the loop section has reply priority AND follow-up question ----
    loop_section = None
    for k in ["close_the_loop", "close_loop", "loop_closure", "follow_up", "next_steps"]:
        if k in data:
            loop_section = data[k]
            break

    has_reply_priority = False
    has_followup_question = False
    if loop_section:
        loop_str = json.dumps(loop_section).lower()
        has_reply_priority = any(kw in loop_str for kw in ["reply", "respond", "comment", "first", "priorit"])
        has_followup_question = any(kw in loop_str for kw in ["follow", "question", "ask", "signal", "demand"])
    # Also check globally if loop section key wasn't found explicitly
    if not has_reply_priority:
        has_reply_priority = ("reply first" in data_str or "reply to" in data_str or "comments to reply" in data_str)
    if not has_followup_question:
        has_followup_question = ("follow-up question" in data_str or "follow up question" in data_str or "followup" in data_str)

    checks.append({
        "name": "close_loop_has_reply_priority",
        "passed": has_reply_priority,
        "detail": f"Reply priority found in close-the-loop section: {has_reply_priority}"
    })
    checks.append({
        "name": "close_loop_has_followup_question",
        "passed": has_followup_question,
        "detail": f"Follow-up question found in close-the-loop section: {has_followup_question}"
    })

    # ---- CHECK 10: Deduplication/normalization was applied ----
    # Verify that spam/noise comments (c036-c040) are not listed as content ideas
    # and that duplicates (c001/c002/c032 all about google home) are merged into one cluster
    spam_phrases = ["buy cheap", "first!", "keep it up", "great video as always", "myspamsite"]
    spam_leaked = any(phrase in data_str.lower() for phrase in spam_phrases)
    checks.append({
        "name": "spam_and_noise_filtered_out",
        "passed": not spam_leaked,
        "detail": f"Spam/noise phrases leaked into output: {spam_leaked}"
    })

    # ---- COMPUTE SCORE ----
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    # Overall pass requires at least 9/11 checks
    overall_pass = passed_count >= 9

    return checks, score, overall_pass


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

    try:
        result = run_eval(workspace)
        if isinstance(result, list):
            # Error path from load_output
            checks = result
            score = 0.0
            overall_pass = False
        else:
            checks, score, overall_pass = result
    except Exception as e:
        checks = [{"name": "eval_runtime_error", "passed": False, "detail": str(e)}]
        score = 0.0
        overall_pass = False

    output = {
        "passed": overall_pass,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()