import os
import random
import string

random.seed(42)

workspace = "/workspace"

# Create deeply nested distractor directory structure
distractor_dirs = [
    "workspace/reports/2024/q1",
    "workspace/reports/2024/q2",
    "workspace/reports/2024/q3",
    "workspace/logs/system",
    "workspace/logs/errors",
    "workspace/data/raw",
    "workspace/data/processed",
    "workspace/config/envs",
    "workspace/scripts/utils",
    "workspace/archive/old_chats",
]

for d in distractor_dirs:
    full = os.path.join(workspace, d)
    os.makedirs(full, exist_ok=True)

def rand_str(n=40):
    return ''.join(random.choices(string.ascii_letters + string.digits + " ", k=n))

# Distractor files — misleading names and formats
distractor_files = {
    "workspace/reports/2024/q1/summary.txt": f"Q1 Summary\n{rand_str()}\n{rand_str()}\n",
    "workspace/reports/2024/q2/summary.txt": f"Q2 Summary\n{rand_str()}\n",
    "workspace/reports/2024/q3/anomaly_report.csv": "timestamp,issue,severity\n2024-09-01,timeout,high\n2024-09-02,null_ptr,medium\n",
    "workspace/logs/system/sys.log": "[ERROR] 2024-01-01 disk full\n[WARN] 2024-01-02 memory usage high\n",
    "workspace/logs/errors/err.log": "FileNotFoundError: config.yaml missing\nKeyError: 'timeout'\n",
    "workspace/data/raw/interactions.json": '{"sessions": [{"id": 1, "messages": 42}, {"id": 2, "messages": 17}]}\n',
    "workspace/data/processed/clean.csv": "id,user,assistant\n1,hello,hi there\n2,bye,goodbye\n",
    "workspace/config/envs/production.env": "NODE_ENV=production\nPORT=3000\nLOG_LEVEL=info\n",
    "workspace/config/envs/staging.env": "NODE_ENV=staging\nPORT=3001\nLOG_LEVEL=debug\n",
    "workspace/scripts/utils/helpers.js": "function formatDate(d) { return d.toISOString().split('T')[0]; }\nmodule.exports = { formatDate };\n",
    "workspace/archive/old_chats/legacy_2023.txt": "User: old query\nAgent: old response\n[no timestamps here]\n",
    "workspace/archive/old_chats/legacy_2022.txt": "--- BEGIN LOG ---\nSession 1\nUser asked about billing.\n--- END LOG ---\n",
    # A deliberately wrong-format chat file to be a trap
    "workspace/archive/old_chats/2024-11-30.md": "timestamp: 10:00:00\nuser_msg: hey\nassistant_msg: hello\n",
    "workspace/data/raw/schema.json": '{"version": "2.0", "fields": ["timestamp", "user", "assistant"]}\n',
    "workspace/scripts/utils/logger_old.js": "// Deprecated logger\nconsole.log('logging...');\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# Write the conversation turns the agent must log — stored as structured task input
# The agent needs to find this file and use it as input
task_input_content = """\
# Conversation Archive Task

Archive the following support conversations to today's daily log.

## Turn 1
Time: 09:15:42
User: I can't log in to my account. It keeps saying invalid credentials.
Assistant: I've reset your credentials. Please try logging in with your email and the temporary password sent to you.

## Turn 2
Time: 09:22:10
User: The temporary password worked but now I'm getting a 403 error on the dashboard.
Assistant: Your account permissions were misconfigured. I've corrected the role assignments. Please refresh and try again.

## Turn 3
Time: 09:45:00
[Assistant-only note, no user message]
Assistant: Escalation ticket #4821 created for billing discrepancy. Awaiting finance review.

## Turn 4
Time: 10:03:55
User: Is there an ETA on the billing issue resolution?
Assistant: The finance team has been notified and aims to resolve it within 24 hours. You'll receive an email confirmation.
"""

task_input_path = os.path.join(workspace, "task_input.md")
with open(task_input_path, "w") as f:
    f.write(task_input_content)

print("Workspace setup complete.")
print(f"Task input written to: {task_input_path}")