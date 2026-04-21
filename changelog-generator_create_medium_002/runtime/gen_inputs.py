import os
import subprocess

# Set a deterministic git user environment
os.environ["GIT_AUTHOR_NAME"] = "Test User"
os.environ["GIT_AUTHOR_EMAIL"] = "testuser@example.com"
os.environ["GIT_COMMITTER_NAME"] = "Test User"
os.environ["GIT_COMMITTER_EMAIL"] = "testuser@example.com"

# Initialize a new git repo
subprocess.run(["git", "init"], check=True)

# Configure user
subprocess.run(["git", "config", "user.name", "Test User"], check=True)
subprocess.run(["git", "config", "user.email", "testuser@example.com"], check=True)

# Create commits with dates between Mar 1 and Mar 15, 2024
commits = [
    ("2024-03-02T10:00:00", "feat: add user profile customization"),
    ("2024-03-05T15:00:00", "fix: resolve crash on login when using special characters"),
    ("2024-03-06T09:30:00", "chore: update dependencies"),
    ("2024-03-08T13:00:00", "refactor: simplify authentication flow"),
    ("2024-03-10T11:45:00", "feat: introduce dark mode for better accessibility"),
    ("2024-03-11T16:20:00", "fix: correct typo in payment processing"),
    ("2024-03-12T08:15:00", "perf: improve dashboard load time"),
    ("2024-03-13T14:30:00", "BREAKING CHANGE: change API endpoint for fetching user data"),
    ("2024-03-14T10:00:00", "test: add unit tests for notifications"),
    ("2024-03-15T17:00:00", "docs: update README with new setup instructions")
]

for date_iso, message in commits:
    # Create a dummy file to commit
    filename = "file_" + date_iso.replace(":", "_") + ".txt"
    with open(filename, "w") as f:
        f.write(f"Commit marker: {message}\n")

    # Commit with specified date
    env = os.environ.copy()
    env["GIT_COMMITTER_DATE"] = date_iso
    env["GIT_AUTHOR_DATE"] = date_iso

    subprocess.run(["git", "add", filename], check=True, env=env)
    subprocess.run(["git", "commit", "-m", message], check=True, env=env)

# Tag a previous release v2.4.0 before March 1 for reference
subprocess.run(["git", "tag", "v2.4.0", "HEAD~10"], check=True)
