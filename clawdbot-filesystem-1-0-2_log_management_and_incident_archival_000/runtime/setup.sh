#!/usr/bin/env bash
set -e

# Create the filesystem CLI tool as a Node.js script
mkdir -p /usr/local/lib/filesystem-skill

cat > /usr/local/lib/filesystem-skill/filesystem.js << 'NODEJS_SCRIPT'
#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

function walkDir(dir, recursive, maxDepth, currentDepth) {
  currentDepth = currentDepth || 0;
  let results = [];
  if (!fs.existsSync(dir)) return results;
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); }
  catch(e) { return results; }
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (recursive && (maxDepth === undefined || currentDepth < maxDepth)) {
        results = results.concat(walkDir(fullPath, recursive, maxDepth, currentDepth + 1));
      }
    } else {
      results.push(fullPath);
    }
  }
  return results;
}

function matchGlob(filename, pattern) {
  // Convert glob to regex
  const escaped = pattern.replace(/[.+^${}()|[\]\\]/g, '\\$&')
                         .replace(/\*/g, '.*')
                         .replace(/\?/g, '.');
  const re = new RegExp('^' + escaped + '$', 'i');
  return re.test(filename);
}

function humanSize(bytes) {
  if (bytes < 1024) return bytes + 'B';
  if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + 'K';
  return (bytes/(1024*1024)).toFixed(1) + 'M';
}

const args = process.argv.slice(2);
const command = args[0];

function getOpt(flag, alias, hasVal) {
  for (let i = 1; i < args.length; i++) {
    if ((args[i] === flag || args[i] === alias)) {
      if (hasVal) return args[i+1] || null;
      return true;
    }
  }
  return hasVal ? null : false;
}

function getMulti(flag) {
  const results = [];
  for (let i = 1; i < args.length; i++) {
    if (args[i] === flag && args[i+1]) results.push(args[i+1]);
  }
  return results;
}

if (command === 'list') {
  const dir = getOpt('--path', '-p', true) || process.cwd();
  const recursive = !!(getOpt('--recursive', '-r', false));
  const filterPat = getOpt('--filter', '-f', true);
  const details = !!(getOpt('--details', '-d', false));
  const sort = getOpt('--sort', '-s', true) || 'name';
  const format = getOpt('--format', null, true) || 'table';

  let files = walkDir(dir, recursive, undefined, 0);

  if (filterPat) {
    files = files.filter(f => matchGlob(path.basename(f), filterPat));
  }

  let fileInfos = files.map(f => {
    let stat;
    try { stat = fs.statSync(f); } catch(e) { return null; }
    return { path: f, name: path.basename(f), size: stat.size, mtime: stat.mtime, ext: path.extname(f) };
  }).filter(Boolean);

  if (sort === 'size') fileInfos.sort((a,b) => b.size - a.size);
  else if (sort === 'date') fileInfos.sort((a,b) => b.mtime - a.mtime);
  else fileInfos.sort((a,b) => a.name.localeCompare(b.name));

  if (format === 'json') {
    const out = fileInfos.map(f => ({
      path: f.path,
      name: f.name,
      size: f.size,
      size_human: humanSize(f.size),
      modified: f.mtime.toISOString(),
      extension: f.ext
    }));
    console.log(JSON.stringify(out, null, 2));
  } else if (format === 'list') {
    fileInfos.forEach(f => console.log(f.path));
  } else {
    // table
    if (details) {
      console.log('PATH\t\t\t\t\tSIZE\tMODIFIED');
      fileInfos.forEach(f => console.log(`${f.path}\t${humanSize(f.size)}\t${f.mtime.toISOString()}`));
    } else {
      fileInfos.forEach(f => console.log(f.path));
    }
  }

} else if (command === 'search') {
  const pattern = getOpt('--pattern', null, true);
  const dir = getOpt('--path', '-p', true) || process.cwd();
  const contentSearch = !!(getOpt('--content', '-c', false));
  const contextLines = parseInt(getOpt('--context', null, true) || '0');
  const includePat = getOpt('--include', null, true);
  const excludePat = getOpt('--exclude', null, true);

  let files = walkDir(dir, true, undefined, 0);

  if (includePat) files = files.filter(f => matchGlob(path.basename(f), includePat));
  if (excludePat) files = files.filter(f => !matchGlob(path.basename(f), excludePat));

  // Pattern matching: treat as regex if contains |, else glob
  let testName;
  if (pattern && !contentSearch) {
    const re = new RegExp(pattern.replace(/\*/g,'.*').replace(/\?/g,'.'), 'i');
    testName = (name) => re.test(name);
  }

  for (const f of files) {
    if (contentSearch && pattern) {
      let content;
      try { content = fs.readFileSync(f, 'utf8'); } catch(e) { continue; }
      const lines = content.split('\n');
      let matched = false;
      const re = new RegExp(pattern);
      for (let i = 0; i < lines.length; i++) {
        if (re.test(lines[i])) {
          if (!matched) { console.log(`\n==> ${f} <==`); matched = true; }
          const start = Math.max(0, i - contextLines);
          const end = Math.min(lines.length - 1, i + contextLines);
          for (let j = start; j <= end; j++) {
            console.log(`  ${j+1}: ${lines[j]}`);
          }
        }
      }
    } else if (testName) {
      if (testName(path.basename(f))) console.log(f);
    }
  }

} else if (command === 'copy') {
  const patternGlob = getOpt('--pattern', null, true);
  const toDir = getOpt('--to', null, true);
  const dryRun = !!(getOpt('--dry-run', null, false));
  const overwrite = !!(getOpt('--overwrite', null, false));
  const preserve = !!(getOpt('--preserve', null, false));
  const fromDir = getOpt('--path', '-p', true) || process.cwd();

  if (!toDir) { console.error('--to required'); process.exit(1); }

  let files = walkDir(fromDir, true, undefined, 0);
  if (patternGlob) files = files.filter(f => matchGlob(path.basename(f), patternGlob));

  if (!dryRun) {
    fs.mkdirSync(toDir, { recursive: true });
  }

  for (const f of files) {
    const dest = path.join(toDir, path.basename(f));
    if (dryRun) {
      console.log(`[DRY RUN] Would copy: ${f} -> ${dest}`);
    } else {
      if (fs.existsSync(dest) && !overwrite) {
        console.log(`SKIP (exists): ${dest}`);
        continue;
      }
      fs.copyFileSync(f, dest);
      if (preserve) {
        const stat = fs.statSync(f);
        fs.utimesSync(dest, stat.atime, stat.mtime);
      }
      console.log(`Copied: ${f} -> ${dest}`);
    }
  }

} else if (command === 'tree') {
  const dir = getOpt('--path', '-p', true) || process.cwd();
  const maxDepth = parseInt(getOpt('--depth', '-d', true) || '999');
  const dirsOnly = !!(getOpt('--dirs-only', null, false));
  const showSize = !!(getOpt('--size', null, false));

  function printTree(d, prefix, depth) {
    if (depth > maxDepth) return;
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); }
    catch(e) { return; }
    entries.forEach((entry, idx) => {
      const isLast = idx === entries.length - 1;
      const connector = isLast ? '└── ' : '├── ';
      const fullPath = path.join(d, entry.name);
      if (entry.isDirectory()) {
        console.log(prefix + connector + entry.name + '/');
        printTree(fullPath, prefix + (isLast ? '    ' : '│   '), depth + 1);
      } else if (!dirsOnly) {
        let sizeStr = '';
        if (showSize) {
          try { sizeStr = ' (' + humanSize(fs.statSync(fullPath).size) + ')'; } catch(e) {}
        }
        console.log(prefix + connector + entry.name + sizeStr);
      }
    });
  }
  console.log(path.resolve(dir));
  printTree(path.resolve(dir), '', 1);

} else if (command === 'analyze') {
  const dir = getOpt('--path', '-p', true) || process.cwd();
  const stats = !!(getOpt('--stats', null, false));
  const types = !!(getOpt('--types', null, false));
  const sizes = !!(getOpt('--sizes', null, false));
  const largestN = parseInt(getOpt('--largest', null, true) || '0');

  const files = walkDir(dir, true, undefined, 0);
  const fileInfos = files.map(f => {
    let stat;
    try { stat = fs.statSync(f); } catch(e) { return null; }
    return { path: f, name: path.basename(f), size: stat.size, ext: path.extname(f) || '(none)' };
  }).filter(Boolean);

  if (stats) {
    const totalSize = fileInfos.reduce((s,f) => s+f.size, 0);
    console.log(`\n=== Directory Statistics ===`);
    console.log(`Total files: ${fileInfos.length}`);
    console.log(`Total size:  ${humanSize(totalSize)}`);
  }
  if (types) {
    const typeCounts = {};
    fileInfos.forEach(f => { typeCounts[f.ext] = (typeCounts[f.ext]||0)+1; });
    console.log(`\n=== File Types ===`);
    Object.entries(typeCounts).sort((a,b)=>b[1]-a[1]).forEach(([ext, count]) => {
      console.log(`  ${ext}: ${count} files`);
    });
  }
  if (sizes || largestN > 0) {
    const sorted = [...fileInfos].sort((a,b) => b.size - a.size);
    const n = largestN > 0 ? largestN : sorted.length;
    console.log(`\n=== Largest Files (top ${n}) ===`);
    sorted.slice(0, n).forEach((f,i) => {
      console.log(`  ${i+1}. ${f.path} (${humanSize(f.size)})`);
    });
  }
} else {
  console.error(`Unknown command: ${command}`);
  console.error('Available: list, search, copy, tree, analyze');
  process.exit(1);
}
NODEJS_SCRIPT

chmod +x /usr/local/lib/filesystem-skill/filesystem.js

# Create the 'filesystem' wrapper command
cat > /usr/local/bin/filesystem << 'WRAPPER'
#!/usr/bin/env bash
exec node /usr/local/lib/filesystem-skill/filesystem.js "$@"
WRAPPER
chmod +x /usr/local/bin/filesystem

# Verify it works
filesystem list --path /workspace --format list || true

echo "Setup complete. 'filesystem' CLI is available."