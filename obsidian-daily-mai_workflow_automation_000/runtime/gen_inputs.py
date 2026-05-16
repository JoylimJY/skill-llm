import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Build realistic PARA vault structure with distractor files ---
dirs = [
    "vault/00.DAILY",
    "vault/01.PROJECT/game-engine-renderer",
    "vault/01.PROJECT/multiplayer-lobby",
    "vault/02.AREA/engine-research",
    "vault/02.AREA/monetization",
    "vault/03.RESOURCES/godot-docs",
    "vault/03.RESOURCES/shaders",
    "vault/04.ARCHIVE/2025-sprints",
    "vault/04.ARCHIVE/old-designs",
    "docs/A_analysis",
    "docs/D_design",
    "docs/I_implementation",
    "docs/T_test",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files in vault ---
distractor_files = {
    "vault/00.DAILY/2025-11-10_shader-debug-session.md": (
        "# 2025-11-10 (Monday) — Daily Note\n\n"
        "## Completed Today\n\n"
        "### 🔧 Dev\n"
        "- **Fixed shader compilation** → Resolved GLSL version mismatch\n\n"
        "## Tomorrow's Actions\n\n"
        "- [ ] Profile render pipeline\n"
    ),
    "vault/00.DAILY/2025-12-03_multiplayer-sync.md": (
        "# 2025-12-03 (Wednesday) — Daily Note\n\n"
        "## Completed Today\n\n"
        "### 🔗 Integration\n"
        "- **WebSocket handshake** → Reduced latency by 40ms\n\n"
        "## Tomorrow's Actions\n\n"
        "- [ ] Test with 8-player lobby\n"
    ),
    "vault/01.PROJECT/game-engine-renderer/kanban.md": (
        "# Renderer Kanban\n\n"
        "## Backlog\n- Shadow mapping\n- SSAO pass\n\n"
        "## In Progress\n- Deferred rendering\n\n"
        "## Done\n- Basic forward renderer\n"
    ),
    "vault/01.PROJECT/multiplayer-lobby/dashboard.md": (
        "# Multiplayer Lobby Dashboard\n\nStatus: Alpha\n\nMilestones:\n- [x] Basic connection\n- [ ] Matchmaking\n"
    ),
    "vault/02.AREA/engine-research/vulkan-notes.md": (
        "# Vulkan Research\n\nVulkan requires explicit synchronization. Key primitives: semaphores, fences, barriers.\n"
    ),
    "vault/02.AREA/monetization/pricing-ideas.md": (
        "# Monetization Ideas\n\n- One-time purchase $14.99\n- DLC expansions\n- OST bundle\n"
    ),
    "vault/03.RESOURCES/godot-docs/gdscript-cheatsheet.md": (
        "# GDScript Cheatsheet\n\n```gdscript\nfunc _ready():\n    print('Hello')\n```\n"
    ),
    "vault/03.RESOURCES/shaders/pbr-reference.md": (
        "# PBR Shader Reference\n\nAlbedo, Normal, Roughness, Metallic, AO channels.\n"
    ),
    "vault/04.ARCHIVE/2025-sprints/sprint-08-retro.md": (
        "# Sprint 08 Retrospective\n\nVelocity: 34pts\nBlockers: Asset pipeline delays\n"
    ),
    "vault/04.ARCHIVE/old-designs/legacy-ecs-design.md": (
        "# Legacy ECS Design (Archived)\n\nComponent-entity approach, superseded by new architecture.\n"
    ),
    "docs/A_analysis/performance-analysis.md": (
        "# Performance Analysis\n\nFrame time budget: 16ms\nCurrent bottleneck: CPU-GPU sync\n"
    ),
    "docs/D_design/renderer-design.md": (
        "# Renderer Design\n\nDeferred rendering pipeline with G-buffer.\n"
    ),
    "docs/I_implementation/deferred-renderer-impl.md": (
        "# Deferred Renderer Implementation Notes\n\nG-buffer layout: position, normal, albedo, specular.\n"
    ),
    "docs/T_test/render-benchmarks.md": (
        "# Render Benchmarks\n\nScene A: 120fps avg\nScene B: 87fps avg (heavy particles)\n"
    ),
}

for rel_path, content in distractor_files.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# --- THE PROBLEM: Raw, unstructured session log the agent must process ---
session_log_content = """DATE: 2026-03-12

WORK SESSION LOG
================

Today I spent time on several things across the game project.

DEV WORK:
- Investigated why the deferred renderer was dropping frames on scenes with more than 50 dynamic lights. Traced it to the G-buffer's lighting accumulation pass not being batched. Fixed by implementing tile-based light culling. Frame times dropped from ~28ms to ~14ms on the stress test scene.
- Refactored the shadow map atlas allocator — it was leaking descriptor sets on Vulkan. Plug the leak and confirmed with RenderDoc capture, zero leaks now.
- Updated the CMake build system to separate the renderer module into its own static lib target. Took longer than expected due to circular includes, but resolved.

MOBILE PORT:
- Started investigating OpenGL ES 3.0 compatibility for the Android build. The tile-based GPU on test device doesn't support compute shaders the same way, so the culling pass needs a fallback path.
- Got the basic forward renderer running on the device at ~45fps (target is 60fps).

DOCUMENTATION:
- Updated the renderer architecture doc to reflect the new deferred pipeline changes.

STILL PENDING / TOMORROW:
- Need to implement the fallback culling path for mobile GPUs.
- Profile the Android build further to find the remaining performance gap.
- Write unit tests for the shadow atlas allocator refactor.
"""

session_log_path = workspace / "session_log_2026-03-12.txt"
session_log_path.write_text(session_log_content, encoding="utf-8")

print("Workspace generated successfully.")
print("\nDirectory structure:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")