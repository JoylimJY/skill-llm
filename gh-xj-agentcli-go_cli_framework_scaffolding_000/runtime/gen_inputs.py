import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Create a partially broken / half-baked attempt at the project ──────────
project_dir = workspace / "infra-deployer"
project_dir.mkdir(exist_ok=True)

# Wrong main.go - doesn't use Execute pattern correctly
(project_dir / "main.go").write_text("""\
package main

import (
\t"fmt"
\t"os"
)

func main() {
\tfmt.Println("infra-deployer starting")
\tif len(os.Args) > 1 && os.Args[1] == "version" {
\t\tfmt.Println("v0.0.1")
\t}
}
""")

# Wrong cmd layout - flat instead of using cobrax
cmd_dir = project_dir / "cmd"
cmd_dir.mkdir(exist_ok=True)

(cmd_dir / "root.go").write_text("""\
package cmd

import (
\t"fmt"

\t"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
\tUse:   "infra-deployer",
\tShort: "Infrastructure deployment tool",
\tRun: func(cmd *cobra.Command, args []string) {
\t\tfmt.Println("use a subcommand")
\t},
}

func Execute() error {
\treturn rootCmd.Execute()
}
""")

# Broken config - wrong pattern, no configx, no NormalizeEnv
internal_config = project_dir / "internal" / "config"
internal_config.mkdir(parents=True, exist_ok=True)

(internal_config / "load.go").write_text("""\
package config

import (
\t"encoding/json"
\t"os"
)

type Config struct {
\tEnv     string `json:"env"`
\tTimeout int    `json:"timeout"`
\tRegion  string `json:"region"`
}

func Load(filePath string) (*Config, error) {
\tcfg := &Config{Env: "default", Timeout: 30, Region: "us-east-1"}
\tif filePath != "" {
\t\tdata, err := os.ReadFile(filePath)
\t\tif err != nil {
\t\t\treturn nil, err
\t\t}
\t\tif err := json.Unmarshal(data, cfg); err != nil {
\t\t\treturn nil, err
\t\t}
\t}
\treturn cfg, nil
}
""")

(internal_config / "schema.go").write_text("""\
package config

// Config holds application configuration
type AppConfig struct {
\tEnvironment string
\tDebug       bool
}
""")

# Broken app directory
internal_app = project_dir / "internal" / "app"
internal_app.mkdir(parents=True, exist_ok=True)

(internal_app / "bootstrap.go").write_text("""\
package app

import "fmt"

func Bootstrap() {
\tfmt.Println("bootstrapping...")
}
""")

# Missing lifecycle.go and errors.go in app
# Wrong io output
internal_io = project_dir / "internal" / "io"
internal_io.mkdir(parents=True, exist_ok=True)

(internal_io / "output.go").write_text("""\
package io

import "fmt"

func Print(msg string) {
\tfmt.Println(msg)
}
""")

# Missing smokecheck
# Wrong pkg/version
pkg_version = project_dir / "pkg" / "version"
pkg_version.mkdir(parents=True, exist_ok=True)

(pkg_version / "version.go").write_text("""\
package version

const Version = "0.0.1-dev"
""")

# No test directory
# No Taskfile.yml
# Missing smoke schema

# go.mod with wrong dependencies (no agentcli-go)
(project_dir / "go.mod").write_text("""\
module github.com/platform-team/infra-deployer

go 1.23

require (
\tgithub.com/spf13/cobra v1.8.0
)
""")

# go.sum placeholder
(project_dir / "go.sum").write_text("# placeholder\n")

# ── Distractor files to test contextual awareness ──────────────────────────

# Old deploy scripts
old_scripts = workspace / "old-scripts"
old_scripts.mkdir(exist_ok=True)
(old_scripts / "deploy.sh").write_text("#!/bin/bash\necho 'legacy deploy'\n")
(old_scripts / "rollback.sh").write_text("#!/bin/bash\necho 'rollback'\n")
(old_scripts / "config.yaml").write_text("env: staging\ntimeout: 60\n")

# Random Go files that look like they belong somewhere but don't
distractor_go = workspace / "scratch"
distractor_go.mkdir(exist_ok=True)
(distractor_go / "experiment.go").write_text("""\
package scratch

// This was an experiment - ignore
func tryThing() {}
""")
(distractor_go / "notes.txt").write_text("TODO: figure out configx prefix convention\nMaybe INFRA_ or DEPLOY_ prefix?\n")

# Fake CI config
ci_dir = workspace / ".github" / "workflows"
ci_dir.mkdir(parents=True, exist_ok=True)
(ci_dir / "ci.yml").write_text("""\
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: go build ./...
""")

# Fake documentation with wrong info
docs_dir = workspace / "docs"
docs_dir.mkdir(exist_ok=True)
(docs_dir / "architecture.md").write_text("""\
# Architecture

The infra-deployer tool manages infrastructure deployments.

## Commands
- `deploy` - runs deployment checks
- `version` - shows version

## Config
Config is loaded from ~/.infra-deployer/config.json
Environment variables use INFRA_ prefix (TBD - not confirmed)
""")
(docs_dir / "config-options.md").write_text("""\
# Configuration Options

| Key | Default | Description |
|-----|---------|-------------|
| env | default | deployment environment |
| timeout | 30 | operation timeout |
| region | us-east-1 | target region |
""")

# Fake test files
test_dir = workspace / "tests-old"
test_dir.mkdir(exist_ok=True)
(test_dir / "integration_test.go").write_text("""\
package tests

import "testing"

func TestDeploy(t *testing.T) {
\t// old test - not used
\tt.Skip("skipping old test")
}
""")

# Another fake project attempt (different approach)
attempt2 = workspace / "deployer-v2-attempt"
attempt2.mkdir(exist_ok=True)
(attempt2 / "main.go").write_text("""\
package main

import "github.com/platform-team/infra-deployer/cmd"

func main() {
\tcmd.Execute()
}
""")
(attempt2 / "README.md").write_text("# Deployer v2 attempt - abandoned\n")

# Env file with misleading prefix
(workspace / ".env.example").write_text("""\
# Example environment variables
INFRA_ENV=production
INFRA_TIMEOUT=60
DEPLOY_REGION=eu-west-1
""")

# A requirements-like spec document
(workspace / "SPEC.md").write_text("""\
# infra-deployer CLI Specification

## Requirements
1. Must support `deploy` command for running deployment checks
2. Must read config from file AND environment variables
3. Environment variable prefix should match the tool name
4. Must support --verbose, --config, --json flags
5. Module path: github.com/platform-team/infra-deployer

## Deliverable
A fully scaffolded Go CLI project at ./infra-deployer/ ready for the platform team.
""")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")