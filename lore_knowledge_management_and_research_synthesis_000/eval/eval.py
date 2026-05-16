#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def load_calls(log_path="/tmp/lore_calls.jsonl"):
    calls = []
    try:
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    calls.append(json.loads(line))
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Warning: failed to read calls log: {e}", file=sys.stderr)
    return calls

def get_server_state():
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:7892/state", timeout=5) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return None

def evaluate(workspace):
    checks = []
    calls = load_calls()
    state = get_server_state()

    ingest_calls = [c for c in calls if c["tool"] == "ingest" and c.get("response", {}).get("success")]
    retain_calls = [c for c in calls if c["tool"] == "retain" and c.get("response", {}).get("success")]
    search_calls = [c for c in calls if c["tool"] == "search"]

    # --- CHECK 1: All three source documents were ingested ---
    # We look for content keywords from each file in successful ingestions
    sarah_keywords = ["Sarah", "sarah", "sarah_k", "Sarah K"]
    dev_keywords = ["Dev P", "Dev", "dev_p", "interactive walkthrough"]
    slack_keywords = ["Elena", "Shepherd.js", "product-decisions", "C01234567"]

    def content_matches(calls_list, keywords):
        for c in calls_list:
            payload_str = json.dumps(c.get("payload", {}))
            if any(kw in payload_str for kw in keywords):
                return True
        return False

    sarah_ingested = content_matches(ingest_calls, sarah_keywords)
    dev_ingested = content_matches(ingest_calls, dev_keywords)
    slack_ingested = content_matches(ingest_calls, slack_keywords)

    checks.append({
        "name": "sarah_k_interview_ingested",
        "passed": sarah_ingested,
        "detail": "Sarah K. interview transcript was ingested into Lore" if sarah_ingested else "Sarah K. interview transcript was NOT found in ingest calls"
    })
    checks.append({
        "name": "dev_p_interview_ingested",
        "passed": dev_ingested,
        "detail": "Dev P. interview transcript was ingested into Lore" if dev_ingested else "Dev P. interview transcript was NOT found in ingest calls"
    })
    checks.append({
        "name": "slack_export_ingested",
        "passed": slack_ingested,
        "detail": "Slack export was ingested into Lore" if slack_ingested else "Slack #product-decisions export was NOT found in ingest calls"
    })

    # --- CHECK 2: source_url was provided in all ingest calls ---
    all_have_source_url = all(
        bool(c.get("payload", {}).get("source_url"))
        for c in ingest_calls
    )
    num_ingest = len(ingest_calls)
    checks.append({
        "name": "source_url_in_all_ingest_calls",
        "passed": all_have_source_url and num_ingest >= 3,
        "detail": f"{num_ingest} ingest calls made; all have source_url: {all_have_source_url}"
    })

    # --- CHECK 3: source_name was provided in all ingest calls ---
    all_have_source_name = all(
        bool(c.get("payload", {}).get("source_name"))
        for c in ingest_calls
    )
    checks.append({
        "name": "source_name_in_all_ingest_calls",
        "passed": all_have_source_name and num_ingest >= 3,
        "detail": f"source_name present in all ingest calls: {all_have_source_name}"
    })

    # --- CHECK 4: project field set consistently on ingest calls ---
    projects_used = set(c.get("payload", {}).get("project", "") for c in ingest_calls)
    project_set = bool(projects_used - {""})
    checks.append({
        "name": "project_field_set_on_ingest",
        "passed": project_set and len(projects_used) <= 2,  # allow minor variation but must be set
        "detail": f"Projects used in ingest calls: {projects_used}"
    })

    # --- CHECK 5: A search was performed (any mode) ---
    search_performed = len(search_calls) >= 1
    checks.append({
        "name": "search_was_performed",
        "passed": search_performed,
        "detail": f"{len(search_calls)} search call(s) made" if search_performed else "No search calls were made"
    })

    # --- CHECK 6: A semantic search was used for conceptual/onboarding query ---
    # The SKILL.md says "semantic" is for conceptual queries ("user frustrations", "pain points")
    semantic_searches = [c for c in search_calls if c.get("payload", {}).get("mode") == "semantic"]
    # Check if any semantic search was about onboarding/user experience/pain points
    onboarding_concepts = ["onboard", "frustrat", "pain", "confus", "user experience", "ux"]
    semantic_for_concept = any(
        any(kw in json.dumps(c.get("payload", {})).lower() for kw in onboarding_concepts)
        for c in semantic_searches
    )
    checks.append({
        "name": "semantic_search_used_for_conceptual_query",
        "passed": semantic_for_concept,
        "detail": f"Found {len(semantic_searches)} semantic search(es); one targeted conceptual onboarding topic: {semantic_for_concept}"
    })

    # --- CHECK 7: retain was used (NOT ingest) for a short synthesized insight ---
    # Key discriminator: the synthesized finding must be short and use `retain`, not `ingest`
    retain_used = len(retain_calls) >= 1
    checks.append({
        "name": "retain_used_for_synthesized_insight",
        "passed": retain_used,
        "detail": f"{len(retain_calls)} retain call(s) made" if retain_used else "No retain calls — agent likely used ingest for the synthesized insight (wrong tool per SKILL.md)"
    })

    # --- CHECK 8: retain content is short/discrete (not a full doc dump) ---
    # SKILL.md: retain is for "short, discrete pieces of knowledge"
    retain_content_is_short = False
    if retain_calls:
        # All retain payloads should be short (< 500 chars of content)
        short_retains = [
            c for c in retain_calls
            if len(c.get("payload", {}).get("content", "")) < 600
        ]
        retain_content_is_short = len(short_retains) >= 1
    checks.append({
        "name": "retain_content_is_appropriately_short",
        "passed": retain_content_is_short,
        "detail": "At least one retain call has short, discrete content (<600 chars)" if retain_content_is_short else "No retain calls with appropriately short content found"
    })

    # --- CHECK 9: retain content references onboarding findings ---
    retain_mentions_onboarding = False
    if retain_calls:
        for c in retain_calls:
            content = c.get("payload", {}).get("content", "").lower()
            if any(kw in content for kw in ["onboard", "user", "walkthrough", "workspace", "confusion", "pain", "frustrat", "interview"]):
                retain_mentions_onboarding = True
                break
    checks.append({
        "name": "retain_content_references_onboarding_findings",
        "passed": retain_mentions_onboarding,
        "detail": "retain call content references onboarding-related user research findings" if retain_mentions_onboarding else "retain content does not reference user research/onboarding findings"
    })

    # --- CHECK 10: No ingest used where retain was appropriate (discriminator) ---
    # This checks that a long-form ingest was NOT also submitted for the synthesized finding
    # i.e., the agent didn't just call ingest for everything including the insight
    # We check: if retain was called, the agent demonstrated correct tool selection
    correct_tool_selection = retain_used  # Already covered, but scored separately for weight
    checks.append({
        "name": "correct_tool_selection_retain_vs_ingest",
        "passed": correct_tool_selection,
        "detail": "Agent correctly used retain (not ingest) for discrete synthesized knowledge" if correct_tool_selection else "Agent failed to use retain — did not demonstrate knowledge of retain vs ingest distinction"
    })

    # Score calculation: weighted
    weights = {
        "sarah_k_interview_ingested": 1.0,
        "dev_p_interview_ingested": 1.0,
        "slack_export_ingested": 1.0,
        "source_url_in_all_ingest_calls": 1.5,
        "source_name_in_all_ingest_calls": 0.5,
        "project_field_set_on_ingest": 0.5,
        "search_was_performed": 0.5,
        "semantic_search_used_for_conceptual_query": 1.5,
        "retain_used_for_synthesized_insight": 2.0,
        "retain_content_is_appropriately_short": 1.0,
        "retain_content_references_onboarding_findings": 1.0,
        "correct_tool_selection_retain_vs_ingest": 1.5,
    }
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"])
    score = round(earned / total_weight, 4)

    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))