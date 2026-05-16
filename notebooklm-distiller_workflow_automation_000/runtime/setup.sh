#!/bin/bash
set -e

# ─── 1. Create the skill directory structure ───────────────────────────────
mkdir -p ~/.openclaw/skills/notebooklm-distiller/scripts

# ─── 2. Create the mock `notebooklm` binary ────────────────────────────────
# This mock records all invocations so the eval can verify --writeback behavior
cat > /usr/local/bin/notebooklm << 'NLMEOF'
#!/usr/bin/env python3
"""
Mock notebooklm CLI. Records calls to /tmp/nlm_calls.jsonl for eval.
Simulates: list, ask, source add
"""
import sys, json, datetime, os, re

LOG_FILE = "/tmp/nlm_calls.jsonl"
args = sys.argv[1:]

def log_call(cmd, extra=None):
    entry = {"cmd": cmd, "args": args, "ts": datetime.datetime.utcnow().isoformat()}
    if extra:
        entry.update(extra)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

if not args:
    print("notebooklm: no subcommand given")
    sys.exit(1)

subcmd = args[0]

if subcmd == "list":
    log_call("list")
    print(json.dumps([
        {"id": "nb-qec-7f3a2b1c", "name": "Quantum Error Correction", "sources": 12},
        {"id": "nb-qcry-9d4e1a0f", "name": "Quantum Cryptography", "sources": 7},
        {"id": "nb-ml-3c2b1a0e", "name": "Machine Learning Fundamentals", "sources": 5},
    ]))

elif subcmd == "ask":
    log_call("ask")
    # Parse --notebook-id and --prompt
    nb_id = None
    prompt_text = None
    new_session = "--new" in args
    i = 0
    while i < len(args):
        if args[i] == "--notebook-id" and i+1 < len(args):
            nb_id = args[i+1]; i += 2
        elif args[i] == "--prompt" and i+1 < len(args):
            prompt_text = args[i+1]; i += 2
        else:
            i += 1

    # Detect Chinese language request
    is_chinese = prompt_text and "请用中文回答" in prompt_text

    if is_chinese:
        print("""## 摘要
量子纠错是量子计算的核心技术，通过冗余编码保护量子比特免受退相干影响。

## 关键要点
- 稳定子码是主流量子纠错框架
- 表面码具有最高的容错阈值（约1%）
- 逻辑量子比特需要数百个物理量子比特

## 约束条件
- 需要高保真度的量子门操作
- 物理量子比特数量随编码距离平方增长

## 权衡分析
- 更高的纠错能力需要更多物理资源
- 快速解码算法与准确性之间存在权衡

## 开放问题
- 如何在近期设备上实现容错阈值？
- 高效解码算法的可扩展性问题""")
    else:
        print("""## Summary
Quantum error correction protects quantum information from decoherence using redundant encoding.

## Key Points
- Stabilizer codes form the primary QEC framework
- Surface codes achieve highest fault-tolerance thresholds (~1%)

## Constraints
- Requires high-fidelity gate operations

## Trade-offs
- Higher correction capacity demands more physical resources

## Open Questions
- How to achieve fault-tolerance threshold on near-term devices?""")

elif subcmd == "source":
    if len(args) > 1 and args[1] == "add":
        # Parse args for source add
        nb_id = None
        title = None
        content_file = None
        i = 2
        while i < len(args):
            if args[i] == "--notebook-id" and i+1 < len(args):
                nb_id = args[i+1]; i += 2
            elif args[i] == "--title" and i+1 < len(args):
                title = args[i+1]; i += 2
            elif args[i] == "--file" and i+1 < len(args):
                content_file = args[i+1]; i += 2
            else:
                i += 1
        log_call("source_add", {"notebook_id": nb_id, "title": title, "file": content_file})
        print(json.dumps({"status": "ok", "source_id": "src-mock-001", "title": title}))
    else:
        print("notebooklm source: unknown subcommand")
        sys.exit(1)

elif subcmd == "login":
    log_call("login")
    os.makedirs(os.path.expanduser("~"), exist_ok=True)
    with open(os.path.expanduser("~/.book_client_session"), "w") as f:
        json.dump({"token": "mock-token-abc123", "expires": "2099-01-01"}, f)
    print("Login successful. Session saved to ~/.book_client_session")

else:
    log_call("unknown", {"subcmd": subcmd})
    print(f"notebooklm: unknown subcommand '{subcmd}'")
    sys.exit(1)
NLMEOF
chmod +x /usr/local/bin/notebooklm

# ─── 3. Create the mock distill.py ─────────────────────────────────────────
# This implements the actual distill logic per SKILL.md spec
cat > ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py << 'DISTILLEOF'
#!/usr/bin/env python3
"""
NotebookLM Distiller - distill.py (mock implementation per SKILL.md v2.0.0)
Subcommands: distill, research, persist, quiz, evaluate
"""
import sys, os, json, argparse, subprocess, datetime, re
from pathlib import Path

LOG_FILE = "/tmp/distill_calls.jsonl"

def log_call(data):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")

def get_notebooklm_bin(cli_path=None):
    return cli_path if cli_path else "notebooklm"

def run_nlm(args, cli_path=None):
    bin_ = get_notebooklm_bin(cli_path)
    result = subprocess.run([bin_] + args, capture_output=True, text=True)
    return result.stdout.strip()

def cmd_distill(args):
    log_call({"subcommand": "distill", "args": vars(args), "ts": datetime.datetime.utcnow().isoformat()})

    # List notebooks
    nlm_bin = get_notebooklm_bin(args.cli_path)
    notebooks_raw = run_nlm(["list"], args.cli_path)
    try:
        notebooks = json.loads(notebooks_raw)
    except Exception:
        print("ERROR: Could not parse notebook list", file=sys.stderr)
        sys.exit(1)

    # Find matching notebooks
    keywords = [k.lower() for k in args.keywords]
    matched = [nb for nb in notebooks if any(kw in nb["name"].lower() for kw in keywords)]

    if not matched:
        print(f"No notebooks found matching keywords: {args.keywords}")
        sys.exit(1)

    for nb in matched:
        nb_name = nb["name"]
        nb_id = nb["id"]
        today = datetime.date.today().isoformat()

        # Build prompt based on mode and language
        lang_prefix = "请用中文回答。\n" if args.lang == "zh" else ""
        if args.mode == "summary":
            prompt = lang_prefix + f"Please provide a structured summary of notebook '{nb_name}' with these sections: Summary, Key Points, Constraints, Trade-offs, Open Questions."
        elif args.mode == "glossary":
            prompt = lang_prefix + f"Extract 15-30 domain terms and definitions from notebook '{nb_name}'."
        else:  # qa
            prompt = lang_prefix + f"Generate 15-20 deep questions and answers about the content of notebook '{nb_name}'."

        # Call NLM
        answer = run_nlm(["ask", "--notebook-id", nb_id, "--prompt", prompt, "--new"], args.cli_path)

        # Build output filename
        mode_suffix = {"qa": "QA", "summary": "Summary", "glossary": "Glossary"}[args.mode]
        out_filename = f"{nb_name}_{mode_suffix}.md"

        # Build topic-slug for tags
        topic_slug = re.sub(r'[^a-z0-9]+', '-', args.topic.lower()).strip('-')

        # Build mode display name
        mode_display = {"qa": "Deep Q&A", "summary": "Structured Summary", "glossary": "Glossary"}[args.mode]

        # Build frontmatter
        frontmatter = f"""---
title: "{nb_name} | {mode_display}"
date: {today}
type: knowledge-note
author: notebooklm-distiller
tags: ["distillation", "{args.mode}", "{topic_slug}"]
source: "NotebookLM/{nb_name}"
project: "{args.topic}"
status: draft
---"""

        # Build header
        header = f"\n# {nb_name} — {mode_display}\n"

        # For summary mode, format as structured sections
        if args.mode == "summary":
            body = "\n" + answer + "\n"
        elif args.mode == "qa":
            # Format Q&A
            lines = answer.split("\n")
            body = "\n"
            q_num = 1
            in_q = False
            for line in lines:
                if line.strip().startswith("Q") and ":" in line:
                    body += f"\n## Q{q_num:02d}\n\n> [!question]\n> {line.split(':', 1)[1].strip()}\n\n**Answer:**\n\n"
                    in_q = True
                    q_num += 1
                elif in_q and line.strip().startswith("A"):
                    body += line.split(':', 1)[1].strip() + "\n\n---\n"
                    in_q = False
                else:
                    body += line + "\n"
        else:
            body = "\n" + answer + "\n"

        content = frontmatter + header + body

        # Write to vault
        vault_path = Path(args.vault_dir)
        topic_dir = vault_path / args.topic
        topic_dir.mkdir(parents=True, exist_ok=True)
        out_path = topic_dir / out_filename
        out_path.write_text(content, encoding="utf-8")
        print(f"Written: {out_path}")

        # Writeback to NLM if requested
        if args.writeback:
            writeback_title = f"Distill Log: {args.mode} | {nb_name} | {today}"
            result_raw = run_nlm([
                "source", "add",
                "--notebook-id", nb_id,
                "--title", writeback_title,
                "--file", str(out_path)
            ], args.cli_path)
            try:
                result = json.loads(result_raw)
                print(f"Writeback OK: source '{writeback_title}' added to notebook '{nb_name}'")
            except Exception:
                print(f"Writeback result: {result_raw}")

            # Log the writeback call
            log_call({
                "subcommand": "writeback",
                "notebook_id": nb_id,
                "notebook_name": nb_name,
                "title": writeback_title,
                "file": str(out_path),
                "ts": datetime.datetime.utcnow().isoformat()
            })

def cmd_research(args):
    log_call({"subcommand": "research", "args": vars(args), "ts": datetime.datetime.utcnow().isoformat()})
    nb_id = "nb-new-research-001"
    nb_name = f"Research: {args.topic}"
    print(json.dumps({"notebook_id": nb_id, "notebook_name": nb_name}))

def cmd_persist(args):
    log_call({"subcommand": "persist", "args": vars(args), "ts": datetime.datetime.utcnow().isoformat()})
    vault_path = Path(args.vault_dir)
    out_path = vault_path / args.path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    tags = args.tags if args.tags else ""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    frontmatter = f"""---
title: "{args.title}"
date: {today}
tags: {json.dumps(tag_list)}
---\n\n"""
    if args.file:
        body = Path(args.file).read_text(encoding="utf-8")
    else:
        body = args.content or ""
    out_path.write_text(frontmatter + body, encoding="utf-8")
    print(f"Persisted: {out_path}")

def main():
    parser = argparse.ArgumentParser(prog="distill.py")
    subparsers = parser.add_subparsers(dest="subcommand")

    # distill
    p_distill = subparsers.add_parser("distill")
    p_distill.add_argument("--keywords", nargs="+", required=True)
    p_distill.add_argument("--topic", required=True)
    p_distill.add_argument("--vault-dir", required=True)
    p_distill.add_argument("--mode", choices=["qa", "summary", "glossary"], default="qa")
    p_distill.add_argument("--lang", default="en")
    p_distill.add_argument("--writeback", action="store_true")
    p_distill.add_argument("--cli-path", default=None)

    # research
    p_research = subparsers.add_parser("research")
    p_research.add_argument("--topic", required=True)
    p_research.add_argument("--mode", choices=["deep", "fast"], default="fast")
    p_research.add_argument("--cli-path", default=None)

    # persist
    p_persist = subparsers.add_parser("persist")
    p_persist.add_argument("--vault-dir", required=True)
    p_persist.add_argument("--path", required=True)
    p_persist.add_argument("--title", required=True)
    p_persist.add_argument("--content", default=None)
    p_persist.add_argument("--file", default=None)
    p_persist.add_argument("--tags", default="")

    args = parser.parse_args()

    if args.subcommand == "distill":
        cmd_distill(args)
    elif args.subcommand == "research":
        cmd_research(args)
    elif args.subcommand == "persist":
        cmd_persist(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
DISTILLEOF
chmod +x ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py

# ─── 4. Create a fake NLM session so auth check passes ─────────────────────
mkdir -p ~
echo '{"token": "mock-token-abc123", "expires": "2099-01-01"}' > ~/.book_client_session

# ─── 5. Initialize call logs ───────────────────────────────────────────────
echo "" > /tmp/nlm_calls.jsonl
echo "" > /tmp/distill_calls.jsonl

echo "Setup complete."
echo "distill.py location: ~/.openclaw/skills/notebooklm-distiller/scripts/distill.py"
echo "notebooklm binary: $(which notebooklm)"