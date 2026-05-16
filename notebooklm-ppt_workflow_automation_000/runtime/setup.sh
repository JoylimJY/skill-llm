#!/bin/bash
set -e

# ── Create ~/.openclaw/media/inbound directory ────────────────────────────────
mkdir -p ~/.openclaw/media/inbound

# ── Create the mock `nlm` CLI ─────────────────────────────────────────────────
cat > /usr/local/bin/nlm << 'NLMEOF'
#!/usr/bin/env python3
"""
Mock nlm (notebooklm-mcp-cli) CLI for testing purposes.
Simulates the full workflow and records all calls for evaluation.
"""
import sys
import os
import json
import time
import hashlib
from pathlib import Path

LOG_DIR = Path("/tmp/nlm_mock_state")
LOG_DIR.mkdir(exist_ok=True)

CALL_LOG = LOG_DIR / "call_log.jsonl"
STATE_FILE = LOG_DIR / "state.json"

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"notebooks": {}, "sources": {}, "queries": {}, "slides": {}, "downloads": {}}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def log_call(args):
    with open(CALL_LOG, "a") as f:
        f.write(json.dumps({"timestamp": time.time(), "args": args}) + "\n")

def main():
    args = sys.argv[1:]
    log_call(args)
    state = load_state()

    if not args:
        print("nlm: notebooklm-mcp-cli mock")
        print("Usage: nlm <command> [subcommand] [options]")
        sys.exit(0)

    cmd = args[0]

    # nlm doctor
    if cmd == "doctor":
        print("✓ Authentication: OK")
        print("✓ API endpoint: reachable")
        print("✓ CLI version: 1.4.2")
        sys.exit(0)

    # nlm notebook create <name>
    elif cmd == "notebook" and len(args) >= 3 and args[1] == "create":
        name = args[2]
        nb_id = "nb_" + hashlib.md5(name.encode()).hexdigest()[:8]
        state["notebooks"][nb_id] = {"name": name, "created": time.time()}
        save_state(state)
        print(f"✓ Notebook created")
        print(f"  ID: {nb_id}")
        print(f"  Name: {name}")
        sys.exit(0)

    # nlm source add <notebook_id> --url <url> OR --file <file>
    elif cmd == "source" and len(args) >= 3 and args[1] == "add":
        nb_id = args[2]
        source_ref = None
        for i, a in enumerate(args):
            if a in ("--url", "--file") and i + 1 < len(args):
                source_ref = args[i+1]
        if nb_id not in state["notebooks"]:
            print(f"Error: notebook {nb_id} not found", file=sys.stderr)
            sys.exit(1)
        src_id = "src_" + hashlib.md5((nb_id + str(source_ref)).encode()).hexdigest()[:8]
        state["sources"][src_id] = {"notebook_id": nb_id, "ref": source_ref}
        if "sources" not in state["notebooks"][nb_id]:
            state["notebooks"][nb_id]["sources"] = []
        state["notebooks"][nb_id]["sources"].append(src_id)
        save_state(state)
        print(f"✓ Source added to notebook {nb_id}")
        print(f"  Source ID: {src_id}")
        sys.exit(0)

    # nlm notebook query <notebook_id> <query_text>
    elif cmd == "notebook" and len(args) >= 4 and args[1] == "query":
        nb_id = args[2]
        query_text = " ".join(args[3:])
        if nb_id not in state["notebooks"]:
            print(f"Error: notebook {nb_id} not found", file=sys.stderr)
            sys.exit(1)
        if "queries" not in state:
            state["queries"] = {}
        if nb_id not in state["queries"]:
            state["queries"][nb_id] = []
        state["queries"][nb_id].append(query_text)
        save_state(state)
        print(f"✓ Query processed for notebook {nb_id}")
        print(f"  The style requirements have been recorded.")
        print(f"  Response: Understood. I will apply the specified style when generating slides.")
        sys.exit(0)

    # nlm slides create <notebook_id> --language <lang> --confirm
    elif cmd == "slides" and len(args) >= 3 and args[1] == "create":
        nb_id = args[2]
        has_confirm = "--confirm" in args
        language = "en"
        for i, a in enumerate(args):
            if a == "--language" and i + 1 < len(args):
                language = args[i+1]
        if nb_id not in state["notebooks"]:
            print(f"Error: notebook {nb_id} not found", file=sys.stderr)
            sys.exit(1)
        if not has_confirm:
            print("Error: --confirm flag required to create slides", file=sys.stderr)
            print("Use: nlm slides create <notebook_id> --language <lang> --confirm", file=sys.stderr)
            sys.exit(1)
        artifact_id = "art_" + hashlib.md5((nb_id + str(time.time())).encode()).hexdigest()[:12]
        if "slides" not in state:
            state["slides"] = {}
        if nb_id not in state["slides"]:
            state["slides"][nb_id] = []
        state["slides"][nb_id].append({"artifact_id": artifact_id, "language": language, "status": "processing"})
        save_state(state)
        print(f"✓ Slide generation initiated")
        print(f"  Notebook ID: {nb_id}")
        print(f"  Artifact ID: {artifact_id}")
        print(f"  Language: {language}")
        print(f"  Status: processing")
        sys.exit(0)

    # nlm studio status <notebook_id>
    elif cmd == "studio" and len(args) >= 3 and args[1] == "status":
        nb_id = args[2]
        if nb_id not in state["notebooks"]:
            print(f"Error: notebook {nb_id} not found", file=sys.stderr)
            sys.exit(1)
        slides = state.get("slides", {}).get(nb_id, [])
        if not slides:
            print(f"Status: no slides found for notebook {nb_id}", file=sys.stderr)
            sys.exit(1)
        # Mark as complete
        for s in slides:
            s["status"] = "complete"
        save_state(state)
        latest = slides[-1]
        print(f"✓ Studio Status for notebook {nb_id}")
        print(f"  Artifact ID: {latest['artifact_id']}")
        print(f"  Status: complete")
        print(f"  Ready for download")
        sys.exit(0)

    # nlm download slide-deck <notebook_id> --id <artifact_id> --format pptx
    elif cmd == "download" and len(args) >= 3 and args[1] == "slide-deck":
        nb_id = args[2]
        artifact_id = None
        fmt = "pptx"
        for i, a in enumerate(args):
            if a == "--id" and i + 1 < len(args):
                artifact_id = args[i+1]
            if a == "--format" and i + 1 < len(args):
                fmt = args[i+1]
        if not artifact_id:
            print("Error: --id <artifact_id> is required", file=sys.stderr)
            sys.exit(1)
        # Verify artifact exists
        slides = state.get("slides", {}).get(nb_id, [])
        valid_ids = [s["artifact_id"] for s in slides]
        if artifact_id not in valid_ids:
            print(f"Error: artifact {artifact_id} not found for notebook {nb_id}", file=sys.stderr)
            sys.exit(1)
        # Generate a real minimal PPTX using python-pptx
        output_file = f"arch_review.{fmt}"
        try:
            from pptx import Presentation
            from pptx.util import Inches, Pt
            from pptx.dml.color import RGBColor
            prs = Presentation()
            # Slide 1: Title
            slide_layout = prs.slide_layouts[0]
            slide = prs.slides.add_slide(slide_layout)
            slide.shapes.title.text = "Microservices Architecture"
            slide.placeholders[1].text = "Platform Engineering Review — Q2"
            # Slide 2: Content
            slide_layout2 = prs.slide_layouts[1]
            slide2 = prs.slides.add_slide(slide_layout2)
            slide2.shapes.title.text = "Service Decomposition"
            tf = slide2.placeholders[1].text_frame
            tf.text = "User Service • Order Service • Inventory Service • Notification Service"
            # Embed metadata
            from pptx.opc.constants import RELATIONSHIP_TYPE as RT
            core_props = prs.core_properties
            core_props.subject = f"artifact_id={artifact_id};notebook_id={nb_id};template=sharp_edged_minimalism"
            prs.save(output_file)
            print(f"✓ Download complete: {output_file}")
            print(f"  Format: {fmt}")
            print(f"  Artifact: {artifact_id}")
            # Record download
            if "downloads" not in state:
                state["downloads"] = {}
            state["downloads"][nb_id] = {"artifact_id": artifact_id, "file": output_file, "format": fmt}
            save_state(state)
        except Exception as e:
            # Fallback: write dummy file
            with open(output_file, "wb") as f:
                f.write(b"PK\x03\x04" + b"\x00" * 100)
            print(f"✓ Download complete (fallback): {output_file}")
            state["downloads"][nb_id] = {"artifact_id": artifact_id, "file": output_file, "format": fmt}
            save_state(state)
        sys.exit(0)

    else:
        print(f"nlm: unknown command '{' '.join(args)}'", file=sys.stderr)
        print("Available commands: doctor, notebook create, notebook query, source add,", file=sys.stderr)
        print("                   slides create, studio status, download slide-deck", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
NLMEOF

chmod +x /usr/local/bin/nlm

# ── Create the mock `message` CLI ─────────────────────────────────────────────
cat > /usr/local/bin/message << 'MSGEOF'
#!/usr/bin/env python3
"""
Mock message CLI for testing purposes.
Records all message calls for evaluation.
"""
import sys
import os
import json
import time
from pathlib import Path

LOG_DIR = Path("/tmp/nlm_mock_state")
LOG_DIR.mkdir(exist_ok=True)
MESSAGE_LOG = LOG_DIR / "message_log.jsonl"

def main():
    args = sys.argv[1:]
    record = {"timestamp": time.time(), "args": args}
    
    # Parse arguments
    parsed = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            key = args[i][2:]
            parsed[key] = args[i+1]
            i += 2
        else:
            i += 1
    
    record["parsed"] = parsed
    
    with open(MESSAGE_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")
    
    file_path = parsed.get("filePath", "")
    channel = parsed.get("channel", parsed.get("to", ""))
    text = parsed.get("text", parsed.get("message", parsed.get("body", "")))
    
    if file_path and not Path(file_path).exists():
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"✓ Message sent")
    if channel:
        print(f"  To: {channel}")
    if text:
        print(f"  Message: {text}")
    if file_path:
        print(f"  Attachment: {file_path}")

if __name__ == "__main__":
    main()
MSGEOF

chmod +x /usr/local/bin/message

# ── Initialize the mock state directory ──────────────────────────────────────
mkdir -p /tmp/nlm_mock_state

echo "Mock CLI setup complete."
echo "nlm binary: $(which nlm)"
echo "message binary: $(which message)"