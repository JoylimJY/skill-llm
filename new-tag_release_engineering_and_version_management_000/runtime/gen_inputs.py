#!/usr/bin/env python3
"""
Generate a realistic pnpm monorepo workspace simulating an analytics SDK project.
The repo has:
- packages/analytics-core  (shared utility, needs version bump)
- packages/analytics-sdk   (primary published package, needs version bump to 2.1.0)
- packages/analytics-cli   (unrelated, must NOT be bumped)
- .github/workflows/release.yml  (has an outdated package filter reference that must be fixed)
- Various distractor files
"""

import os
import json
import subprocess
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── helpers ──────────────────────────────────────────────────────────────────

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content))

def write_raw(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

# ── repo init ─────────────────────────────────────────────────────────────────

os.chdir(WORKSPACE)
subprocess.run(["git", "init"], check=True)
subprocess.run(["git", "config", "user.email", "dev@acme.io"], check=True)
subprocess.run(["git", "config", "user.name", "ACME Dev"], check=True)
subprocess.run(["git", "checkout", "-b", "main"], check=True)

# ── pnpm workspace config ─────────────────────────────────────────────────────

write(WORKSPACE / "pnpm-workspace.yaml", """\
    packages:
      - 'packages/*'
    """)

write(WORKSPACE / "package.json", """\
    {
      "name": "acme-monorepo",
      "private": true,
      "version": "0.0.0",
      "scripts": {
        "build": "pnpm -r build"
      },
      "devDependencies": {
        "typescript": "^5.4.0"
      }
    }
    """)

write(WORKSPACE / ".npmrc", """\
    registry=https://registry.npmjs.org/
    """)

# ── shared tsconfig ────────────────────────────────────────────────────────────

write(WORKSPACE / "tsconfig.base.json", """\
    {
      "compilerOptions": {
        "target": "ES2020",
        "module": "CommonJS",
        "declaration": true,
        "strict": true,
        "esModuleInterop": true,
        "skipLibCheck": true,
        "outDir": "dist",
        "rootDir": "src"
      }
    }
    """)

# ── analytics-core (shared, needs bump: 1.3.1 → 1.4.0) ─────────────────────

core_dir = WORKSPACE / "packages" / "analytics-core"

write(core_dir / "package.json", json.dumps({
    "name": "@acme/analytics-core",
    "version": "1.3.1",
    "main": "dist/index.js",
    "types": "dist/index.d.ts",
    "scripts": {
        "build": "tsc"
    },
    "devDependencies": {
        "typescript": "^5.4.0"
    }
}, indent=2))

write(core_dir / "tsconfig.json", """\
    {
      "extends": "../../tsconfig.base.json",
      "compilerOptions": {
        "outDir": "dist",
        "rootDir": "src"
      },
      "include": ["src"]
    }
    """)

write(core_dir / "src" / "index.ts", """\
    export interface EventPayload {
      name: string;
      ts: number;
      props?: Record<string, unknown>;
    }

    export function createEvent(name: string, props?: Record<string, unknown>): EventPayload {
      return { name, ts: Date.now(), props };
    }

    // NEW in 1.4.0: batch support
    export function createBatch(events: EventPayload[]): EventPayload[] {
      return events.map(e => ({ ...e, ts: Date.now() }));
    }
    """)

# ── analytics-sdk (primary published, needs bump: 2.0.3 → 2.1.0) ─────────────

sdk_dir = WORKSPACE / "packages" / "analytics-sdk"

write(sdk_dir / "package.json", json.dumps({
    "name": "@acme/analytics-sdk",
    "version": "2.0.3",
    "main": "dist/index.js",
    "types": "dist/index.d.ts",
    "scripts": {
        "build": "tsc"
    },
    "dependencies": {
        "@acme/analytics-core": "workspace:*"
    },
    "devDependencies": {
        "typescript": "^5.4.0"
    }
}, indent=2))

write(sdk_dir / "tsconfig.json", """\
    {
      "extends": "../../tsconfig.base.json",
      "compilerOptions": {
        "outDir": "dist",
        "rootDir": "src"
      },
      "include": ["src"]
    }
    """)

write(sdk_dir / "src" / "index.ts", """\
    import { createEvent, createBatch, EventPayload } from '@acme/analytics-core';

    export class AnalyticsClient {
      private endpoint: string;

      constructor(endpoint: string) {
        this.endpoint = endpoint;
      }

      track(name: string, props?: Record<string, unknown>): EventPayload {
        return createEvent(name, props);
      }

      trackBatch(events: Array<{ name: string; props?: Record<string, unknown> }>): EventPayload[] {
        const payloads = events.map(e => createEvent(e.name, e.props));
        return createBatch(payloads);
      }
    }

    export { EventPayload } from '@acme/analytics-core';
    """)

# ── analytics-cli (unrelated, must NOT be bumped: stays at 0.5.2) ─────────────

cli_dir = WORKSPACE / "packages" / "analytics-cli"

write(cli_dir / "package.json", json.dumps({
    "name": "@acme/analytics-cli",
    "version": "0.5.2",
    "main": "dist/index.js",
    "bin": {
        "acme-analytics": "dist/cli.js"
    },
    "scripts": {
        "build": "tsc"
    },
    "devDependencies": {
        "typescript": "^5.4.0"
    }
}, indent=2))

write(cli_dir / "tsconfig.json", """\
    {
      "extends": "../../tsconfig.base.json",
      "compilerOptions": {
        "outDir": "dist",
        "rootDir": "src"
      },
      "include": ["src"]
    }
    """)

write(cli_dir / "src" / "cli.ts", """\
    #!/usr/bin/env node
    console.log('acme-analytics CLI v0.5.2');
    """)

# ── GitHub Actions workflow ────────────────────────────────────────────────────
# BUG: the build step uses old package name "@acme/analytics-sdk-v2" instead of "@acme/analytics-sdk"
# The agent must fix this before the tag-triggered workflow can succeed.

write(WORKSPACE / ".github" / "workflows" / "release.yml", """\
    name: Release

    on:
      push:
        tags:
          - 'v*'
      workflow_dispatch:

    jobs:
      build-core:
        name: Build analytics-core
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: pnpm/action-setup@v3
            with:
              version: 9
          - uses: actions/setup-node@v4
            with:
              node-version: '20'
          - run: pnpm install --frozen-lockfile
          - run: pnpm --filter @acme/analytics-core build

      build-sdk:
        name: Build analytics-sdk
        runs-on: ubuntu-latest
        needs: build-core
        steps:
          - uses: actions/checkout@v4
          - uses: pnpm/action-setup@v3
            with:
              version: 9
          - uses: actions/setup-node@v4
            with:
              node-version: '20'
          - run: pnpm install --frozen-lockfile
          # BUG: wrong package name used here — should be @acme/analytics-sdk
          - run: pnpm --filter @acme/analytics-sdk-v2 build

      publish-sdk:
        name: Publish analytics-sdk to npm
        runs-on: ubuntu-latest
        needs: build-sdk
        steps:
          - uses: actions/checkout@v4
          - uses: pnpm/action-setup@v3
            with:
              version: 9
          - uses: actions/setup-node@v4
            with:
              node-version: '20'
              registry-url: 'https://registry.npmjs.org'
          - run: pnpm install --frozen-lockfile
          - run: pnpm --filter @acme/analytics-sdk publish --no-git-checks
            env:
              NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
    """)

# ── distractor files ───────────────────────────────────────────────────────────

write(WORKSPACE / "docs" / "architecture.md", """\
    # Architecture

    The ACME Analytics platform consists of three main components:
    - **analytics-core**: Low-level event primitives
    - **analytics-sdk**: Browser/Node SDK for event collection
    - **analytics-cli**: Developer tooling

    ## Release Process
    Tags are pushed manually after code review.
    """)

write(WORKSPACE / "docs" / "changelog" / "CHANGELOG-sdk.md", """\
    # analytics-sdk Changelog

    ## 2.0.3
    - Fix event deduplication edge case

    ## 2.0.2
    - Performance improvements

    ## 2.0.0
    - Major rewrite with TypeScript
    """)

write(WORKSPACE / "docs" / "changelog" / "CHANGELOG-core.md", """\
    # analytics-core Changelog

    ## 1.3.1
    - Patch: fix timestamp precision

    ## 1.3.0
    - Add EventPayload interface

    ## 1.2.0
    - Initial public release
    """)

write(WORKSPACE / ".github" / "workflows" / "ci.yml", """\
    name: CI

    on:
      push:
        branches: ['main', 'release/**']
      pull_request:

    jobs:
      lint:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - run: echo "linting..."

      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - run: echo "testing..."
    """)

write(WORKSPACE / ".github" / "CODEOWNERS", """\
    * @acme/platform-team
    packages/analytics-sdk/ @acme/sdk-team
    packages/analytics-core/ @acme/sdk-team
    """)

write(WORKSPACE / "scripts" / "check-versions.sh", """\
    #!/usr/bin/env bash
    # Checks that all workspace packages have consistent peer dependency declarations
    echo "Version consistency check passed."
    """)

write(WORKSPACE / "scripts" / "clean.sh", """\
    #!/usr/bin/env bash
    find packages -name 'dist' -type d -exec rm -rf {} + 2>/dev/null || true
    echo "Cleaned dist directories."
    """)

write(WORKSPACE / ".gitignore", """\
    node_modules/
    dist/
    *.tsbuildinfo
    .env
    """)

write(WORKSPACE / "packages" / "analytics-core" / "README.md", """\
    # @acme/analytics-core

    Internal event primitives used by analytics-sdk.
    """)

write(WORKSPACE / "packages" / "analytics-sdk" / "README.md", """\
    # @acme/analytics-sdk

    The official ACME Analytics browser/Node SDK.

    ## Installation
    npm install @acme/analytics-sdk
    """)

write(WORKSPACE / "packages" / "analytics-cli" / "README.md", """\
    # @acme/analytics-cli

    Developer CLI tools for the ACME Analytics platform.
    """)

# ── initial git commit + tags ─────────────────────────────────────────────────

subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-m", "chore: initial monorepo setup"], check=True)

# Add a fake remote so push commands are structurally valid but will fail safely
# We'll use a bare repo as the "remote"
bare_repo = WORKSPACE.parent / "remote.git"
subprocess.run(["git", "init", "--bare", str(bare_repo)], check=True)
subprocess.run(["git", "remote", "add", "origin", str(bare_repo)], check=True)
subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

# Simulate existing tags representing prior releases
subprocess.run(["git", "tag", "-a", "v2.0.3", "-m", "v2.0.3"], check=True)
subprocess.run(["git", "tag", "-a", "v2.0.2", "-m", "v2.0.2"], check=True)
subprocess.run(["git", "tag", "-a", "v2.0.0", "-m", "v2.0.0"], check=True)
subprocess.run(["git", "push", "origin", "v2.0.3", "v2.0.2", "v2.0.0"], check=True)

# Install pnpm dependencies so builds work
subprocess.run(
    ["pnpm", "install", "--registry", "https://registry.npmmirror.com"],
    cwd=str(WORKSPACE),
    check=True
)

# Re-add lock file changes
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-m", "chore: add pnpm lockfile"], check=True)
subprocess.run(["git", "push", "origin", "main"], check=True)

print("Workspace generated successfully.")