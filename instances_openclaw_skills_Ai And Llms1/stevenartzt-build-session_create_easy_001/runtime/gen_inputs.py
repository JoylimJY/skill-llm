from pathlib import Path

Path('HEARTBEAT.md').write_text(
    '# Heartbeat\n\nUrgent messages: none.\nLast session blocker: waiting on a build-session note.\nCurrent date/time marker: 2025-05-01 09:00 UTC.\n\nMarker token: BUILD_SESSION_MARKER_7A9F\n',
    encoding='utf-8'
)
