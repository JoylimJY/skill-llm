import os
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic, deeply nested directory structure with distractor files
dirs = [
    "docs/release",
    "docs/internal",
    "docs/api",
    "src/core",
    "src/utils",
    "src/i18n/zh",
    "src/i18n/ja",
    "src/i18n/en",
    "tests/unit",
    "tests/integration",
    "config/prod",
    "config/dev",
    "scripts/deploy",
    "scripts/build",
    "assets/images",
    "assets/fonts",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "src/core/engine.py": "# Core translation engine module\nclass Engine:\n    pass\n",
    "src/utils/formatter.py": "# Formatter utility\ndef format_output(text):\n    return text.strip()\n",
    "config/prod/settings.json": '{"env": "production", "debug": false, "version": "2.1.0"}\n',
    "config/dev/settings.json": '{"env": "development", "debug": true, "version": "2.1.0-dev"}\n',
    "tests/unit/test_engine.py": "# Unit tests\ndef test_placeholder():\n    assert True\n",
    "tests/integration/test_pipeline.py": "# Integration tests\ndef test_integration():\n    pass\n",
    "scripts/deploy/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "scripts/build/build.sh": "#!/bin/bash\necho 'Building...'\n",
    "docs/api/endpoints.md": "# API Endpoints\n## GET /translate\nReturns translated text.\n",
    "docs/internal/architecture.md": "# Architecture\nMicroservices based design.\n",
    "src/i18n/en/strings.json": '{"greeting": "Hello", "farewell": "Goodbye"}\n',
    "src/i18n/zh/strings.json": '{"greeting": "你好", "farewell": "再见"}\n',
    "src/i18n/ja/strings.json": '{"greeting": "こんにちは", "farewell": "さようなら"}\n',
    "assets/fonts/README.txt": "Font assets directory.\n",
    "docs/release/changelog.md": "# Changelog\n## v2.1.0\n- Added multi-language support\n## v2.0.0\n- Initial release\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN PROBLEM FILE: English technical release notes (30 lines)
# Lines 3-8 should be translated to Chinese
# Lines 15-22 should be translated to Japanese
release_notes_content = """\
=====================================
Product Release Notes - Version 3.0.0
This release introduces major performance improvements to the core engine.
Database connection pooling has been optimized for high-throughput workloads.
Memory usage has been reduced by approximately thirty percent.
The new caching layer supports both Redis and Memcached backends.
All deprecated APIs from version 2.x have been removed in this release.
Migration guides are available in the official documentation portal.
=====================================
Change Summary for Development Teams
=====================================
Bug Fixes and Patches
The critical security vulnerability in the authentication module has been resolved.
Input validation now correctly handles Unicode edge cases and special characters.
Session timeout logic has been rewritten to prevent race conditions.
=====================================
New Features and Enhancements
The user dashboard now supports real-time notifications via WebSocket protocol.
Dark mode has been implemented across all user interface components.
Export functionality now supports CSV, JSON, and XML output formats.
The search engine has been upgraded to support full-text indexing.
Two-factor authentication is now available for all account types.
Performance benchmarks show a forty percent improvement in query response times.
Batch processing jobs can now be scheduled with configurable retry policies.
=====================================
Known Issues and Limitations
The legacy import wizard is not compatible with the new file format.
Mobile Safari users may experience rendering delays on complex dashboard views.
=====================================
Support and Contact Information
For technical support, please contact the engineering helpdesk.
All bug reports should be submitted through the internal issue tracker.
=====================================
End of Release Notes
=====================================
"""

release_notes_path = os.path.join(workspace, "docs/release/release_notes.txt")
with open(release_notes_path, "w", encoding="utf-8") as f:
    f.write(release_notes_content)

# Also place a copy at workspace root for easier access
with open(os.path.join(workspace, "release_notes.txt"), "w", encoding="utf-8") as f:
    f.write(release_notes_content)

print("Workspace generated successfully.")
print(f"Main file: {release_notes_path}")
print(f"Total lines in release_notes.txt: {len(release_notes_content.splitlines())}")