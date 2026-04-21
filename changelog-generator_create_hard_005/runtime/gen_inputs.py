import os
import subprocess

# Create a new git repo with fixed commits for deterministic changelog generation
if os.path.exists('.git'):
    subprocess.run(['rm', '-rf', '.git'], check=True)
subprocess.run(['git', 'init'], check=True)

# Set fixed user info
subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True)
subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)

commits = [
    # Between March 1 and March 15, 2024
    ("2024-03-01T10:00:00", "feat: add team workspaces with invite feature"),
    ("2024-03-02T14:30:00", "fix: resolve large image upload failure"),
    ("2024-03-03T09:15:00", "improve: speed up file sync to 2x"),
    ("2024-03-05T16:50:00", "docs: update readme with setup instructions"),
    ("2024-03-06T11:00:00", "refactor: clean up workspace code"),
    ("2024-03-07T13:00:00", "feat: add keyboard shortcut help dialog"),
    ("2024-03-08T08:45:00", "fix: correct notification badge count"),
    ("2024-03-10T12:20:00", "breaking: remove deprecated sync API, update clients"),
    ("2024-03-11T15:00:00", "ci: update pipeline to run tests on node 20"),
    ("2024-03-13T09:00:00", "security: patch open redirect vulnerability"),
    ("2024-03-14T17:30:00", "fix: fix timezone confusion in scheduled posts"),
    
    # Outside the date range, should be ignored
    ("2024-02-28T23:59:59", "feat: early feature before March"),
    ("2024-03-16T00:00:01", "fix: post-March bug fix"),
]

for dt, msg in commits:
    filename = f"file_{dt.replace(':', '').replace('-', '').replace('T', '_')}.txt"
    with open(filename, "w") as f:
        f.write(f"Marker file for commit on {dt}\n")
    subprocess.run(["git", "add", filename], check=True)
    subprocess.run([
        "git", "commit", "-m", msg, "--date", dt
    ], check=True)

# Tag last commit before March range (for testing changelog from v1 to HEAD)
subprocess.run(["git", "tag", "v1.0.0", "HEAD~4"], check=True)
