import os
import subprocess

def write_file(fname, content):
    with open(fname, 'w') as f:
        f.write(content)

def setup_git_repo():
    # initialize repo
    if os.path.exists('.git'):
        subprocess.run(['rm', '-rf', '.git'], check=True)
    subprocess.run(['git', 'init'], check=True)

    # Create initial commit
    write_file('readme.md', '# Example Project\n[MARKER-INIT]')
    subprocess.run(['git', 'add', 'readme.md'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)

    # Tag v1.2.0
    subprocess.run(['git', 'tag', 'v1.2.0'], check=True)

    # Add commits between v1.2.0 and v1.3.0
    commits = [
        ('feat(auth): add login feature', 'Add login functionality for users. [MARKER-FEATURE]'),
        ('fix(auth): correct token validation bug', 'Fix bug with token expiry check. [MARKER-BUGFIX]'),
        ('chore(tests): add unit tests for auth', 'Add tests for authentication module.'),
        ('refactor(api): improve response handling', 'Refactor API response code. This is internal only.'),
        ('docs: update README with setup instructions', 'Update readme docs.'),
        ('feat(ui): add dark mode support', 'Users can now switch to dark mode. [MARKER-FEATURE]'),
        ('perf(sync): improve sync speed by 30%', 'Optimization to sync feature. [MARKER-IMPROVEMENT]'),
        ('fix(ui): resolve button misalignment issue', 'Fix button alignment bug on homepage. [MARKER-BUGFIX]'),
        ('breaking(change): update API endpoint from /v1 to /v2', 'API endpoint changed, update required. [MARKER-BREAKING]'),
        ('security: patch vulnerability in auth flow', 'Security fix for auth vulnerability. [MARKER-SECURITY]')
    ]

    for msg, content in commits:
        filename = msg.split('(')[-1].split(')')[0] + '.txt'
        write_file(filename, content)
        subprocess.run(['git', 'add', filename], check=True)
        subprocess.run(['git', 'commit', '-m', msg], check=True)

    # Tag v1.3.0
    subprocess.run(['git', 'tag', 'v1.3.0'], check=True)

if __name__ == '__main__':
    setup_git_repo()
