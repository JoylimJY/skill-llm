import os
import subprocess

# Create a git repo and add deterministic commits between 2024-03-01 and 2024-03-15

def run(cmd):
    subprocess.check_call(cmd, shell=True)

if __name__ == '__main__':
    if os.path.exists('.git'):
        run('rm -rf .git')

    run('git init')
    run('git config user.name "Test User"')
    run('git config user.email "test@example.com"')

    base_date = '2024-03-01T12:00:00'

    commits = [
        ("2024-03-01T12:00:00", "feat: Add team workspaces to organize projects"),
        ("2024-03-02T10:30:00", "feat: Add keyboard shortcuts overview with ? key"),
        ("2024-03-03T09:00:00", "perf: Improve file sync speed to 2x"),
        ("2024-03-04T14:30:00", "improve: Enhance search to include file contents"),
        ("2024-03-05T08:00:00", "fix: Prevent large image upload failure"),
        ("2024-03-06T11:00:00", "fix: Correct timezone confusion in scheduled posts"),
        ("2024-03-07T13:15:00", "fix: Fix notification badge count issue"),
        ("2024-03-08T09:00:00", "chore: Refactor sync module for clarity"),
        ("2024-03-09T15:20:00", "test: Add unit tests for search functionality"),
        ("2024-03-10T10:00:00", "feat: Introduce breaking change to API v2 auth flow"),
        ("2024-03-11T16:00:00", "security: Patch vulnerability in password reset process"),
        ("2024-03-12T12:00:00", "docs: Update changelog format guidelines"),
        ("2024-03-13T14:45:00", "improve: Faster startup time for mobile app"),
        ("2024-03-14T09:30:00", "fix: Resolve crash when opening settings on iOS"),
        ("2024-03-15T11:30:00", "feat: Enable multi-factor authentication option")
    ]

    for date, msg in commits:
        # create dummy commit
        filename = msg.replace(':', '').replace(' ', '_').lower() + '.txt'
        with open(filename, 'w') as f:
            f.write(f'# Commit marker for testing\nCommit message: {msg}\n')

        # Create commit with fixed date
        env = dict(os.environ)
        env['GIT_COMMITTER_DATE'] = date
        env['GIT_AUTHOR_DATE'] = date
        run(f'git add {filename}')
        run(f'git commit -m "{msg}" --date "{date}"')
