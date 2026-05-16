import os
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create fake macOS application directory structure
app_dirs = [
    "/Applications",
    "/Applications/Utilities",
    "/System/Applications",
    "/System/Applications/Utilities",
]
home_dir = os.path.expanduser("~")
user_app_dir = os.path.join(home_dir, "Applications")
app_dirs.append(user_app_dir)

for d in app_dirs:
    os.makedirs(d, exist_ok=True)

# Create fake .app bundles (just directories with Contents/MacOS stub)
apps = {
    "/Applications": [
        "Sketch.app",
        "Figma.app",
        "Slack.app",
        "Zoom.app",
        "Google Chrome.app",
        "Visual Studio Code.app",
        "Spotify.app",
        "1Password 7 - Password Manager.app",
    ],
    "/Applications/Utilities": [
        "Terminal.app",
        "Activity Monitor.app",
        "Disk Utility.app",
        "ColorSync Utility.app",
    ],
    "/System/Applications": [
        "Photos.app",
        "Music.app",
        "Mail.app",
        "Safari.app",
        "Calendar.app",
        "Notes.app",
        "Maps.app",
    ],
    "/System/Applications/Utilities": [
        "Screenshot.app",
        "Script Editor.app",
    ],
    user_app_dir: [
        "DevUtils.app",
        "Proxyman.app",
        "TablePlus.app",
    ],
}

for directory, app_list in apps.items():
    for app_name in app_list:
        app_path = os.path.join(directory, app_name)
        macos_path = os.path.join(app_path, "Contents", "MacOS")
        os.makedirs(macos_path, exist_ok=True)
        # Create a fake executable inside
        exe_name = app_name.replace(".app", "").replace(" ", "")
        exe_path = os.path.join(macos_path, exe_name)
        with open(exe_path, "w") as f:
            f.write("#!/bin/bash\necho 'Fake app running'\n")
        os.chmod(exe_path, 0o755)
        # Create Info.plist stub
        plist_dir = os.path.join(app_path, "Contents")
        with open(os.path.join(plist_dir, "Info.plist"), "w") as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{app_name.replace('.app', '')}</string>
    <key>CFBundleIdentifier</key>
    <string>com.fake.{app_name.replace('.app', '').lower().replace(' ', '.')}</string>
</dict>
</plist>
""")

# Create distractor files in workspace to simulate a messy environment
distractor_dirs = [
    os.path.join(workspace, "logs"),
    os.path.join(workspace, "configs"),
    os.path.join(workspace, "scripts", "old"),
    os.path.join(workspace, "scripts", "deprecated"),
    os.path.join(workspace, "data", "exports"),
    os.path.join(workspace, "data", "imports", "batch_01"),
    os.path.join(workspace, "tmp"),
    os.path.join(workspace, "backup", "2023"),
    os.path.join(workspace, "backup", "2024"),
    os.path.join(workspace, "reports"),
]

for d in distractor_dirs:
    os.makedirs(d, exist_ok=True)

distractor_files = [
    (os.path.join(workspace, "logs", "system.log"), "2024-01-01 ERROR: disk full\n2024-01-02 INFO: cleared cache\n"),
    (os.path.join(workspace, "configs", "app_config.json"), '{"version": "1.0", "debug": false, "apps": ["Sketch", "Figma"]}\n'),
    (os.path.join(workspace, "configs", "launch_prefs.yaml"), "preferred_apps:\n  - Sketch\n  - DevUtils\nautostartup: false\n"),
    (os.path.join(workspace, "scripts", "old", "launch.sh"), "#!/bin/bash\n# deprecated launch script\nopen Sketch\n"),
    (os.path.join(workspace, "scripts", "deprecated", "find_apps.py"), "# This script is outdated\nimport subprocess\nsubprocess.run(['find', '/Applications', '-name', '*.app'])\n"),
    (os.path.join(workspace, "data", "exports", "app_inventory.csv"), "AppName,Path,LastUsed\nSketch,/Applications/Sketch.app,2024-06-01\nFigma,/Applications/Figma.app,2024-06-02\n"),
    (os.path.join(workspace, "data", "imports", "batch_01", "new_apps.txt"), "Sketch\nDevUtils\nProxyman\n"),
    (os.path.join(workspace, "tmp", "scratch.txt"), "temp notes: check if DevUtils is installed\n"),
    (os.path.join(workspace, "backup", "2023", "app_list.txt"), "old app list from 2023\nPhotoshop\nAcrobat\n"),
    (os.path.join(workspace, "backup", "2024", "app_list.txt"), "Sketch\nFigma\nDevUtils\n"),
    (os.path.join(workspace, "reports", "usage_stats.json"), '{"monthly_opens": {"Sketch": 45, "Figma": 30, "DevUtils": 12}}\n'),
]

for filepath, content in distractor_files:
    with open(filepath, "w") as f:
        f.write(content)

# Create the task specification file that the agent must fulfill
task_spec = """ONBOARDING AUTOMATION TASK
==========================
New developer Mac setup verification task.

Required apps to verify and launch:
1. Sketch  (design tool)
2. DevUtils  (developer utility tool)

For each app:
- Search for it on this system
- If found, record its full path
- Launch it

Output required: Write results to app_report.txt in /workspace
"""

with open(os.path.join(workspace, "task.txt"), "w") as f:
    f.write(task_spec)

print("Workspace initialized successfully.")
print(f"Fake app directories created: {list(apps.keys())}")