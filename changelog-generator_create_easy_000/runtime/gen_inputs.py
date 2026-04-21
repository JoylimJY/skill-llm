import os
import subprocess

def run(cmd):
    subprocess.run(cmd, shell=True, check=True)

# Initialize git repo
if os.path.exists('.git'):
    run('rm -rf .git')
run('git init')

# Configure user
run('git config user.email "tester@example.com"')
run('git config user.name "Test User"')

commits = [
    # Date format: YYYY-MM-DD
    ("2024-03-02", "feat: Add user profile customization option"),
    ("2024-03-03", "fix: Resolve crash when uploading large files"),
    ("2024-03-04", "docs: Update README with new instructions"),
    ("2024-03-05", "improvement: Speed up sync on mobile devices"),
    ("2024-03-06", "test: Add unit tests for billing module"),
    ("2024-03-07", "refactor: Simplify auth middleware code"),
    ("2024-03-08", "fix: Correct timezone display on dashboard"),
    ("2024-03-09", "feat: Enable dark mode for app interface"),
]

for date, message in commits:
    # Create a dummy file to commit
    fname = "file_" + date.replace('-', '') + ".txt"
    with open(fname, 'w') as f:
        f.write(f"Marker for {message}\n")
    
    run(f'git add {fname}')
    run(f'GIT_COMMITTER_DATE="{date}T12:00:00" git commit --date "{date}T12:00:00" -m "{message}"')
