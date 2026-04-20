from pathlib import Path

# Deterministic input generation with marker content
Path("HEARTBEAT.md").write_text(
    "# Heartbeat\n\n"
    "Urgent messages: none\n"
    "Blockers from last session: none\n"
    "Current date/time marker: 2025-05-01T09:00:00Z\n"
    "Session marker: BUILD_SESSION_MARKER_7F3A\n",
    encoding="utf-8",
)
