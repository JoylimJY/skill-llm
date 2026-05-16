import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Create realistic distractor directory structure - a developer's project workspace
dirs = [
    workspace / "projects" / "web_app" / "src" / "components",
    workspace / "projects" / "web_app" / "src" / "utils",
    workspace / "projects" / "web_app" / "config",
    workspace / "projects" / "ml_pipeline" / "data" / "raw",
    workspace / "projects" / "ml_pipeline" / "models",
    workspace / "tools" / "scripts",
    workspace / "tools" / "configs",
    workspace / "notes" / "ai_experiments",
    workspace / "notes" / "research",
    workspace / "dotfiles" / "vim",
    workspace / "dotfiles" / "zsh",
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files - realistic developer files
distractor_files = {
    workspace / "projects" / "web_app" / "src" / "components" / "Button.tsx": """
import React from 'react';
interface ButtonProps { label: string; onClick: () => void; }
export const Button: React.FC<ButtonProps> = ({ label, onClick }) => (
  <button onClick={onClick}>{label}</button>
);
""",
    workspace / "projects" / "web_app" / "src" / "utils" / "api.ts": """
export async function fetchData(endpoint: string) {
  const response = await fetch(`/api/${endpoint}`);
  return response.json();
}
""",
    workspace / "projects" / "web_app" / "config" / "webpack.config.js": """
module.exports = {
  entry: './src/index.tsx',
  output: { path: __dirname + '/dist', filename: 'bundle.js' },
  module: { rules: [{ test: /\\.tsx?$/, use: 'ts-loader' }] }
};
""",
    workspace / "projects" / "ml_pipeline" / "data" / "raw" / "sample_data.json": json.dumps({
        "dataset": "ai_benchmarks",
        "samples": [{"id": i, "score": random.uniform(0.5, 1.0)} for i in range(20)]
    }, indent=2),
    workspace / "projects" / "ml_pipeline" / "models" / "config.yaml": """
model:
  name: base_transformer
  layers: 12
  hidden_size: 768
  attention_heads: 12
training:
  batch_size: 32
  learning_rate: 0.0001
  epochs: 10
""",
    workspace / "tools" / "scripts" / "deploy.sh": """#!/bin/bash
echo "Deploying application..."
docker build -t myapp:latest .
docker push myapp:latest
echo "Deploy complete."
""",
    workspace / "tools" / "configs" / "eslint.json": json.dumps({
        "extends": ["eslint:recommended"],
        "rules": {"no-unused-vars": "warn", "semi": ["error", "always"]}
    }, indent=2),
    workspace / "notes" / "ai_experiments" / "experiment_log.md": """
# AI Experiment Log

## 2024-01 Baseline Tests
- Tested GPT-4 on code generation: 7.8/10
- Tested Claude on reasoning: 8.9/10
- Need better prompting strategies

## 2024-02 Prompt Engineering
- Chain-of-thought improves results by ~15%
- System prompts matter a lot for consistency
""",
    workspace / "notes" / "research" / "papers_to_read.txt": """
Attention Is All You Need
Constitutional AI: Harmlessness from AI Feedback
Chain-of-Thought Prompting Elicits Reasoning in Large Language Models
ReAct: Synergizing Reasoning and Acting in Language Models
""",
    workspace / "dotfiles" / "vim" / ".vimrc": """
set number
set relativenumber
set expandtab
set tabstop=4
set shiftwidth=4
syntax on
colorscheme desert
""",
    workspace / "dotfiles" / "zsh" / ".zshrc": """
export PATH="$HOME/.local/bin:$PATH"
alias ll='ls -la'
alias gs='git status'
alias gc='git commit'
export EDITOR=vim
""",
    workspace / "tools" / "scripts" / "ai_test.sh": """#!/bin/bash
# Placeholder for AI assistant testing
# TODO: configure the AI assistant properly first
echo "AI assistant not yet configured"
""",
}

for filepath, content in distractor_files.items():
    filepath.write_text(content.strip() + "\n")

# Create a partial/broken openclaw directory to act as a trap - exists but workspace subdir and SOUL.md do NOT exist
openclaw_dir = Path("/root/.openclaw")
openclaw_dir.mkdir(parents=True, exist_ok=True)

# Put a random config file in .openclaw but NOT the workspace subdirectory or SOUL.md
(openclaw_dir / "app.conf").write_text("""[openclaw]
version = 1.4.2
log_level = info
theme = dark
[user]
name = developer
locale = zh-CN
""")

# Create a misleading 'workspace' note elsewhere to trap agents
(workspace / "notes" / "ai_experiments" / "assistant_config_ideas.txt").write_text("""
Ideas for configuring AI assistant:
- Maybe put config in ~/config/assistant.yaml ?
- Or perhaps ~/.assistant/settings.json ?
- Need to research the correct location...
- Something about a SOUL file mentioned in docs
""")

print("Workspace initialized successfully.")
print(f"Distractor files created: {len(distractor_files)}")
print(f"Partial .openclaw dir created at: {openclaw_dir}")
print("SOUL.md NOT created - agent must create it at correct path with correct content")