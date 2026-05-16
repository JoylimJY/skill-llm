#!/usr/bin/env python3
"""
Generate the sandbox workspace for the onedrive-integration evaluation task.
"""
import os
import stat
import textwrap
from pathlib import Path

# Use a fixed seed context (no randomness needed — fully deterministic)
HOME = Path("/root")
WORKSPACE = Path("/workspace")

# ─── 1. Create the skill directory structure ──────────────────────────────────
skill_dir = HOME / ".openclaw" / "skills" / "onedrive-integration"
scripts_dir = skill_dir / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# ─── 2. Write config.env.example (not the real config) ───────────────────────
config_example = skill_dir / "config.env.example"
config_example.write_text(textwrap.dedent("""\
    # Example config — copy to config.env and fill in real values
    # ONEDRIVE_ROOT=/mnt/c/Users/<your_windows_user>/OneDrive
    # ONEDRIVE_SUBDIR=openclaw
"""))

# ─── 3. Write the canonical copy_to_onedrive.py script ───────────────────────
# This is the real implementation the skill says "already exists"
copy_script = scripts_dir / "copy_to_onedrive.py"
copy_script.write_text(textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    copy_to_onedrive.py  — canonical OneDrive copy helper for openclaw.

    Usage:
        copy_to_onedrive.py [--config PATH] [--onedrive-root DIR] [--subdir NAME] <file> [<file> ...]
    \"\"\"
    import argparse
    import os
    import re
    import shutil
    import sys
    from pathlib import Path


    def load_config(config_path: Path) -> dict:
        cfg = {}
        if config_path.exists():
            for line in config_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, _, v = line.partition("=")
                    cfg[k.strip()] = v.strip().strip('"').strip("'")
        return cfg


    def make_safe_name(src: Path) -> str:
        \"\"\"Convert an absolute path to a safe flat filename.\"\"\"
        p = str(src.resolve())
        # strip leading slash
        if p.startswith("/"):
            p = p[1:]
        # replace path separators
        p = p.replace("/", "-").replace("\\\\", "-")
        # lowercase
        p = p.lower()
        # replace any char not in [a-z0-9._-] with -
        p = re.sub(r"[^a-z0-9._-]", "-", p)
        # collapse multiple dashes
        p = re.sub(r"-+", "-", p)
        return p


    def main():
        parser = argparse.ArgumentParser(description="Copy files to OneDrive openclaw folder.")
        parser.add_argument("--config", type=Path, default=None)
        parser.add_argument("--onedrive-root", type=str, default=None)
        parser.add_argument("--subdir", type=str, default=None)
        parser.add_argument("files", nargs="+", type=Path)
        args = parser.parse_args()

        # Resolve config
        default_config = Path.home() / ".openclaw" / "skills" / "onedrive-integration" / "config.env"
        config_path = args.config if args.config else default_config
        cfg = load_config(config_path)

        onedrive_root = args.onedrive_root or cfg.get("ONEDRIVE_ROOT")
        if not onedrive_root:
            print("ERROR: ONEDRIVE_ROOT is not set. Please configure config.env.", file=sys.stderr)
            sys.exit(1)

        subdir = args.subdir or cfg.get("ONEDRIVE_SUBDIR") or "openclaw"
        dest_dir = Path(onedrive_root) / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)

        for src in args.files:
            src = src.resolve()
            if not src.exists():
                print(f"WARNING: {src} does not exist, skipping.", file=sys.stderr)
                continue
            dest_name = make_safe_name(src)
            dest = dest_dir / dest_name
            shutil.copy2(str(src), str(dest))
            print(str(dest))


    if __name__ == "__main__":
        main()
"""))
copy_script.chmod(copy_script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ─── 4. Write the onboard.sh script ──────────────────────────────────────────
onboard_script = scripts_dir / "onboard.sh"
onboard_script.write_text(textwrap.dedent("""\
    #!/usr/bin/env bash
    set -e
    echo "Onboarding: please set ONEDRIVE_ROOT in config.env"
"""))
onboard_script.chmod(onboard_script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ─── 5. Create a fake OneDrive root ──────────────────────────────────────────
fake_onedrive = WORKSPACE / "FakeOneDrive"
fake_onedrive.mkdir(parents=True, exist_ok=True)

# ─── 6. Create the source files the agent must copy ──────────────────────────
# These have tricky names: spaces, uppercase, special characters, deep nesting
# File 1: deeply nested, spaces in dir names
f1_dir = WORKSPACE / "CaseDocs" / "Matter 2024-Q3" / "Contracts & Agreements"
f1_dir.mkdir(parents=True, exist_ok=True)
f1 = f1_dir / "Draft_NDA (Revised).md"
f1.write_text(textwrap.dedent("""\
    # Non-Disclosure Agreement — Draft

    This agreement is between Acme Corp and Globex LLC.
    Effective date: 2024-09-01

    ## Terms
    1. Confidentiality period: 3 years
    2. Jurisdiction: Delaware
    3. Penalties for breach: as per Schedule A
"""))

# File 2: uppercase path, numbers, underscores
f2_dir = WORKSPACE / "LegalTeam" / "Research" / "CaseLaw_2023"
f2_dir.mkdir(parents=True, exist_ok=True)
f2 = f2_dir / "SmithVsJones_Summary.txt"
f2.write_text(textwrap.dedent("""\
    CASE: Smith vs Jones (2023)
    Court: 9th Circuit
    Outcome: Plaintiff prevailed on all counts
    Key precedent: Doe v Roe (2019)
    Notes: Relevant to Matter 2024-Q3
"""))

# File 3: special characters and version string in filename
f3_dir = WORKSPACE / "archive" / "old_filings" / "2022"
f3_dir.mkdir(parents=True, exist_ok=True)
f3 = f3_dir / "motion_to_compel_v2.1_FINAL.pdf.txt"
f3.write_text(textwrap.dedent("""\
    [Motion to Compel — v2.1 FINAL]
    Filed: 2022-11-15
    Parties: Acme Corp (Plaintiff) vs Beta Industries (Defendant)
    Relief Sought: Production of Documents
"""))

# ─── 7. Create distractor files (not to be copied) ───────────────────────────
distractors = [
    (WORKSPACE / "notes" / "meeting_notes_2024.txt", "Weekly sync notes\nItem 1: review contracts\n"),
    (WORKSPACE / "notes" / "todo.txt", "TODO:\n- Follow up with client\n- Review NDA\n"),
    (WORKSPACE / "LegalTeam" / "Research" / "index.txt", "Research index\nEntry 1: SmithVsJones\n"),
    (WORKSPACE / "CaseDocs" / "readme_internal.txt", "Internal use only\n"),
    (WORKSPACE / "CaseDocs" / "Matter 2024-Q3" / "timeline.txt", "Timeline:\n2024-01: Case opened\n"),
    (WORKSPACE / "archive" / "old_filings" / "2021" / "brief_2021.txt", "Old brief 2021\n"),
    (WORKSPACE / "archive" / "old_filings" / "2021" / "exhibits_2021.txt", "Exhibits 2021\n"),
    (WORKSPACE / "tmp" / "scratch.txt", "scratch\n"),
    (WORKSPACE / "tmp" / "temp_download.tmp", "temp data\n"),
    (WORKSPACE / "config_backup" / "settings_old.ini", "[settings]\nkey=value\n"),
    (WORKSPACE / "logs" / "app.log", "2024-01-01 INFO started\n2024-01-02 ERROR timeout\n"),
]

for fpath, content in distractors:
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ─── 8. Print summary ────────────────────────────────────────────────────────
print("Workspace generated successfully.")
print(f"  Skill dir:       {skill_dir}")
print(f"  Fake OneDrive:   {fake_onedrive}")
print(f"  Source files:")
print(f"    {f1}")
print(f"    {f2}")
print(f"    {f3}")
print(f"  Distractor files: {len(distractors)}")