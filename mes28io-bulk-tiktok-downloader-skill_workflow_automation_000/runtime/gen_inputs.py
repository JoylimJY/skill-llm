import os
import random
import json

random.seed(42)

workspace = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "skills/bulk-tiktok-downloader/scripts",
    "skills/bulk-tiktok-downloader/references",
    "assets/brand/2024/q3",
    "assets/brand/2024/q4",
    "assets/raw_exports",
    "campaign/offline_review/briefs",
    "campaign/offline_review/assets",
    "reports/engagement",
    "reports/reach",
    "archive/old_campaigns",
    "tmp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── requirements.txt ─────────────────────────────────────────────────────────
req_path = os.path.join(workspace, "skills/bulk-tiktok-downloader/scripts/requirements.txt")
with open(req_path, "w") as f:
    f.write("yt-dlp>=2024.1.1\n")

# ── mock downloader.py ───────────────────────────────────────────────────────
# This is the pre-existing script the skill references.
# It simulates downloading: creates stub files and prints counts.
downloader_src = r'''#!/usr/bin/env python3
"""
Bulk TikTok downloader (mock implementation for sandbox).
Usage:
  python3 downloader.py                        # uses urls.txt + downloads/
  python3 downloader.py <url_file>             # custom url file
  python3 downloader.py <url_file> <out_dir>   # custom url file + output dir
"""
import sys, os, json, re, pathlib, time

SCRIPT_DIR = pathlib.Path(__file__).parent

def parse_args():
    args = sys.argv[1:]
    url_file = args[0] if len(args) >= 1 else str(SCRIPT_DIR.parent / "urls.txt")
    out_dir  = args[1] if len(args) >= 2 else str(SCRIPT_DIR.parent / "downloads")
    return url_file, out_dir

TIKTOK_PAT = re.compile(r'https?://(www\.)?(tiktok\.com|vm\.tiktok\.com)/\S+')

SIMULATED_FAILURES = {
    "https://www.tiktok.com/@brandX/video/0000000000000001": "private",
    "https://www.tiktok.com/@brandX/video/0000000000000002": "deleted",
}

def main():
    url_file, out_dir = parse_args()

    # Validate
    if not os.path.exists(url_file):
        print(f"[ERROR] URL file not found: {url_file}", flush=True)
        sys.exit(1)

    with open(url_file) as f:
        raw_lines = f.readlines()

    urls = []
    for line in raw_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if TIKTOK_PAT.match(stripped):
            urls.append(stripped)
        else:
            print(f"[WARN] Skipping non-TikTok line: {stripped!r}", flush=True)

    if not urls:
        print("[ERROR] No valid URLs found in file.", flush=True)
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    success, failed = [], []
    log_entries = []

    for url in urls:
        if url in SIMULATED_FAILURES:
            reason = SIMULATED_FAILURES[url]
            print(f"[FAIL]  {url}  ({reason})", flush=True)
            failed.append({"url": url, "reason": reason})
        else:
            # Simulate a downloaded file
            vid_id = url.rstrip("/").split("/")[-1]
            fname = os.path.join(out_dir, f"{vid_id}.mp4")
            with open(fname, "wb") as fh:
                fh.write(b"\x00" * 128)   # stub mp4
            print(f"[OK]    {url}  -> {fname}", flush=True)
            success.append(url)
        time.sleep(0.01)

    print(f"\n=== Summary ===", flush=True)
    print(f"Successful : {len(success)}", flush=True)
    print(f"Failed     : {len(failed)}", flush=True)
    if failed:
        print("Failed URLs:", flush=True)
        for entry in failed:
            print(f"  {entry['url']}  [{entry['reason']}]", flush=True)

    log = {
        "url_file": os.path.abspath(url_file),
        "out_dir":  os.path.abspath(out_dir),
        "argv":     sys.argv[1:],
        "success_count": len(success),
        "failed_count":  len(failed),
        "failed": failed,
    }
    log_path = os.path.join(out_dir, "_download_log.json")
    with open(log_path, "w") as lf:
        json.dump(log, lf, indent=2)

    print(f"\nLog saved to: {log_path}", flush=True)

if __name__ == "__main__":
    main()
'''
dl_path = os.path.join(workspace, "skills/bulk-tiktok-downloader/scripts/downloader.py")
with open(dl_path, "w") as f:
    f.write(downloader_src)
os.chmod(dl_path, 0o755)

# ── upstream readme (distractor) ─────────────────────────────────────────────
upstream_ref = os.path.join(workspace, "skills/bulk-tiktok-downloader/references/upstream-readme.md")
with open(upstream_ref, "w") as f:
    f.write("# yt-dlp upstream readme\nSee https://github.com/yt-dlp/yt-dlp for full docs.\n")

# ── THE MESSY RAW INPUT FILE agents must work from ───────────────────────────
# This is a realistic "exports from marketing spreadsheet" dump. It has:
#  - valid TikTok URLs (the ones to download)
#  - annotation/note lines (NOT prefixed with #, agent must decide what to do)
#  - blank lines
#  - two known-bad URLs (private/deleted) mixed in
#  - one clearly non-TikTok URL (YouTube) that should be excluded
#  - duplicate
raw_export = """\
# Exported from Notion campaign tracker - Q4 Brand Review
# Generated: 2024-11-15

BATCH 1 - Hero videos for offline screening
https://www.tiktok.com/@brandX/video/7311111111111111111
https://www.tiktok.com/@brandX/video/7311111111111111112
https://www.tiktok.com/@brandX/video/7311111111111111113

NOTE: video below was flagged as private - may fail
https://www.tiktok.com/@brandX/video/0000000000000001

BATCH 2 - UGC reposts
https://www.tiktok.com/@ugcuser1/video/7322222222222222221
https://www.tiktok.com/@ugcuser2/video/7322222222222222222
https://www.tiktok.com/@ugcuser3/video/7322222222222222223

DO NOT INCLUDE - wrong platform
https://www.youtube.com/watch?v=dQw4w9WgXcQ

BATCH 3 - Influencer collab
https://vm.tiktok.com/ZMhShortLink1/
https://vm.tiktok.com/ZMhShortLink2/
https://www.tiktok.com/@brandX/video/7333333333333333331

duplicate below (intentional test):
https://www.tiktok.com/@brandX/video/7311111111111111111

deleted video:
https://www.tiktok.com/@brandX/video/0000000000000002
"""
raw_path = os.path.join(workspace, "campaign/offline_review/raw_tiktok_export.txt")
with open(raw_path, "w") as f:
    f.write(raw_export)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "assets/brand/2024/q3/brand_guide.pdf.stub": b"PDF stub - brand colours",
    "assets/brand/2024/q4/campaign_brief.docx.stub": b"DOCX stub - Q4 brief",
    "assets/raw_exports/instagram_links.txt": (
        "https://www.instagram.com/p/ABC123/\nhttps://www.instagram.com/p/DEF456/\n"
    ).encode(),
    "assets/raw_exports/youtube_links.txt": (
        "https://youtu.be/aaa\nhttps://youtu.be/bbb\n"
    ).encode(),
    "reports/engagement/tiktok_metrics_q3.csv": (
        "video_id,views,likes\n7300001,100000,5000\n7300002,80000,4200\n"
    ).encode(),
    "reports/reach/reach_summary.json": json.dumps({"q3": 1200000, "q4_projected": 1800000}).encode(),
    "archive/old_campaigns/2023_links.txt": (
        "https://www.tiktok.com/@old/video/111\nhttps://www.tiktok.com/@old/video/222\n"
    ).encode(),
    "campaign/offline_review/briefs/offline_event_plan.md": (
        "# Offline Review Event\nDate: 2024-12-01\nVenue: HQ Screening Room\n"
        "We need all campaign TikToks downloaded for the screening.\n"
    ).encode(),
    "tmp/scratch/notes.txt": b"Random scratch notes from intern\nDo not use this file\n",
    "campaign/offline_review/assets/.gitkeep": b"",
}
for rel, content in distractors.items():
    fp = os.path.join(workspace, rel)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "wb") as fh:
        fh.write(content)

print("Workspace generated successfully.")
print(f"Raw export file: {raw_path}")