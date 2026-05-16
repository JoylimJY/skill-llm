import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Skill directory (mimics the real skill layout) ──────────────────────────
skill_dir = workspace / "skills" / "dotline-art"
scripts_dir = skill_dir / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# Write the real dotline_art.py script (this IS the skill script)
dotline_script = scripts_dir / "dotline_art.py"
dotline_script.write_text(r'''#!/usr/bin/env python3
"""
Dot-line ASCII art generator.
Converts text (with Chinese->pinyin auto-conversion) into dot-line style art.
"""
import sys
import re

try:
    from pypinyin import lazy_pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False

# Dot-line font definition: each character is 7 rows of 7 cols
FONT = {
    'A': [
        "  .-.  ",
        " /   \ ",
        "|     |",
        "|-ooo-|",
        "|     |",
        "|     |",
        "'     '",
    ],
    'B': [
        ".---. ",
        "|    \\",
        "|    /",
        "|---' ",
        "|    \\",
        "|    /",
        "'---' ",
    ],
    'C': [
        " .---.",
        "/     ",
        "|     ",
        "|     ",
        "|     ",
        "\\     ",
        " '---'",
    ],
    'D': [
        ".---. ",
        "|    \\",
        "|     |",
        "|     |",
        "|     |",
        "|    /",
        "'---' ",
    ],
    'E': [
        ".----.",
        "|     ",
        "|---- ",
        "|---- ",
        "|     ",
        "|     ",
        "'----'",
    ],
    'F': [
        ".----.",
        "|     ",
        "|---- ",
        "|---- ",
        "|     ",
        "|     ",
        "'     ",
    ],
    'G': [
        " .---.",
        "/     ",
        "|     ",
        "| .--.",
        "|    |",
        "\\    |",
        " '---'",
    ],
    'H': [
        ".   .",
        "|   |",
        "|   |",
        "|-.-|",
        "|   |",
        "|   |",
        "'   '",
    ],
    'I': [
        ".----.",
        "  ||  ",
        "  ||  ",
        "  ||  ",
        "  ||  ",
        "  ||  ",
        "'----'",
    ],
    'J': [
        " .---.",
        "     |",
        "     |",
        "     |",
        ".    |",
        "\\    |",
        " '---'",
    ],
    'K': [
        ".   .",
        "|  / ",
        "| /  ",
        "|<   ",
        "| \\  ",
        "|  \\ ",
        "'   '",
    ],
    'L': [
        ".    ",
        "|    ",
        "|    ",
        "|    ",
        "|    ",
        "|    ",
        "'----'",
    ],
    'M': [
        ".     .",
        "|\\ /|",
        "| v |",
        "|   |",
        "|   |",
        "|   |",
        "'   '",
    ],
    'N': [
        ".   .",
        "|\\  |",
        "| \\ |",
        "|  \\|",
        "|   |",
        "|   |",
        "'   '",
    ],
    'O': [
        " .---.",
        "/     \\",
        "|     |",
        "|     |",
        "|     |",
        "\\     /",
        " '---'",
    ],
    'P': [
        ".----.",
        "|    /",
        "|---' ",
        "|     ",
        "|     ",
        "|     ",
        "'     ",
    ],
    'Q': [
        " .---.",
        "/     \\",
        "|     |",
        "|  .  |",
        "| / \\ |",
        "\\/   \\|",
        " '---'",
    ],
    'R': [
        ".----.",
        "|    /",
        "|---' ",
        "|  \\ ",
        "|   \\",
        "|    \\",
        "'     ",
    ],
    'S': [
        " .---.",
        "/     ",
        "\\     ",
        " '---'",
        "     |",
        "     /",
        "'---' ",
    ],
    'T': [
        ".----.",
        "  ||  ",
        "  ||  ",
        "  ||  ",
        "  ||  ",
        "  ||  ",
        "  ''  ",
    ],
    'U': [
        ".   .",
        "|   |",
        "|   |",
        "|   |",
        "|   |",
        "\\   /",
        " '.' ",
    ],
    'V': [
        ".   .",
        "|   |",
        "|   |",
        " \\ / ",
        "  V  ",
        "     ",
        "     ",
    ],
    'W': [
        ".     .",
        "|     |",
        "|     |",
        "|  .  |",
        "| / \\ |",
        "|/   \\|",
        "'     '",
    ],
    'X': [
        ".   .",
        " \\ / ",
        "  X  ",
        " / \\ ",
        ".   .",
        "|   |",
        "'   '",
    ],
    'Y': [
        ".   .",
        "|   |",
        " \\ / ",
        "  |  ",
        "  |  ",
        "  |  ",
        "  '  ",
    ],
    'Z': [
        ".----.",
        "    / ",
        "   /  ",
        "  /   ",
        " /    ",
        "/     ",
        "'----'",
    ],
    ' ': [
        "   ",
        "   ",
        "   ",
        "   ",
        "   ",
        "   ",
        "   ",
    ],
}

def chinese_to_pinyin(text):
    """Convert Chinese characters to uppercase pinyin."""
    if not HAS_PYPINYIN:
        return text.upper()
    result = []
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            pinyin = lazy_pinyin(char, style=Style.NORMAL)
            result.append(pinyin[0].upper() if pinyin else char.upper())
        else:
            result.append(char.upper())
    return ''.join(result)

def clean_text(text):
    """Remove numbers and special symbols, keep only letters and spaces."""
    cleaned = re.sub(r'[^A-Za-z\s]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned.upper()

def generate_dotline_art(text):
    """Generate dot-line art for the given text."""
    # Step 1: Convert Chinese to pinyin
    text = chinese_to_pinyin(text)
    # Step 2: Clean - remove digits/specials
    text = clean_text(text)

    if not text:
        return "(no renderable characters)"

    # Build rows
    rows = [''] * 7
    for i, char in enumerate(text):
        glyph = FONT.get(char, FONT.get(' ', ['       '] * 7))
        for row_idx in range(7):
            rows[row_idx] += glyph[row_idx]
            if i < len(text) - 1:
                rows[row_idx] += ' '

    return '\n'.join(rows)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 dotline_art.py '<text>'")
        sys.exit(1)
    input_text = ' '.join(sys.argv[1:])
    art = generate_dotline_art(input_text)
    print(art)
''')
dotline_script.chmod(0o755)

# ── Skill metadata ────────────────────────────────────────────────────────────
(skill_dir / "SKILL.md").write_text("# dotline-art skill\nSee scripts/dotline_art.py\n")

# ── Distractor project structure ─────────────────────────────────────────────
project = workspace / "devops-cli-tool"
(project / "src" / "commands").mkdir(parents=True, exist_ok=True)
(project / "src" / "utils").mkdir(parents=True, exist_ok=True)
(project / "tests").mkdir(parents=True, exist_ok=True)
(project / "config").mkdir(parents=True, exist_ok=True)
(project / "docs").mkdir(parents=True, exist_ok=True)
(project / "banners").mkdir(parents=True, exist_ok=True)  # target output dir exists but is empty

(project / "src" / "commands" / "deploy.py").write_text("# deploy command\ndef deploy(): pass\n")
(project / "src" / "commands" / "rollback.py").write_text("# rollback command\ndef rollback(): pass\n")
(project / "src" / "commands" / "status.py").write_text("# status command\ndef status(): pass\n")
(project / "src" / "utils" / "logger.py").write_text("import logging\ndef get_logger(name): return logging.getLogger(name)\n")
(project / "src" / "utils" / "config_loader.py").write_text("import json\ndef load(path): return json.load(open(path))\n")
(project / "tests" / "test_deploy.py").write_text("def test_deploy(): assert True\n")
(project / "tests" / "test_rollback.py").write_text("def test_rollback(): assert True\n")
(project / "config" / "staging.json").write_text(json.dumps({"env": "staging", "replicas": 2}))
(project / "config" / "production.json").write_text(json.dumps({"env": "production", "replicas": 5}))
(project / "docs" / "architecture.md").write_text("# Architecture\nMicroservices on Kubernetes.\n")
(project / "docs" / "onboarding.md").write_text(
    "# Onboarding\nWelcome to DevOps CLI Tool!\n\n"
    "The tool greets new engineers with a startup banner.\n"
    "Banners should be stored in the `banners/` directory.\n"
    "We need a banner for the project name (Chinese: 你好世界) and one for DEVOPS.\n"
)

# Fake/wrong banner placeholder that agent must NOT keep
(project / "banners" / "placeholder.txt").write_text(
    "TODO: replace with real dot-line art banners\n"
)

# More distractors
(project / "src" / "__init__.py").write_text("")
(workspace / "notes.txt").write_text(
    "Reminder: we use a custom in-house dot-line art generator, not figlet or toilet.\n"
    "The skill is located under skills/dotline-art/\n"
)

print("Workspace generated successfully.")
print(f"Skill script: {dotline_script}")
print(f"Project banners dir: {project / 'banners'}")