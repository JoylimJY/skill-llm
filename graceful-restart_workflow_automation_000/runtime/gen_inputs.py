import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"

# Create deep directory structure to simulate a real openclaw project
dirs = [
    ".openclaw/workspace/skills/graceful-restart",
    ".openclaw/workspace/skills/other-skill",
    ".openclaw/workspace/skills/deploy-helper",
    ".openclaw/config",
    ".openclaw/logs",
    ".openclaw/sessions",
    "project/src/pipeline",
    "project/src/gateway",
    "project/config/envs",
    "project/docs",
    "project/scripts",
    "data/migrations/v2",
    "data/migrations/v1",
]

home = os.path.expanduser("~")
for d in dirs:
    os.makedirs(os.path.join(home, d), exist_ok=True)

# Create distractor files to simulate real environment
distractor_files = {
    os.path.join(home, ".openclaw/config/gateway.json"): json.dumps({
        "host": "localhost",
        "port": 8080,
        "heartbeat_interval": 5,
        "session_timeout": 300
    }, indent=2),
    os.path.join(home, ".openclaw/logs/gateway.log"): "\n".join([
        "[2024-01-15 09:00:01] Gateway started",
        "[2024-01-15 09:05:23] Session main connected",
        "[2024-01-15 09:10:44] Heartbeat OK",
        "[2024-01-15 09:15:12] Config reload requested",
    ]),
    os.path.join(home, ".openclaw/sessions/main.json"): json.dumps({
        "session_id": "main",
        "status": "active",
        "last_task": "database migration v2"
    }, indent=2),
    os.path.join(home, ".openclaw/workspace/skills/other-skill/other-skill.js"): 
        "// Other skill - not relevant\nconsole.log('other skill');",
    os.path.join(home, ".openclaw/workspace/skills/deploy-helper/deploy-helper.js"):
        "// Deploy helper skill\nconsole.log('deploy helper');",
    os.path.join(home, "project/src/gateway/config.js"): 
        "module.exports = { port: 8080, maxConnections: 100 };",
    os.path.join(home, "project/src/pipeline/migration.py"): 
        "# Database migration script\nprint('migrating...')",
    os.path.join(home, "project/config/envs/production.env"):
        "DB_HOST=prod-db.internal\nDB_PORT=5432\nGATEWAY_PORT=8080",
    os.path.join(home, "project/config/envs/staging.env"):
        "DB_HOST=staging-db.internal\nDB_PORT=5432\nGATEWAY_PORT=8081",
    os.path.join(home, "project/docs/architecture.md"):
        "# Architecture\nGateway -> Pipeline -> Database",
    os.path.join(home, "project/scripts/deploy.sh"):
        "#!/bin/bash\necho 'deploying...'",
    os.path.join(home, "data/migrations/v2/schema.sql"):
        "ALTER TABLE users ADD COLUMN last_login TIMESTAMP;",
    os.path.join(home, "data/migrations/v1/schema.sql"):
        "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(255));",
    os.path.join(home, "project/src/pipeline/validate.py"):
        "# Validation script\nprint('validating data...')",
}

for filepath, content in distractor_files.items():
    with open(filepath, 'w') as f:
        f.write(content)

# Create a WRONG/TEMPTING restart method to trap naive agents
wrong_restart = os.path.join(home, "project/scripts/restart_gateway.sh")
with open(wrong_restart, 'w') as f:
    f.write("#!/bin/bash\n# WARNING: This script does NOT preserve session context!\nexec openclaw gateway restart\n")
os.chmod(wrong_restart, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)

# Create the actual graceful-restart.js script that records invocation
graceful_restart_js = os.path.join(home, ".openclaw/workspace/skills/graceful-restart/graceful-restart.js")
graceful_restart_content = r"""#!/usr/bin/env node
/**
 * graceful-restart skill
 * Records invocation arguments and simulates graceful gateway restart
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// Parse CLI arguments
const args = process.argv.slice(2);
let task = null;
let delay = 10; // default 10 seconds
let sessionMain = false;
let systemEvent = false;
let deleteAfterRun = false;

for (let i = 0; i < args.length; i++) {
    if (args[i] === '--task' && i + 1 < args.length) {
        task = args[i + 1];
        i++;
    } else if (args[i] === '--delay' && i + 1 < args.length) {
        delay = parseInt(args[i + 1], 10);
        i++;
    } else if (args[i] === '--session' && i + 1 < args.length) {
        if (args[i + 1] === 'main') sessionMain = true;
        i++;
    } else if (args[i] === '--system-event') {
        systemEvent = true;
    } else if (args[i] === '--delete-after-run') {
        deleteAfterRun = true;
    }
}

// Record the invocation for evaluation
const record = {
    invoked: true,
    timestamp: new Date().toISOString(),
    raw_args: args,
    task: task,
    delay: delay,
    session_main: sessionMain,
    system_event: systemEvent,
    delete_after_run: deleteAfterRun,
    called_via_node: true
};

const recordPath = path.join(os.homedir(), '.openclaw', 'graceful_restart_invocation.json');
fs.writeFileSync(recordPath, JSON.stringify(record, null, 2));

// Simulate setting up cron
console.log(`[graceful-restart] Setting up one-time cron task (delay: ${delay}s)...`);
if (task) {
    console.log(`[graceful-restart] Task to resume: "${task}"`);
}
console.log(`[graceful-restart] Cron scheduled: will send system-event to main session in ${delay}s`);
console.log(`[graceful-restart] Executing Gateway restart...`);
console.log(`[graceful-restart] Gateway restart initiated successfully.`);
console.log(`[graceful-restart] After ${delay}s, session 'main' will receive task context.`);

process.exit(0);
"""

with open(graceful_restart_js, 'w') as f:
    f.write(graceful_restart_content)
os.chmod(graceful_restart_js, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# Create a scenario context file for the agent to understand the situation
scenario_file = os.path.join(workspace, "SITUATION.md")
with open(scenario_file, 'w') as f:
    f.write("""# Current Situation

## Active Task
The gateway is currently handling a database schema migration task:
- Task: "resume PostgreSQL schema migration for users table - adding indexes and foreign keys"
- Status: In progress (50% complete)
- Requires gateway restart to apply new TLS configuration

## Gateway Restart Required
A new TLS certificate has been deployed to production. The gateway must be restarted
to pick up the new certificate. 

## Requirement
- The restart must NOT lose the current migration task context
- After restart, the system should automatically resume the migration task
- The ops team requires a 30-second wake delay (instead of default) to allow
  downstream services enough time to warm up before the gateway sends the resume signal

## Current Directory
The workspace is at /workspace. The openclaw environment is set up under the home directory.
""")

print("Workspace initialized successfully.")
print(f"Graceful restart script created at: {graceful_restart_js}")
print(f"Scenario file created at: {scenario_file}")