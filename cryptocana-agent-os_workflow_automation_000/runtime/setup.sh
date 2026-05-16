#!/bin/bash
set -e

cd /workspace

# agent-os is not a real npm package, so we create a local stub module
mkdir -p node_modules/agent-os

cat > node_modules/agent-os/index.js << 'EOF'
class AgentOS {
  constructor(projectId) {
    this.projectId = projectId;
    this.teams = [];
    this.taskTemplates = {};
  }

  addTeam(id, name, capabilities) {
    this.teams.push({ id, name, capabilities });
    return this;
  }

  setTaskTemplate(taskType, steps) {
    this.taskTemplates[taskType] = steps;
    return this;
  }

  async run(goal, taskTypes) {
    const result = {
      projectId: this.projectId,
      goal: goal,
      teams: this.teams,
      taskTypes: taskTypes,
      taskTemplates: this.taskTemplates,
      status: "completed",
      timestamp: new Date().toISOString()
    };
    return result;
  }
}

module.exports = { AgentOS };
EOF

cat > node_modules/agent-os/package.json << 'EOF'
{
  "name": "agent-os",
  "version": "1.0.0",
  "main": "index.js"
}
EOF

# Make scripts executable
chmod +x warehouse-project/scripts/migrate.sh

# Verify agent-os installed
node -e "const { AgentOS } = require('agent-os'); console.log('agent-os loaded OK');"

echo "Setup complete. agent-os is ready."