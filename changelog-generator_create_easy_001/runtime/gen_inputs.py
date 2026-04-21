import os
import subprocess

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n" + result.stderr)
    return result.stdout.strip()

# Create a new git repo
if os.path.exists('repo'):
    import shutil
    shutil.rmtree('repo')
os.mkdir('repo')
os.chdir('repo')
run('git init')

# Configure user
run('git config user.name "Test User"')
run('git config user.email "test@example.com"')

# Create initial commit and tag v1.0.0
with open('file.txt', 'w') as f:
    f.write('Initial content\n')
run('git add file.txt')
run('git commit -m "Initial commit"')
run('git tag v1.0.0')

# Add commits after v1.0.0
commits = [
    ("feat: add user profile page", "Added a new user profile page so users can edit their personal info."),
    ("fix: correct typo in welcome message", "Fixed a typo in the welcome message displayed on login."),
    ("docs: update README", "Updated README file with new setup instructions."),
    ("refactor: rename variable", "Internal code cleanup by renaming variables."),
    ("improvement: faster image loading", "Improved image loading speed by optimizing caching."),
    ("test: add unit tests for login", "Added unit tests to cover login functionality.")
]

for i, (msg, content) in enumerate(commits, start=1):
    with open(f'file{i}.txt', 'w') as f:
        f.write(content + '\n')
    run(f'git add file{i}.txt')
    run(f'git commit -m "{msg}"')
