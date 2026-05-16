import os
import random
import textwrap

random.seed(42)

# --- Directory structure ---
base = "/workspace"

dirs = [
    "scripts",
    "ref/agent-surveys/pdfs",
    "ref/agent-surveys/text",
    "docs/notes",
    "docs/planning",
    "data/raw",
    "data/processed",
    "configs",
    "logs",
    "outputs/drafts",
    "outputs/final",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "docs/notes/meeting_notes_2024.txt": "Q3 planning: finalize the survey pipeline by end of month.\nAction items: assign PDF downloader task to engineer.\n",
    "docs/planning/roadmap.md": "# Roadmap\n\n- [ ] Build style corpus\n- [ ] Run analysis\n- [ ] Write draft\n",
    "data/raw/placeholder.csv": "id,title,year\n001,Survey of LLMs,2023\n002,Agent Benchmarks,2024\n",
    "data/processed/nothing_yet.txt": "Processed outputs will go here.\n",
    "configs/pipeline.yaml": "pipeline:\n  stage: extraction\n  max_workers: 4\n  timeout: 30\n",
    "logs/run_20240101.log": "[INFO] Starting pipeline run\n[INFO] No inputs found\n[WARN] Exiting early\n",
    "outputs/drafts/outline_v1.txt": "Introduction\nRelated Work\nMethodology\nExperiments\nConclusion\n",
    "outputs/final/.gitkeep": "",
    "tmp/scratch.py": "# temporary scratch file\nprint('hello')\n",
    "docs/notes/style_notes.txt": "Look at how top survey papers write their related work sections.\nFocus on transition sentences and claim density.\n",
    ".gitignore": "ref/**/pdfs/\nref/**/text/\n*.pyc\n__pycache__/\n",
    "configs/arxiv_config_OLD.txt": "# DEPRECATED - do not use\n2302.11382\n2210.03629\n",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(base, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- The core run.py script (the skill's proprietary script) ---
run_py = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    Agent Survey Corpus downloader and text extractor.
    Reads arXiv IDs from an input file, downloads PDFs from arXiv,
    extracts the first N pages as text, and writes a STYLE_REPORT.md.
    \"\"\"
    import argparse
    import os
    import time
    import sys
    import re
    from pathlib import Path

    def parse_args():
        p = argparse.ArgumentParser(description="Download arXiv survey PDFs and extract text.")
        p.add_argument("--workspace", default=".", help="Root workspace directory")
        p.add_argument("--inputs", default="ref/agent-surveys/arxiv_ids.txt",
                       help="Semicolon-separated list of input files with arXiv IDs")
        p.add_argument("--max-pages", type=int, default=20, help="Max pages to extract per PDF")
        p.add_argument("--sleep", type=float, default=1.0, help="Seconds to sleep between downloads")
        p.add_argument("--overwrite", action="store_true", help="Re-download and re-extract existing files")
        return p.parse_args()

    def load_ids(inputs_str, workspace):
        ids = []
        for inp in inputs_str.split(";"):
            inp = inp.strip()
            candidate = Path(workspace) / inp if not Path(inp).is_absolute() else Path(inp)
            if candidate.exists():
                for line in candidate.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ids.append(line)
        return ids

    def download_pdf(arxiv_id, pdf_path, sleep_sec):
        import urllib.request
        url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        try:
            urllib.request.urlretrieve(url, str(pdf_path))
            time.sleep(sleep_sec)
            return True
        except Exception as e:
            print(f"[WARN] Failed to download {arxiv_id}: {e}", file=sys.stderr)
            return False

    def extract_text(pdf_path, max_pages):
        \"\"\"Extract text from first max_pages of a PDF using pymupdf (fitz) if available, else pdfminer.\"\"\"
        try:
            import fitz  # pymupdf
            doc = fitz.open(str(pdf_path))
            pages = min(max_pages, len(doc))
            texts = []
            for i in range(pages):
                texts.append(doc[i].get_text())
            return "\\n".join(texts)
        except ImportError:
            pass
        try:
            from pdfminer.high_level import extract_text as pm_extract
            return pm_extract(str(pdf_path), maxpages=max_pages)
        except Exception as e:
            return f"[ERROR extracting text: {e}]"

    def count_sections(text):
        h2 = len(re.findall(r'^#{1,2}\\s+\\S', text, re.MULTILINE))
        # Also count lines that look like numbered sections
        numbered = len(re.findall(r'^\\d+\\.\\s+[A-Z]', text, re.MULTILINE))
        # Count ALL-CAPS headings as a heuristic for PDFs
        caps = len(re.findall(r'^[A-Z][A-Z ]{4,}$', text, re.MULTILINE))
        return {"markdown_h2": h2, "numbered": numbered, "caps_headings": caps}

    def build_style_report(workspace, results):
        report_path = Path(workspace) / "ref/agent-surveys/STYLE_REPORT.md"
        lines = [
            "# Style Report\\n",
            f"Generated for {len(results)} paper(s).\\n",
            "| arXiv ID | Pages Extracted | Chars | Numbered Sections | Caps Headings |",
            "|---|---|---|---|---|",
        ]
        for r in results:
            lines.append(
                f"| {r['id']} | {r['pages']} | {r['chars']} | {r['sections']['numbered']} | {r['sections']['caps_headings']} |"
            )
        lines.append("\\n## Notes\\n")
        lines.append("- Review the text/ directory for raw extracted content.\\n")
        lines.append("- Focus on section transitions and rhetorical patterns.\\n")
        report_path.write_text("\\n".join(lines))
        print(f"[INFO] Style report written to {report_path}")

    def main():
        args = parse_args()
        ws = Path(args.workspace).resolve()
        pdf_dir = ws / "ref/agent-surveys/pdfs"
        text_dir = ws / "ref/agent-surveys/text"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        text_dir.mkdir(parents=True, exist_ok=True)

        ids = load_ids(args.inputs, ws)
        if not ids:
            print("[ERROR] No arXiv IDs found. Check your inputs file.", file=sys.stderr)
            sys.exit(1)

        print(f"[INFO] Processing {len(ids)} arXiv IDs with max-pages={args.max_pages}")
        results = []
        for arxiv_id in ids:
            pdf_path = pdf_dir / f"{arxiv_id.replace('/', '_')}.pdf"
            text_path = text_dir / f"{arxiv_id.replace('/', '_')}.txt"

            if pdf_path.exists() and not args.overwrite:
                print(f"[INFO] Skipping download (exists): {arxiv_id}")
            else:
                print(f"[INFO] Downloading: {arxiv_id}")
                ok = download_pdf(arxiv_id, pdf_path, args.sleep)
                if not ok:
                    continue

            if text_path.exists() and not args.overwrite:
                print(f"[INFO] Skipping extraction (exists): {arxiv_id}")
                text = text_path.read_text()
            else:
                print(f"[INFO] Extracting text: {arxiv_id}")
                text = extract_text(pdf_path, args.max_pages)
                text_path.write_text(text)

            secs = count_sections(text)
            results.append({
                "id": arxiv_id,
                "pages": args.max_pages,
                "chars": len(text),
                "sections": secs,
            })

        if results:
            build_style_report(ws, results)
        else:
            print("[WARN] No papers processed successfully.", file=sys.stderr)

    if __name__ == "__main__":
        main()
""")

with open(os.path.join(base, "scripts", "run.py"), "w") as f:
    f.write(run_py)

# --- INTENTIONALLY WRONG / MISSING arxiv_ids.txt ---
# The file does NOT exist yet at the correct path.
# There IS a decoy in the wrong location to trap the agent.
with open(os.path.join(base, "configs", "arxiv_ids_backup.txt"), "w") as f:
    f.write("# OLD backup — do not use directly\n2302.11382\n2210.03629\n")

# The ref/agent-surveys/ directory exists, but the arxiv_ids.txt is missing (agent must create it)
# Also, there is a partial/corrupted file at the ref level to confuse
with open(os.path.join(base, "ref", "draft_ids.txt"), "w") as f:
    f.write("# draft - incomplete\n# 2303.18223\n")

print("Workspace initialized successfully.")
print("Key structure:")
print("  /workspace/scripts/run.py        <- the proprietary script")
print("  /workspace/ref/agent-surveys/    <- target output area (no arxiv_ids.txt yet)")
print("  /workspace/configs/arxiv_ids_backup.txt <- decoy file")