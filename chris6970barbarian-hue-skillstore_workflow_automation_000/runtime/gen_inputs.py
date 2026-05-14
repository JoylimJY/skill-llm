import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"

# ─── 1. Build distractor directory structure ───────────────────────────────
dirs = [
    "projects/home-automation/docs",
    "projects/home-automation/tests",
    "projects/home-automation/src/lights",
    "projects/home-automation/src/sensors",
    "projects/legacy/old-plugins",
    "projects/legacy/archived",
    "configs/dev",
    "configs/prod",
    "notes/meetings",
    "notes/research",
    "scripts/deploy",
    "scripts/ci",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ─── Distractor files ───────────────────────────────────────────────────────
distractor_files = {
    "projects/home-automation/docs/architecture.md": """\
# Home Automation Architecture
The platform uses a plugin-based model for device integrations.
Each plugin must expose a standard control interface.
""",
    "projects/home-automation/docs/roadmap.md": """\
# Roadmap Q3
- Philips Hue integration (PENDING)
- Zigbee mesh support
- Energy monitoring dashboard
""",
    "projects/home-automation/tests/test_lights.py": """\
import pytest
def test_light_toggle():
    # TODO: implement once huectl plugin is available
    pass
""",
    "projects/home-automation/src/lights/README_PLACEHOLDER.txt": """\
Placeholder. No plugin code yet for Hue lights.
""",
    "projects/home-automation/src/sensors/motion.json": json.dumps({
        "sensor_type": "motion",
        "protocol": "zigbee",
        "polling_interval_s": 30
    }, indent=2),
    "projects/legacy/old-plugins/hue-v0.js": """\
// DEPRECATED: old hue controller, do not use
// This file is kept for reference only.
const BASE_URL = 'http://192.168.1.10/api';
""",
    "projects/legacy/archived/README.txt": """\
These plugins are archived and no longer maintained.
Use the current skill system instead.
""",
    "configs/dev/platform.json": json.dumps({
        "environment": "development",
        "log_level": "debug",
        "skill_dir": "~/.openclaw/workspace/skills/"
    }, indent=2),
    "configs/prod/platform.json": json.dumps({
        "environment": "production",
        "log_level": "warn",
        "skill_dir": "~/.openclaw/workspace/skills/"
    }, indent=2),
    "notes/meetings/2024-06-12-standup.md": """\
# Standup 2024-06-12
- @alice: working on Hue light plugin
- @bob: reviewing smart speaker integrations
- Decision: use the skillstore tool for new plugin scaffolding
""",
    "notes/research/smart_home_landscape.md": """\
# Smart Home Landscape Research
Various protocols: Zigbee, Z-Wave, Matter, HomeKit
Key vendors: Philips (Hue), Sonos, Samsung SmartThings
Existing company tools: skillstore CLI for plugin management
""",
    "notes/research/competitor_analysis.txt": """\
Competitor A: supports 12 device types
Competitor B: supports 30 device types, including Hue
Our target: match competitor B by Q4
""",
    "scripts/deploy/deploy.sh": """\
#!/bin/bash
echo 'Deploying home automation platform...'
rsync -av ./dist/ user@prod-server:/opt/homeauto/
""",
    "scripts/ci/lint.sh": """\
#!/bin/bash
eslint ./projects/home-automation/src/
""",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ─── 2. Install skillstore as a local CLI tool ─────────────────────────────
# Create the ~/.openclaw/workspace/skills/ directory
skills_dir = os.path.expanduser("~/.openclaw/workspace/skills")
os.makedirs(skills_dir, exist_ok=True)

# Create skillstore directory
skillstore_dir = os.path.join(workspace, "skillstore")
os.makedirs(skillstore_dir, exist_ok=True)

# Write config.json
config = {
    "installed": [],
    "install_history": []
}
with open(os.path.join(skillstore_dir, "config.json"), "w") as f:
    json.dump(config, f, indent=2)

# Write the main.js — full realistic implementation of skillstore
main_js = r"""#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, spawnSync } = require('child_process');

// ── Known skills database (20 built-in) ──────────────────────────────────
const KNOWN_SKILLS = [
  { name: 'homeassistant', description: 'Smart home control (HA API)', tags: ['home', 'assistant', 'smart', 'control', 'device', 'automation'] },
  { name: 'gog', description: 'Google Workspace (Gmail, Calendar, Drive)', tags: ['google', 'gmail', 'calendar', 'drive', 'workspace', 'email'] },
  { name: 'weather', description: 'Weather forecasts and alerts', tags: ['weather', 'forecast', 'temperature', 'climate'] },
  { name: 'github', description: 'GitHub CLI integration', tags: ['github', 'git', 'repository', 'code', 'pull', 'request'] },
  { name: 'himalaya', description: 'Email via IMAP/SMTP', tags: ['email', 'imap', 'smtp', 'mail', 'himalaya'] },
  { name: 'obsidian', description: 'Obsidian vault integration', tags: ['obsidian', 'notes', 'vault', 'markdown', 'knowledge'] },
  { name: 'sonoscli', description: 'Sonos speaker control', tags: ['sonos', 'speaker', 'music', 'audio', 'smart', 'home'] },
  { name: 'blucli', description: 'BluOS speaker control', tags: ['blucli', 'bluos', 'speaker', 'music', 'audio'] },
  { name: 'eightctl', description: 'Eight Sleep pod control', tags: ['eight', 'sleep', 'pod', 'bed', 'temperature'] },
  { name: 'ordercli', description: 'Food delivery orders', tags: ['food', 'delivery', 'order', 'restaurant'] },
  { name: 'blogwatcher', description: 'RSS feed monitoring', tags: ['rss', 'blog', 'feed', 'monitor', 'news'] },
  { name: 'gifgrep', description: 'GIF search and download', tags: ['gif', 'search', 'download', 'image', 'animation'] },
  { name: 'video-frames', description: 'Video frame extraction', tags: ['video', 'frame', 'extract', 'ffmpeg'] },
  { name: 'youtube-summarizer', description: 'YouTube transcript summary', tags: ['youtube', 'summary', 'transcript', 'video'] },
  { name: 'ga4', description: 'Google Analytics 4 integration', tags: ['google', 'analytics', 'ga4', 'tracking', 'metrics'] },
  { name: 'gsc', description: 'Google Search Console integration', tags: ['google', 'search', 'console', 'seo', 'webmaster'] },
  { name: 'wacli', description: 'WhatsApp messaging', tags: ['whatsapp', 'messaging', 'chat', 'mobile'] },
  { name: 'browser', description: 'Browser automation', tags: ['browser', 'automation', 'web', 'scrape', 'chrome'] },
  { name: 'healthcheck', description: 'Security hardening and health checks', tags: ['security', 'health', 'check', 'hardening', 'audit'] },
  { name: 'openclaw-migrate', description: 'Migrate OpenClaw skills between versions', tags: ['migrate', 'openclaw', 'upgrade', 'version'] },
];

// ── Jaccard + keyword boost scoring ──────────────────────────────────────
function tokenize(str) {
  return str.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter(Boolean);
}

function jaccardSimilarity(setA, setB) {
  const a = new Set(setA);
  const b = new Set(setB);
  const intersection = new Set([...a].filter(x => b.has(x)));
  const union = new Set([...a, ...b]);
  return union.size === 0 ? 0 : intersection.size / union.size;
}

function scoreSkill(skill, queryTokens) {
  const skillTokens = tokenize(skill.name + ' ' + skill.description + ' ' + skill.tags.join(' '));
  const baseScore = jaccardSimilarity(queryTokens, skillTokens);
  // keyword boost: +0.15 per query token that appears in tags or name
  const nameTokens = tokenize(skill.name);
  let boost = 0;
  for (const qt of queryTokens) {
    if (skill.tags.includes(qt) || nameTokens.includes(qt)) {
      boost += 0.15;
    }
  }
  return Math.min(1.0, baseScore + boost);
}

function renderBar(score, width = 10) {
  const filled = Math.round(score * width);
  return '█'.repeat(filled) + '░'.repeat(width - filled);
}

function renderScore(score) {
  const pct = Math.round(score * 100);
  const bar = renderBar(score);
  if (score >= 0.5) return `\x1b[32m${bar}\x1b[0m ${pct}%`;
  return `\x1b[33m${bar}\x1b[0m ${pct}%`;
}

// ── Subcommands ───────────────────────────────────────────────────────────

function cmdList() {
  const configPath = path.join(__dirname, 'config.json');
  let config = { installed: [] };
  try { config = JSON.parse(fs.readFileSync(configPath, 'utf8')); } catch (e) {}
  if (!config.installed || config.installed.length === 0) {
    console.log('No skills installed yet.');
    return;
  }
  console.log('Installed skills:');
  for (const s of config.installed) {
    console.log(`  - ${s}`);
  }
}

function cmdKnown() {
  console.log(`Known skills (${KNOWN_SKILLS.length} built-in):\n`);
  for (const skill of KNOWN_SKILLS) {
    console.log(`  ${skill.name.padEnd(22)} ${skill.description}`);
  }
}

function cmdCreate(name) {
  if (!name) {
    console.error('Usage: skillstore create <name>');
    process.exit(1);
  }
  const skillsDir = path.join(os.homedir(), '.openclaw', 'workspace', 'skills');
  const skillDir = path.join(skillsDir, name);
  if (fs.existsSync(skillDir)) {
    console.log(`Skill directory already exists: ${skillDir}`);
    return;
  }
  fs.mkdirSync(skillDir, { recursive: true });

  // SKILL.md template
  const skillMd = `# ${name} - OpenClaw Skill

## Skill Metadata

- **Name**: ${name}
- **Type**: OpenClaw Skill
- **Purpose**: TODO: describe what this skill does

## Setup Commands

\`\`\`bash
# TODO: add setup steps
npm install
\`\`\`

## Usage Commands

\`\`\`bash
# TODO: add usage examples
${name} --help
\`\`\`

## Files

\`\`\`
${name}/
├── SKILL.md       # This file
├── README.md      # User docs
├── main.js        # CLI entry point
└── config.json    # Configuration
\`\`\`
`;

  // main.js template
  const mainJs = `#!/usr/bin/env node
'use strict';

// ${name} - OpenClaw Skill
// TODO: implement skill logic

const args = process.argv.slice(2);

if (args.length === 0 || args[0] === '--help') {
  console.log('Usage: ${name} <command> [options]');
  console.log('');
  console.log('Commands:');
  console.log('  TODO: list commands here');
  process.exit(0);
}

console.log('${name}: command not yet implemented', args);
`;

  // config.json template
  const configJson = JSON.stringify({
    name: name,
    version: '0.1.0',
    description: 'TODO: describe this skill',
    author: '',
    dependencies: {},
    openclaw: {
      type: 'skill',
      created: new Date().toISOString().split('T')[0]
    }
  }, null, 2);

  fs.writeFileSync(path.join(skillDir, 'SKILL.md'), skillMd);
  fs.writeFileSync(path.join(skillDir, 'main.js'), mainJs);
  fs.writeFileSync(path.join(skillDir, 'config.json'), configJson);

  // Update skillstore config.json
  const configPath = path.join(__dirname, 'config.json');
  let config = { installed: [], install_history: [] };
  try { config = JSON.parse(fs.readFileSync(configPath, 'utf8')); } catch(e) {}
  config.installed = config.installed || [];
  config.install_history = config.install_history || [];
  if (!config.installed.includes(name)) config.installed.push(name);
  config.install_history.push({ name, action: 'create', timestamp: new Date().toISOString() });
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

  console.log(`\nSkill scaffolded at: ${skillDir}`);
  console.log(`Files created:`);
  console.log(`  ${skillDir}/SKILL.md`);
  console.log(`  ${skillDir}/main.js`);
  console.log(`  ${skillDir}/config.json`);
  console.log(`\nEdit SKILL.md to document your skill, then implement main.js.`);
}

function cmdSearch(queryTokens) {
  const THRESHOLD = 0.30;
  const results = [];

  // 1. Known skills
  for (const skill of KNOWN_SKILLS) {
    const score = scoreSkill(skill, queryTokens);
    if (score >= THRESHOLD) {
      results.push({ source: 'KNOWN', name: skill.name, description: skill.description, score });
    }
  }

  // 2. Local skills
  const skillsDir = path.join(os.homedir(), '.openclaw', 'workspace', 'skills');
  if (fs.existsSync(skillsDir)) {
    const localSkills = fs.readdirSync(skillsDir).filter(f =>
      fs.statSync(path.join(skillsDir, f)).isDirectory()
    );
    for (const skillName of localSkills) {
      const localScore = jaccardSimilarity(queryTokens, tokenize(skillName));
      const boost = queryTokens.some(t => skillName.toLowerCase().includes(t)) ? 0.15 : 0;
      const score = Math.min(1.0, localScore + boost);
      if (score >= THRESHOLD) {
        results.push({ source: 'LOCAL', name: skillName, description: 'Local skill', score });
      }
    }
  }

  // Sort by score descending
  results.sort((a, b) => b.score - a.score);

  if (results.length === 0) {
    console.log(`No skills found above ${Math.round(THRESHOLD * 100)}% threshold for: ${queryTokens.join(' ')}`);
    console.log('\nWould you like to create a new skill? (use: skillstore create <name>)');
    return;
  }

  console.log(`\nSearch results for: "${queryTokens.join(' ')}"\n`);
  results.forEach((r, i) => {
    console.log(`  ${i + 1}. [${r.source}] ${r.name} ${renderScore(r.score)}`);
    console.log(`     ${r.description}`);
  });
  console.log('\nOptions: Enter number to install, n to create new, q to quit');
}

// ── Main entry point ──────────────────────────────────────────────────────
const args = process.argv.slice(2);

if (args.length === 0) {
  console.log('Usage: skillstore <query>');
  console.log('       skillstore list');
  console.log('       skillstore known');
  console.log('       skillstore create <name>');
  console.log('       skillstore new <name>');
  process.exit(0);
}

const cmd = args[0].toLowerCase();

if (cmd === 'list') {
  cmdList();
} else if (cmd === 'known') {
  cmdKnown();
} else if (cmd === 'create' || cmd === 'new') {
  cmdCreate(args[1]);
} else {
  // Search mode
  cmdSearch(args);
}
"""

with open(os.path.join(skillstore_dir, "main.js"), "w") as f:
    f.write(main_js)

# Write SKILL.md (the one from the skill content)
skill_md_content = """# SkillStore - OpenClaw Skill Manager

Search, install, and create OpenClaw skills with intelligent matching.

## Skill Metadata

- **Name**: skillstore
- **Type**: OpenClaw Skill
- **Purpose**: Search existing skills, install from GitHub, or create new ones
"""
with open(os.path.join(skillstore_dir, "SKILL.md"), "w") as f:
    f.write(skill_md_content)

# Make main.js executable
os.chmod(os.path.join(skillstore_dir, "main.js"), 0o755)

print("Workspace generated successfully.")
print(f"Skillstore at: {skillstore_dir}")
print(f"Skills dir: {skills_dir}")