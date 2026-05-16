import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deep distractor directory structure ---

dirs = [
    "internal/marketing/assets",
    "internal/marketing/campaigns/q3",
    "internal/engineering/specs",
    "internal/engineering/legacy_docs",
    "internal/hr/onboarding",
    "internal/hr/policies",
    "community/forums/archive",
    "community/forums/active",
    "releases/v0.1.0",
    "releases/v0.1.1",
    "platform_notes/windows",
    "platform_notes/mac",
    "platform_notes/linux",
    "drafts/player_guides",
    "drafts/press_releases",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files with intentionally misleading content ---

distractor_files = {
    "internal/marketing/assets/banner.txt": "GameClaw Banner Art v2 — do not distribute",
    "internal/marketing/campaigns/q3/q3_targets.txt": "Target: 500 downloads by end of Q3\nFocus: Linux and Windows users",
    "internal/engineering/specs/arch_overview.txt": "GameClaw monorepo layout:\n  games/\n    lobster-cli-roguelike/\n  tools/",
    "internal/engineering/legacy_docs/old_install.txt": (
        "DEPRECATED: git clone https://github.com/Arcobalneo/gameclaw\n"
        "cd gameclaw/games/lobster-cli-roguelike\n"
        "cargo build --release\n"
        "Run: ./target/release/lobster-cli-roguelike\n"
        "NOTE: This method is no longer recommended."
    ),
    "internal/hr/onboarding/welcome.txt": "Welcome to the GameClaw team! Please review all platform support docs before publishing.",
    "internal/hr/policies/oss_policy.txt": "All binaries must be released under the project license. Source remains on GitHub.",
    "community/forums/archive/thread_001.txt": (
        "User: Does GameClaw support Windows?\n"
        "Mod: Not currently. Only Linux x86_64 and macOS Apple Silicon.\n"
        "User: What about macOS Intel?\n"
        "Mod: Not yet supported.\n"
    ),
    "community/forums/archive/thread_002.txt": (
        "User: Can I decompile the binary?\n"
        "Mod: The binary is compiled — it reduces casual source visibility but is not impossible to reverse engineer.\n"
    ),
    "community/forums/active/thread_099.txt": "User: Where do I download the game?\nMod: Check the GitHub releases page.",
    "releases/v0.1.0/changelog.txt": "v0.1.0 — Initial release. Linux x86_64 only.",
    "releases/v0.1.1/changelog.txt": "v0.1.1 — Added darwin-arm64 support.",
    "platform_notes/windows/status.txt": "Windows: NOT SUPPORTED. Do not publish Windows download links.",
    "platform_notes/mac/status.txt": "macOS Apple Silicon (darwin-arm64): SUPPORTED\nmacOS Intel (darwin-x86_64): NOT SUPPORTED",
    "platform_notes/linux/status.txt": "Linux x86_64 (linux-x86_64): SUPPORTED\nLinux ARM: NOT SUPPORTED",
    "drafts/player_guides/PLACEHOLDER.txt": (
        "TODO: Write the official player guide here.\n"
        "Must cover: available games, platforms, download, unpack, run.\n"
        "Must NOT mislead users about platform support.\n"
        "Must NOT say binaries are impossible to reverse engineer.\n"
    ),
    "drafts/press_releases/announcement.txt": (
        "FOR IMMEDIATE RELEASE:\n"
        "GameClaw launches lobster-cli-roguelike — a terminal roguelike game from the lobster's perspective.\n"
        "Available now on Linux and macOS Apple Silicon.\n"
    ),
}

for rel_path, content in distractor_files.items():
    full_path = workspace / rel_path
    full_path.write_text(content, encoding="utf-8")

print("Workspace generated successfully.")
print("Files created:")
for rel_path in distractor_files:
    print(f"  /workspace/{rel_path}")