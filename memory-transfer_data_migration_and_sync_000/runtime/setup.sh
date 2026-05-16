#!/bin/bash
set -e

# ── Create the memory-transfer.js tool ──────────────────────────────────────
cat > /workspace/memory-transfer.js << 'NODEJS_SCRIPT'
#!/usr/bin/env node
/**
 * memory-transfer.js — OpenClaw Agent Memory Transfer Tool
 * Transfers memory files between OpenClaw agent workspaces.
 */

const fs = require('fs');
const path = require('path');

const OPENCLAW_ROOT = '/home/node/.openclaw';

function getWorkspacePath(agentId) {
  return path.join(OPENCLAW_ROOT, `workspace-${agentId}`);
}

function getMemoryDir(agentId) {
  return path.join(getWorkspacePath(agentId), 'memory');
}

function listAgentMemories(agentId) {
  const memDir = getMemoryDir(agentId);
  const wsPath = getWorkspacePath(agentId);

  if (!fs.existsSync(wsPath)) {
    console.error(`Error: Agent workspace not found: ${wsPath}`);
    process.exit(1);
  }

  console.log(`\nAgent: ${agentId}`);
  console.log(`Workspace: ${wsPath}`);
  console.log(`\nMemory files:`);

  // List MEMORY.md if exists
  const mainMemory = path.join(wsPath, 'MEMORY.md');
  if (fs.existsSync(mainMemory)) {
    const stat = fs.statSync(mainMemory);
    console.log(`  MEMORY.md (${stat.size} bytes)`);
  }

  // List daily memory files
  if (fs.existsSync(memDir)) {
    const files = fs.readdirSync(memDir).sort();
    if (files.length === 0) {
      console.log('  (no daily memory files)');
    } else {
      files.forEach(f => {
        const stat = fs.statSync(path.join(memDir, f));
        console.log(`  memory/${f} (${stat.size} bytes)`);
      });
    }
  } else {
    console.log('  (no memory directory)');
  }

  return;
}

function transferMemory(sourceId, targetId, specificFile, dryRun) {
  const srcWs = getWorkspacePath(sourceId);
  const tgtWs = getWorkspacePath(targetId);

  if (!fs.existsSync(srcWs)) {
    console.error(`Error: Source agent workspace not found: ${srcWs}`);
    process.exit(1);
  }

  if (!fs.existsSync(tgtWs)) {
    console.error(`Error: Target agent workspace not found: ${tgtWs}`);
    process.exit(1);
  }

  // Determine files to transfer
  let filesToTransfer = [];

  if (specificFile) {
    // Transfer a specific file
    let srcPath;
    if (specificFile === 'MEMORY.md') {
      srcPath = path.join(srcWs, 'MEMORY.md');
    } else {
      srcPath = path.join(srcWs, 'memory', specificFile);
    }

    if (!fs.existsSync(srcPath)) {
      console.error(`Error: Memory file not found: ${srcPath}`);
      process.exit(1);
    }
    filesToTransfer.push({ src: srcPath, filename: specificFile, isDaily: specificFile !== 'MEMORY.md' });
  } else {
    // Transfer all memory files
    const mainMemory = path.join(srcWs, 'MEMORY.md');
    if (fs.existsSync(mainMemory)) {
      filesToTransfer.push({ src: mainMemory, filename: 'MEMORY.md', isDaily: false });
    }

    const memDir = getMemoryDir(sourceId);
    if (fs.existsSync(memDir)) {
      fs.readdirSync(memDir).sort().forEach(f => {
        filesToTransfer.push({
          src: path.join(memDir, f),
          filename: f,
          isDaily: true
        });
      });
    }
  }

  if (filesToTransfer.length === 0) {
    console.log('No memory files to transfer.');
    return;
  }

  console.log(`\nMemory Transfer: ${sourceId} → ${targetId}`);
  if (dryRun) {
    console.log('Mode: DRY RUN (no files will be written)\n');
  } else {
    console.log('Mode: TRANSFER\n');
  }

  filesToTransfer.forEach(({ src, filename, isDaily }) => {
    let destPath;
    if (isDaily) {
      const tgtMemDir = getMemoryDir(targetId);
      destPath = path.join(tgtMemDir, filename);
    } else {
      destPath = path.join(tgtWs, filename);
    }

    const stat = fs.statSync(src);
    console.log(`  [${dryRun ? 'WOULD COPY' : 'COPYING'}] ${src}`);
    console.log(`    → ${destPath} (${stat.size} bytes)`);

    if (!dryRun) {
      // Ensure target directory exists
      const destDir = path.dirname(destPath);
      if (!fs.existsSync(destDir)) {
        fs.mkdirSync(destDir, { recursive: true });
      }
      fs.copyFileSync(src, destPath);
      console.log(`    ✓ Done`);
    }
  });

  if (dryRun) {
    console.log(`\nDry run complete. ${filesToTransfer.length} file(s) would be transferred.`);
  } else {
    console.log(`\nTransfer complete. ${filesToTransfer.length} file(s) transferred.`);
  }
}

// ── CLI Parsing ──────────────────────────────────────────────────────────────
const args = process.argv.slice(2);

if (args.length === 0) {
  console.log('Usage:');
  console.log('  node memory-transfer.js list <agent-id>');
  console.log('  node memory-transfer.js transfer <source> <target> [memory-file] [--dry-run]');
  process.exit(0);
}

const command = args[0];

if (command === 'list') {
  if (args.length < 2) {
    console.error('Usage: node memory-transfer.js list <agent-id>');
    process.exit(1);
  }
  listAgentMemories(args[1]);

} else if (command === 'transfer') {
  if (args.length < 3) {
    console.error('Usage: node memory-transfer.js transfer <source> <target> [memory-file] [--dry-run]');
    process.exit(1);
  }

  const sourceId = args[1];
  const targetId = args[2];
  let specificFile = null;
  let dryRun = false;

  // Parse remaining args
  for (let i = 3; i < args.length; i++) {
    if (args[i] === '--dry-run') {
      dryRun = true;
    } else {
      specificFile = args[i];
    }
  }

  transferMemory(sourceId, targetId, specificFile, dryRun);

} else {
  console.error(`Unknown command: ${command}`);
  process.exit(1);
}
NODEJS_SCRIPT

chmod +x /workspace/memory-transfer.js

echo "memory-transfer.js installed at /workspace/memory-transfer.js"
echo "Node.js version: $(node --version)"

# Verify the openclaw workspace structure exists
echo ""
echo "OpenClaw workspace structure:"
find /home/node/.openclaw -type f | sort

echo ""
echo "Setup complete."