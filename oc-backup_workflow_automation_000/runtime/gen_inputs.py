import os
import json
import random
import shutil
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

HOME = Path("/root")
OPENCLAW_WORKSPACE = HOME / ".openclaw" / "workspace"
BACKUP_DIR = HOME / "backups" / "openclaw"
SKILL_DIR = OPENCLAW_WORKSPACE / "skills" / "openclaw-backup"

# ─── 1. Create realistic OpenClaw workspace files ───────────────────────────

OPENCLAW_WORKSPACE.mkdir(parents=True, exist_ok=True)

# openclaw.json
openclaw_cfg = {
    "version": "2.3.1",
    "agent_name": "ClawBot",
    "model": "gpt-4o",
    "max_tokens": 4096,
    "temperature": 0.7,
    "plugins": ["web-search", "code-runner", "openclaw-backup"],
    "log_level": "info",
    "workspace": str(OPENCLAW_WORKSPACE)
}
(OPENCLAW_WORKSPACE / "openclaw.json").write_text(json.dumps(openclaw_cfg, indent=2))

# .env
env_content = """OPENAI_API_KEY=sk-fake-key-for-testing-do-not-use
OPENCLAW_SECRET=supersecret123
DATABASE_URL=postgres://user:pass@localhost:5432/openclaw
REDIS_URL=redis://localhost:6379
"""
(OPENCLAW_WORKSPACE / ".env").write_text(env_content)

# exec-approvals.json
approvals = {
    "approved_commands": ["ls", "cat", "grep", "node", "python3"],
    "denied_commands": ["rm -rf /", "mkfs"],
    "last_updated": "2024-06-01T10:00:00Z"
}
(OPENCLAW_WORKSPACE / "exec-approvals.json").write_text(json.dumps(approvals, indent=2))

# AGENTS.md
(OPENCLAW_WORKSPACE / "AGENTS.md").write_text("""# Agents Configuration
## ClawBot
- Role: General Assistant
- Capabilities: web search, code execution, file management
- Safety Level: High
""")

# SOUL.md
(OPENCLAW_WORKSPACE / "SOUL.md").write_text("""# Soul Definition
You are ClawBot, a helpful AI assistant focused on developer productivity.
Always prioritize safety and accuracy.
""")

# USER.md
(OPENCLAW_WORKSPACE / "USER.md").write_text("""# User Profile
- Name: Frank
- Timezone: Asia/Shanghai
- Preferences: concise responses, code examples, Chinese when informal
""")

# IDENTITY.md
(OPENCLAW_WORKSPACE / "IDENTITY.md").write_text("""# Identity
Version: 1.0
Created: 2024-01-15
""")

# TOOLS.md
(OPENCLAW_WORKSPACE / "TOOLS.md").write_text("""# Available Tools
- web_search: Search the internet
- code_runner: Execute code snippets
- file_manager: Read/write files
""")

# HEARTBEAT.md
(OPENCLAW_WORKSPACE / "HEARTBEAT.md").write_text("""# Heartbeat
Last beat: 2024-06-15T08:00:00Z
Status: healthy
""")

# MEMORY.md
(OPENCLAW_WORKSPACE / "MEMORY.md").write_text("""# Memory
## Recent Interactions
- 2024-06-14: Helped user debug Python script
- 2024-06-13: Generated report on Q2 metrics
""")

# ─── 2. Create skills directory with some custom skills ──────────────────────

skills_dir = OPENCLAW_WORKSPACE / "skills"
skills_dir.mkdir(exist_ok=True)

for skill_name in ["web-search", "code-runner", "file-manager"]:
    skill_path = skills_dir / skill_name
    skill_path.mkdir(exist_ok=True)
    (skill_path / "package.json").write_text(json.dumps({
        "name": skill_name,
        "version": "1.0.0",
        "main": "index.js"
    }, indent=2))
    (skill_path / "index.js").write_text(f"// {skill_name} skill\nmodule.exports = {{}};")
    (skill_path / "README.md").write_text(f"# {skill_name}\nA custom skill.")

# ─── 3. Create cron, devices, memory directories ─────────────────────────────

cron_dir = OPENCLAW_WORKSPACE / "cron"
cron_dir.mkdir(exist_ok=True)
(cron_dir / "tasks.json").write_text(json.dumps([
    {"id": "daily-backup", "schedule": "0 2 * * *", "command": "backup"},
    {"id": "health-check", "schedule": "*/5 * * * *", "command": "heartbeat"}
], indent=2))

devices_dir = OPENCLAW_WORKSPACE / "devices"
devices_dir.mkdir(exist_ok=True)
(devices_dir / "devices.json").write_text(json.dumps([
    {"id": "laptop-main", "type": "workstation", "os": "macOS"},
    {"id": "server-01", "type": "server", "os": "Ubuntu 22.04"}
], indent=2))

memory_dir = OPENCLAW_WORKSPACE / "memory"
memory_dir.mkdir(exist_ok=True)
(memory_dir / "short_term.json").write_text(json.dumps({"entries": []}, indent=2))
(memory_dir / "long_term.json").write_text(json.dumps({"entries": [
    {"date": "2024-06-01", "summary": "User prefers dark mode"}
]}, indent=2))

# ─── 4. Create distractor files (noise in workspace) ─────────────────────────

distractor_dir = OPENCLAW_WORKSPACE / "logs"
distractor_dir.mkdir(exist_ok=True)
for i in range(5):
    (distractor_dir / f"app_{i}.log").write_text(f"[INFO] Log entry {i}\n" * random.randint(10, 50))

cache_dir = OPENCLAW_WORKSPACE / ".cache"
cache_dir.mkdir(exist_ok=True)
(cache_dir / "embeddings.bin").write_bytes(bytes(random.randint(0, 255) for _ in range(256)))
(cache_dir / "model_cache.json").write_text(json.dumps({"cached_at": "2024-06-10", "model": "gpt-4o"}))

tmp_dir = OPENCLAW_WORKSPACE / "tmp"
tmp_dir.mkdir(exist_ok=True)
for i in range(3):
    (tmp_dir / f"session_{i}.tmp").write_text(f"temp session data {i}")

# ─── 5. Create OLD backup files (>7 days old) that should be cleaned ─────────

BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Helper to create fake old backup files with old mtime
def create_old_backup(days_old: int, backup_type: str):
    old_dt = datetime.now() - timedelta(days=days_old)
    ts = old_dt.strftime("%Y%m%d-%H%M%S")
    tar_name = f"openclaw-backup-{backup_type}-{ts}.tar.gz"
    json_name = f"openclaw-backup-{backup_type}-{ts}.json"
    
    tar_path = BACKUP_DIR / tar_name
    json_path = BACKUP_DIR / json_name
    
    # Create minimal tar.gz
    import tarfile, io
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tf:
        data = f"fake backup content for {backup_type}".encode()
        ti = tarfile.TarInfo(name="dummy.txt")
        ti.size = len(data)
        tf.addfile(ti, io.BytesIO(data))
    tar_path.write_bytes(buf.getvalue())
    
    # Create json manifest
    manifest = {
        "version": "1.1.0",
        "type": backup_type,
        "timestamp": old_dt.isoformat(),
        "files": [{"path": "dummy.txt", "status": "backed_up"}]
    }
    json_path.write_text(json.dumps(manifest, indent=2))
    
    # Set mtime to simulate old file
    old_epoch = old_dt.timestamp()
    os.utime(tar_path, (old_epoch, old_epoch))
    os.utime(json_path, (old_epoch, old_epoch))
    print(f"Created old backup: {tar_name} ({days_old} days old)")

# Create backups that are definitely older than 7 days
create_old_backup(10, "full")
create_old_backup(14, "full")
create_old_backup(21, "system")
create_old_backup(8, "system-workspace")

print("\n✅ Workspace generation complete.")
print(f"   OpenClaw workspace: {OPENCLAW_WORKSPACE}")
print(f"   Backup output dir:  {BACKUP_DIR}")
print(f"   Old backups created: 4 files (all >7 days old, should be cleaned by --retain 7)")

# ─── 6. Write the backup.js script ───────────────────────────────────────────

backup_js = r"""#!/usr/bin/env node
'use strict';

const { program } = require('commander');
const fs = require('fs-extra');
const path = require('path');
const tar = require('tar');
const dayjs = require('dayjs');
const os = require('os');

program
  .option('-f, --full', 'Full backup (default)')
  .option('-s, --system', 'Backup system configs only')
  .option('-w, --workspace', 'Backup workspace core files only')
  .option('-k, --skills', 'Backup skills directory only')
  .option('-m, --memory', 'Backup memory data only')
  .option('-c, --cron', 'Backup cron configs only')
  .option('-d, --devices', 'Backup device configs only')
  .option('-o, --output <path>', 'Output directory', path.join(os.homedir(), 'backups', 'openclaw'))
  .option('--dry-run', 'Preview mode, do not actually backup')
  .option('--retain <days>', 'Retain backups for N days, delete older ones', parseInt)
  .option('--clean', 'Clean mode: only delete old backups, no new backup')
  .option('-j, --json', 'Output results as JSON')
  .parse(process.argv);

const opts = program.opts();
const OPENCLAW_HOME = path.join(os.homedir(), '.openclaw', 'workspace');

// Determine which categories to back up
function getCategories() {
  const cats = [];
  if (opts.system) cats.push('system');
  if (opts.workspace) cats.push('workspace');
  if (opts.skills) cats.push('skills');
  if (opts.memory) cats.push('memory');
  if (opts.cron) cats.push('cron');
  if (opts.devices) cats.push('devices');
  if (cats.length === 0 || opts.full) return ['full'];
  return cats;
}

function getFilesForCategory(cat) {
  const base = OPENCLAW_HOME;
  const map = {
    system: [
      path.join(base, 'openclaw.json'),
      path.join(base, '.env'),
      path.join(base, 'exec-approvals.json'),
    ],
    workspace: [
      path.join(base, 'AGENTS.md'),
      path.join(base, 'SOUL.md'),
      path.join(base, 'USER.md'),
      path.join(base, 'IDENTITY.md'),
      path.join(base, 'TOOLS.md'),
      path.join(base, 'HEARTBEAT.md'),
      path.join(base, 'MEMORY.md'),
    ],
    skills: [path.join(base, 'skills')],
    memory: [path.join(base, 'memory')],
    cron: [path.join(base, 'cron')],
    devices: [path.join(base, 'devices')],
  };
  if (cat === 'full') {
    return Object.values(map).flat();
  }
  return map[cat] || [];
}

function buildTypeString(cats) {
  if (cats.length === 1) return cats[0];
  return cats.join('-');
}

async function cleanOldBackups(outputDir, retainDays, dryRun) {
  const cutoff = Date.now() - retainDays * 24 * 60 * 60 * 1000;
  let files;
  try {
    files = await fs.readdir(outputDir);
  } catch (e) {
    return [];
  }
  const deleted = [];
  for (const f of files) {
    if (!f.startsWith('openclaw-backup-')) continue;
    const fp = path.join(outputDir, f);
    const stat = await fs.stat(fp);
    if (stat.mtimeMs < cutoff) {
      deleted.push(f);
      if (!dryRun) await fs.remove(fp);
    }
  }
  return deleted;
}

async function main() {
  const outputDir = path.resolve(opts.output);
  const dryRun = opts.dryRun || false;

  // Clean mode: only delete, no backup
  if (opts.clean) {
    if (opts.retain == null) {
      console.error('--clean requires --retain <days>');
      process.exit(1);
    }
    const deleted = await cleanOldBackups(outputDir, opts.retain, dryRun);
    const result = { mode: 'clean', dryRun, deleted, count: deleted.length };
    if (opts.json) {
      console.log(JSON.stringify(result, null, 2));
    } else {
      console.log(`[openclaw-backup] Clean mode: ${deleted.length} old backup(s) ${dryRun ? 'would be' : ''} deleted.`);
      deleted.forEach(f => console.log('  - ' + f));
    }
    return;
  }

  const cats = getCategories();
  const typeStr = buildTypeString(cats);
  const now = dayjs();
  const dateStr = now.format('YYYYMMDD');
  const timeStr = now.format('HHmmss');
  const baseName = `openclaw-backup-${typeStr}-${dateStr}-${timeStr}`;
  const tarFile = path.join(outputDir, baseName + '.tar.gz');
  const jsonFile = path.join(outputDir, baseName + '.json');

  // Collect all files
  const allFiles = [];
  const manifestEntries = [];

  for (const cat of cats) {
    const filePaths = getFilesForCategory(cat);
    for (const fp of filePaths) {
      const exists = await fs.pathExists(fp);
      const relative = path.relative(os.homedir(), fp);
      const isSensitive = fp.endsWith('.env');
      if (exists) {
        allFiles.push(fp);
        manifestEntries.push({ path: fp, relative, category: cat, status: 'backed_up', sensitive: isSensitive });
      } else {
        manifestEntries.push({ path: fp, relative, category: cat, status: 'skipped', sensitive: false });
      }
    }
  }

  if (dryRun) {
    const result = {
      mode: 'dry-run',
      type: typeStr,
      categories: cats,
      outputDir,
      tarFile,
      jsonFile,
      files: manifestEntries
    };
    if (opts.json) {
      console.log(JSON.stringify(result, null, 2));
    } else {
      console.log('[openclaw-backup] Dry-run mode. Files that would be backed up:');
      manifestEntries.forEach(e => console.log(`  [${e.status}] ${e.path}`));
    }
    return;
  }

  // Create output dir
  await fs.ensureDir(outputDir);

  // Create tar.gz
  const filesToPack = allFiles.map(f => ({ src: f, dest: path.relative(os.homedir(), f) }));
  
  if (filesToPack.length > 0) {
    // We build a temporary staging dir
    const stagingDir = path.join(outputDir, '.staging-' + timeStr);
    await fs.ensureDir(stagingDir);
    for (const { src, dest } of filesToPack) {
      const target = path.join(stagingDir, dest);
      await fs.ensureDir(path.dirname(target));
      await fs.copy(src, target, { preserveTimestamps: true });
    }
    await tar.c(
      { gzip: true, file: tarFile, cwd: stagingDir },
      ['.']
    );
    await fs.remove(stagingDir);
  } else {
    await tar.c({ gzip: true, file: tarFile }, []);
  }

  // Write manifest JSON
  const manifest = {
    version: '1.1.0',
    type: typeStr,
    categories: cats,
    timestamp: now.toISOString(),
    outputDir,
    tarFile,
    jsonFile,
    fileCount: manifestEntries.filter(e => e.status === 'backed_up').length,
    files: manifestEntries
  };
  await fs.writeJson(jsonFile, manifest, { spaces: 2 });

  // Write RECOVERY_GUIDE.md
  const recoveryGuide = path.join(outputDir, 'RECOVERY_GUIDE.md');
  await fs.writeFile(recoveryGuide, `# Recovery Guide\nBackup: ${baseName}\nDate: ${now.toISOString()}\n\nTo restore:\n1. Extract ${tarFile}\n2. Copy files back to their original locations\n`);

  // Handle retain
  let deletedOld = [];
  if (opts.retain != null) {
    deletedOld = await cleanOldBackups(outputDir, opts.retain, false);
  }

  const result = {
    mode: 'backup',
    type: typeStr,
    categories: cats,
    tarFile,
    jsonFile,
    fileCount: manifest.fileCount,
    retainDays: opts.retain || null,
    deletedOld,
    files: manifestEntries
  };

  if (opts.json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(`[openclaw-backup] Backup complete: ${tarFile}`);
    console.log(`[openclaw-backup] Manifest: ${jsonFile}`);
    console.log(`[openclaw-backup] Files backed up: ${manifest.fileCount}`);
    if (deletedOld.length > 0) {
      console.log(`[openclaw-backup] Deleted ${deletedOld.length} old backup(s).`);
    }
  }
}

main().catch(e => { console.error(e); process.exit(1); });
"""

script_path = SKILL_DIR / "scripts" / "backup.js"
script_path.parent.mkdir(parents=True, exist_ok=True)
script_path.write_text(backup_js)
print(f"\n✅ backup.js written to {script_path}")

# Write references
(SKILL_DIR / "references" / "FILE_LIST.md").write_text("# File List\nSee SKILL.md for details.")
(SKILL_DIR / "references" / "RECOVERY_GUIDE_TEMPLATE.md").write_text("# Recovery Guide Template\n")
(SKILL_DIR / "config" / "config.example.json").write_text(json.dumps({"example": True}, indent=2))