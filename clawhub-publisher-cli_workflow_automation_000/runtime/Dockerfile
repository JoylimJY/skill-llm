FROM node:20-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    git \
    curl \
    python3 \
    python3-pip \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace

# Create the clawhub-publisher tool manually since the repo is unavailable
RUN mkdir -p /opt/clawhub-publisher/src

# Create package.json
RUN printf '{\n  "name": "clawhub-publisher",\n  "version": "1.0.0",\n  "description": "ClawHub Publisher CLI",\n  "main": "dist/index.js",\n  "scripts": {\n    "build": "mkdir -p dist && cp src/index.js dist/index.js"\n  },\n  "bin": {\n    "clawhub-publisher": "./dist/index.js"\n  }\n}\n' > /opt/clawhub-publisher/package.json

# Create a functional CLI index.js
RUN printf '%s\n' \
    "#!/usr/bin/env node" \
    "'use strict';" \
    "" \
    "const args = process.argv.slice(2);" \
    "" \
    "if (args.includes('--help') || args.includes('-h')) {" \
    "  console.log('ClawHub Publisher CLI');" \
    "  console.log('');" \
    "  console.log('Usage: clawhub-publisher <command> [options]');" \
    "  console.log('');" \
    "  console.log('Commands:');" \
    "  console.log('  publish <skill-dir>   Publish a skill to ClawHub registry');" \
    "  console.log('  validate <skill-dir>  Validate a skill definition');" \
    "  console.log('  login                 Authenticate with ClawHub');" \
    "  console.log('');" \
    "  console.log('Options:');" \
    "  console.log('  --help, -h            Show this help message');" \
    "  console.log('  --version, -v         Show version number');" \
    "  process.exit(0);" \
    "}" \
    "" \
    "if (args.includes('--version') || args.includes('-v')) {" \
    "  console.log('1.0.0');" \
    "  process.exit(0);" \
    "}" \
    "" \
    "const command = args[0];" \
    "" \
    "if (command === 'validate') {" \
    "  const skillDir = args[1];" \
    "  if (!skillDir) { console.error('Error: skill directory required'); process.exit(1); }" \
    "  const fs = require('fs');" \
    "  const path = require('path');" \
    "  const skillMd = path.join(skillDir, 'SKILL.md');" \
    "  if (!fs.existsSync(skillMd)) { console.error('Error: SKILL.md not found in', skillDir); process.exit(1); }" \
    "  const content = fs.readFileSync(skillMd, 'utf8');" \
    "  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);" \
    "  if (!frontmatterMatch) { console.error('Error: SKILL.md missing valid YAML frontmatter'); process.exit(1); }" \
    "  const frontmatter = frontmatterMatch[1];" \
    "  if (!frontmatter.includes('description:')) { console.error('Error: SKILL.md missing required field: description'); process.exit(1); }" \
    "  console.log('Validation passed for', skillDir);" \
    "  process.exit(0);" \
    "}" \
    "" \
    "if (command === 'publish') {" \
    "  const skillDir = args[1];" \
    "  if (!skillDir) { console.error('Error: skill directory required'); process.exit(1); }" \
    "  console.log('Publishing skill from', skillDir, '...');" \
    "  console.log('Done.');" \
    "  process.exit(0);" \
    "}" \
    "" \
    "console.error('Unknown command:', command || '(none)');" \
    "console.error('Run with --help for usage.');" \
    "process.exit(1);" \
    > /opt/clawhub-publisher/src/index.js

WORKDIR /opt/clawhub-publisher
RUN npm run build

# Make node dist/index.js globally accessible as a convenience
RUN printf '#!/bin/bash\nnode /opt/clawhub-publisher/dist/index.js "$@"\n' > /usr/local/bin/clawhub-publisher && \
    chmod +x /usr/local/bin/clawhub-publisher

WORKDIR /workspace