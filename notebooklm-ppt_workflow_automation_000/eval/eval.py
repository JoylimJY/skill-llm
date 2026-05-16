#!/usr/bin/env python3
"""
Evaluation script for the NotebookLM PPT generation task.
Checks:
1. nlm workflow was followed (correct command sequence)
2. Template from references/templates.md was used (not custom text)
3. --confirm flag was used in slides create
4. Artifact ID was correctly passed to download
5. PPTX file named arch_review.pptx exists
6. File was copied to ~/.openclaw/media/inbound/
7. message was called with the file and correct message text
"""

import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
score_weights = []

def check(name, weight=1.0):
    def decorator(fn):
        try:
            passed, detail = fn()
        except Exception as e:
            passed, detail = False, f"Exception: {e}"
        checks.append({"name": name, "passed": passed, "detail": detail})
        score_weights.append((passed, weight))
        return fn
    return decorator

# ── Load mock state ────────────────────────────────────────────────────────────
STATE_FILE = Path("/tmp/nlm_mock_state/state.json")
CALL_LOG = Path("/tmp/nlm_mock_state/call_log.jsonl")
MESSAGE_LOG = Path("/tmp/nlm_mock_state/message_log.jsonl")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def load_call_log():
    if not CALL_LOG.exists():
        return []
    calls = []
    for line in CALL_LOG.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                calls.append(json.loads(line))
            except:
                pass
    return calls

def load_message_log():
    if not MESSAGE_LOG.exists():
        return []
    msgs = []
    for line in MESSAGE_LOG.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                msgs.append(json.loads(line))
            except:
                pass
    return msgs

state = load_state()
calls = load_call_log()
messages = load_message_log()

# ── Check 1: nlm doctor was called ───────────────────────────────────────────
@check("nlm_doctor_called", weight=0.5)
def check_doctor():
    for c in calls:
        if c.get("args") == ["doctor"]:
            return True, "nlm doctor was called"
    return False, "nlm doctor was not called — authentication check skipped"

# ── Check 2: Notebook was created ─────────────────────────────────────────────
@check("notebook_created", weight=1.0)
def check_notebook():
    notebooks = state.get("notebooks", {})
    if notebooks:
        names = [v.get("name", "") for v in notebooks.values()]
        return True, f"Notebook(s) created: {names}"
    return False, "No notebooks were created"

# ── Check 3: Source was added ─────────────────────────────────────────────────
@check("source_added", weight=1.0)
def check_source():
    sources = state.get("sources", {})
    if sources:
        refs = [v.get("ref", "") for v in sources.values()]
        return True, f"Source(s) added: {refs}"
    return False, "No sources were added to any notebook"

# ── Check 4: Query was made with template content ─────────────────────────────
@check("query_uses_template_content", weight=2.0)
def check_query_template():
    """
    The agent MUST use content from references/templates.md.
    We check for key phrases from the Sharp-edged Minimalism or Neo-Retro Dev templates
    (both are appropriate for a technical/architecture audience).
    """
    queries = state.get("queries", {})
    if not queries:
        return False, "No queries were made"
    
    all_queries = []
    for nb_queries in queries.values():
        all_queries.extend(nb_queries)
    
    query_text = " ".join(all_queries).lower()
    
    # Check for template content from any technically appropriate template
    # Sharp-edged Minimalism key phrases
    sharp_signals = [
        "sharp-edged minimalism",
        "deep navy",
        "0a0e2a",
        "electric cyan",
        "00e5ff",
        "jetbrains mono",
        "space grotesk",
        "asymmetric grid",
        "diagonal cut",
    ]
    # Neo-Retro Dev key phrases
    retro_signals = [
        "neo-retro",
        "phosphor green",
        "39ff14",
        "charcoal",
        "1a1a2e",
        "fira code",
        "terminal",
        "scan-line",
        "ascii-art",
    ]
    
    sharp_matches = [s for s in sharp_signals if s in query_text]
    retro_matches = [s for s in retro_signals if s in query_text]
    
    if len(sharp_matches) >= 2 or len(retro_matches) >= 2:
        template_used = "Sharp-edged Minimalism" if sharp_matches else "Neo-Retro Dev"
        return True, f"Query contains official template content from '{template_used}'. Matched signals: {sharp_matches or retro_matches}"
    
    # Check if they used any other official template at all (partial credit detection)
    other_template_signals = [
        "modern newspaper",
        "playfair display",
        "d32f2f",
        "yellow.*black",
        "ffd600",
        "manga",
        "screentone",
        "neo-retro",
        "premium studio",
        "263238",
    ]
    other_matches = [s for s in other_template_signals if re.search(s, query_text)]
    
    if other_matches:
        return False, f"Used a non-technical template (found: {other_matches}). For architecture content, should use Sharp-edged Minimalism or Neo-Retro Dev from templates.md"
    
    # Check if they wrote custom style (not from template)
    if len(query_text) > 50:
        return False, f"Query exists but does NOT contain any official template content from references/templates.md. Query preview: '{' '.join(all_queries)[:200]}'"
    
    return False, "Query was empty or too short to contain a proper template"

# ── Check 5: slides create was called with --confirm ─────────────────────────
@check("slides_create_with_confirm", weight=2.0)
def check_slides_confirm():
    for c in calls:
        args = c.get("args", [])
        if len(args) >= 2 and args[0] == "slides" and args[1] == "create":
            if "--confirm" in args:
                return True, f"slides create called with --confirm flag: {args}"
            else:
                return False, f"slides create was called but WITHOUT --confirm flag: {args}"
    return False, "nlm slides create was never called"

# ── Check 6: slides create called only once ───────────────────────────────────
@check("slides_create_not_duplicated", weight=0.5)
def check_no_duplicate_slides():
    create_calls = [c for c in calls 
                    if len(c.get("args",[])) >= 2 and c["args"][0] == "slides" and c["args"][1] == "create"]
    if len(create_calls) == 0:
        return False, "slides create was never called"
    elif len(create_calls) == 1:
        return True, "slides create was called exactly once (correct)"
    else:
        return False, f"slides create was called {len(create_calls)} times — should only be called once!"

# ── Check 7: Artifact ID correctly used in download ──────────────────────────
@check("artifact_id_used_in_download", weight=2.0)
def check_artifact_id():
    # Get artifact IDs that were created
    all_slides = state.get("slides", {})
    created_ids = set()
    for nb_slides in all_slides.values():
        for s in nb_slides:
            created_ids.add(s["artifact_id"])
    
    if not created_ids:
        return False, "No slides were created, so no artifact ID exists"
    
    # Check download calls
    for c in calls:
        args = c.get("args", [])
        if len(args) >= 2 and args[0] == "download" and args[1] == "slide-deck":
            # Find --id value
            for i, a in enumerate(args):
                if a == "--id" and i + 1 < len(args):
                    used_id = args[i+1]
                    if used_id in created_ids:
                        return True, f"Correct Artifact ID '{used_id}' was used in download command"
                    else:
                        return False, f"Download used artifact ID '{used_id}' but valid IDs are: {created_ids}"
            return False, f"download slide-deck called but without --id flag: {args}"
    
    downloads = state.get("downloads", {})
    if downloads:
        return True, f"Downloads recorded in state: {downloads}"
    
    return False, "nlm download slide-deck was never called"

# ── Check 8: PPTX file named arch_review.pptx exists ─────────────────────────
@check("pptx_file_exists", weight=1.5)
def check_pptx_exists():
    # Search in workspace and common locations
    search_paths = [
        workspace,
        Path.home(),
        Path("/tmp"),
        Path.home() / ".openclaw" / "media" / "inbound",
    ]
    
    found_files = []
    for sp in search_paths:
        try:
            for f in sp.rglob("arch_review.pptx"):
                found_files.append(str(f))
        except:
            pass
    
    if found_files:
        return True, f"arch_review.pptx found at: {found_files}"
    return False, "arch_review.pptx not found in workspace or expected locations"

# ── Check 9: File copied to ~/.openclaw/media/inbound/ ───────────────────────
@check("file_in_openclaw_inbound", weight=1.5)
def check_openclaw_inbound():
    inbound = Path.home() / ".openclaw" / "media" / "inbound"
    pptx_files = list(inbound.glob("*.pptx"))
    if pptx_files:
        names = [f.name for f in pptx_files]
        return True, f"PPTX file(s) found in ~/.openclaw/media/inbound/: {names}"
    return False, f"No PPTX files found in {inbound}"

# ── Check 10: message command was called with file and correct message ─────────
@check("message_sent_with_file_and_text", weight=2.0)
def check_message_sent():
    if not messages:
        return False, "message CLI was never called"
    
    for msg in messages:
        parsed = msg.get("parsed", {})
        args = msg.get("args", [])
        
        # Check for filePath
        file_path = parsed.get("filePath", "")
        has_pptx = ".pptx" in file_path.lower() if file_path else False
        
        # Also check raw args for filePath
        if not has_pptx:
            for i, a in enumerate(args):
                if "--filePath" in a or ("filePath" in str(a)):
                    if i + 1 < len(args) and ".pptx" in args[i+1].lower():
                        has_pptx = True
                        file_path = args[i+1]
                        break
        
        # Check message text contains expected content
        msg_text = parsed.get("text", parsed.get("message", parsed.get("body", ""))).lower()
        if not msg_text:
            # Search in raw args
            for a in args:
                if isinstance(a, str) and ("architecture" in a.lower() or "slides" in a.lower() or "board" in a.lower()):
                    msg_text = a.lower()
                    break
        
        has_relevant_text = any(kw in msg_text for kw in [
            "architecture", "slides", "board", "presentation", "q2", "platform"
        ])
        
        if has_pptx and has_relevant_text:
            return True, f"message sent with PPTX attachment ({file_path}) and relevant text"
        elif has_pptx:
            return False, f"message sent with PPTX file but message text '{msg_text}' doesn't mention architecture/slides/board/Q2"
        elif has_relevant_text:
            return False, f"message sent with relevant text but no PPTX file attachment (filePath missing or not .pptx)"
    
    all_msg_previews = [str(m.get("parsed", {}))[:100] for m in messages]
    return False, f"message called but missing PPTX attachment or relevant message text. Calls: {all_msg_previews}"

# ── Check 11: --format pptx was used in download ──────────────────────────────
@check("download_format_pptx", weight=0.5)
def check_download_format():
    for c in calls:
        args = c.get("args", [])
        if len(args) >= 2 and args[0] == "download" and args[1] == "slide-deck":
            if "--format" in args:
                idx = args.index("--format")
                if idx + 1 < len(args) and args[idx+1] == "pptx":
                    return True, "download used --format pptx"
                else:
                    fmt_val = args[idx+1] if idx+1 < len(args) else "missing"
                    return False, f"download used --format {fmt_val} instead of pptx"
            # If no --format flag, the default is pptx - check downloads state
            downloads = state.get("downloads", {})
            for nb_id, dl in downloads.items():
                if dl.get("format") == "pptx":
                    return True, "download completed with pptx format (default)"
    return False, "download slide-deck was not called or --format pptx not specified"

# ── Compute final score ────────────────────────────────────────────────────────
total_weight = sum(w for _, w in score_weights)
earned_weight = sum(w for passed, w in score_weights if passed)
score = earned_weight / total_weight if total_weight > 0 else 0.0
overall_passed = score >= 0.75

result = {
    "passed": overall_passed,
    "score": round(score, 4),
    "checks": checks
}

print(json.dumps(result, indent=2, ensure_ascii=False))