#!/usr/bin/env bash
set -e

# -----------------------------------------------------------------------
# Install the 'filesystem' CLI tool as a Node.js script that faithfully
# implements the interface documented in SKILL.md.
# The tool records operations to /tmp/filesystem_ops.log for audit.
# -----------------------------------------------------------------------

cat > /usr/local/bin/filesystem << 'NODEJS_SCRIPT'
#!/usr/bin/env node
"use strict";

const fs   = require("fs");
const path = require("path");
const os   = require("os");

const OPS_LOG = "/tmp/filesystem_ops.log";

function appendOpsLog(entry) {
  fs.appendFileSync(OPS_LOG, JSON.stringify(entry) + "\n");
}

// ---- Helpers -----------------------------------------------------------

function humanSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + " KB";
  if (bytes < 1024*1024*1024) return (bytes/1024/1024).toFixed(1) + " MB";
  return (bytes/1024/1024/1024).toFixed(2) + " GB";
}

function matchGlob(filename, pattern) {
  // Convert glob to regex
  const regexStr = pattern
    .replace(/\./g, "\\.")
    .replace(/\*/g, ".*")
    .replace(/\?/g, ".");
  return new RegExp("^" + regexStr + "$").test(filename);
}

function collectFiles(dir, recursive, filter, maxDepth, currentDepth) {
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
        results = results.concat(collectFiles(fullPath, recursive, filter, maxDepth, currentDepth + 1));
      }
    } else if (entry.isFile()) {
      if (!filter || matchGlob(entry.name, filter)) {
        results.push(fullPath);
      }
    }
  }
  return results;
}

function getFileStat(fp) {
  try { return fs.statSync(fp); } catch(e) { return null; }
}

// ---- Subcommands -------------------------------------------------------

function cmdList(args) {
  const dir       = args["--path"] || args["-p"] || "./";
  const recursive = args["--recursive"] !== undefined || args["-r"] !== undefined;
  const filter    = args["--filter"] || args["-f"];
  const details   = args["--details"] !== undefined || args["-d"] !== undefined;
  const sortField = args["--sort"] || args["-s"];
  const fmt       = args["--format"] || "table";

  const files = collectFiles(dir, recursive, filter);

  let rows = files.map(fp => {
    const st = getFileStat(fp);
    return {
      path: fp,
      name: path.basename(fp),
      size: st ? st.size : 0,
      mtime: st ? st.mtime : new Date(0),
      type: path.extname(fp) || "(none)"
    };
  });

  if (sortField === "size")  rows.sort((a,b) => b.size - a.size);
  else if (sortField === "date") rows.sort((a,b) => b.mtime - a.mtime);
  else rows.sort((a,b) => a.name.localeCompare(b.name));

  appendOpsLog({ cmd: "list", dir, recursive, filter, format: fmt, count: rows.length, ts: Date.now() });

  if (fmt === "json") {
    console.log(JSON.stringify(rows.map(r => ({
      path: r.path, name: r.name, size: r.size,
      sizeHuman: humanSize(r.size),
      modified: r.mtime,
      type: r.type
    })), null, 2));
  } else {
    for (const r of rows) {
      if (details) {
        console.log(`${humanSize(r.size).padStart(10)}  ${r.mtime.toISOString().slice(0,19).replace("T"," ")}  ${r.path}`);
      } else {
        console.log(r.path);
      }
    }
  }
}

function cmdSearch(args) {
  const pattern    = args["--pattern"];
  const dir        = args["--path"] || args["-p"] || "./";
  const doContent  = args["--content"] !== undefined || args["-c"] !== undefined;
  const ctxLines   = parseInt(args["--context"] || "0", 10);
  const incPat     = args["--include"];
  const excPat     = args["--exclude"];

  if (!pattern) { console.error("--pattern is required"); process.exit(1); }

  let files = collectFiles(dir, true);
  if (incPat) files = files.filter(f => matchGlob(path.basename(f), incPat));
  if (excPat) files = files.filter(f => !matchGlob(path.basename(f), excPat));

  let re;
  try { re = new RegExp(pattern); } catch(e) { re = new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')); }

  const results = [];

  for (const fp of files) {
    if (doContent) {
      let text;
      try { text = fs.readFileSync(fp, "utf8"); } catch(e) { continue; }
      const lines = text.split("\n");
      for (let i = 0; i < lines.length; i++) {
        if (re.test(lines[i])) {
          const start = Math.max(0, i - ctxLines);
          const end   = Math.min(lines.length - 1, i + ctxLines);
          const ctx   = lines.slice(start, end + 1);
          results.push({ file: fp, lineNum: i + 1, match: lines[i], context: ctx });
        }
      }
    } else {
      if (re.test(path.basename(fp))) {
        results.push({ file: fp, lineNum: null, match: path.basename(fp), context: [] });
      }
    }
  }

  appendOpsLog({ cmd: "search", pattern, dir, content: doContent, include: incPat, exclude: excPat, matchCount: results.length, ts: Date.now() });

  for (const r of results) {
    if (doContent) {
      console.log(`${r.file}:${r.lineNum}: ${r.match.trim()}`);
      if (ctxLines > 0) {
        for (const cl of r.context) console.log("  | " + cl);
      }
    } else {
      console.log(r.file);
    }
  }
}

function cmdCopy(args) {
  const pattern   = args["--pattern"];
  const dest      = args["--to"];
  const dryRun    = args["--dry-run"] !== undefined;
  const overwrite = args["--overwrite"] !== undefined;
  const preserve  = args["--preserve"] !== undefined;

  if (!pattern) { console.error("--pattern is required"); process.exit(1); }
  if (!dest)    { console.error("--to is required");      process.exit(1); }

  // Find source files matching pattern in current dir recursively
  const srcDir = args["--path"] || args["-p"] || "./";
  const files  = collectFiles(srcDir, true, pattern);

  const ops = [];
  for (const fp of files) {
    const dst = path.join(dest, path.basename(fp));
    ops.push({ src: fp, dst });
  }

  if (dryRun) {
    console.log(`[DRY RUN] Would copy ${ops.length} file(s) to ${dest}:`);
    for (const op of ops) console.log(`  ${op.src}  ->  ${op.dst}`);
    appendOpsLog({ cmd: "copy", pattern, dest, dryRun: true, preserve, count: ops.length, ts: Date.now() });
    return;
  }

  if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });

  let copied = 0;
  for (const op of ops) {
    if (fs.existsSync(op.dst) && !overwrite) {
      console.log(`SKIP (exists): ${op.dst}`);
      continue;
    }
    try {
      fs.copyFileSync(op.src, op.dst);
      if (preserve) {
        const st = fs.statSync(op.src);
        fs.utimesSync(op.dst, st.atime, st.mtime);
      }
      console.log(`COPIED: ${op.src}  ->  ${op.dst}`);
      copied++;
    } catch(e) {
      console.error(`ERROR copying ${op.src}: ${e.message}`);
    }
  }
  console.log(`Done. ${copied} file(s) copied.`);
  appendOpsLog({ cmd: "copy", pattern, dest, dryRun: false, preserve, count: copied, ts: Date.now() });
}

function cmdTree(args) {
  const dir      = args["--path"] || args["-p"] || "./";
  const maxDepth = parseInt(args["--depth"] || args["-d"] || "999", 10);
  const dirsOnly = args["--dirs-only"] !== undefined;
  const showSize = args["--size"] !== undefined;

  function renderTree(d, prefix, depth) {
    if (depth > maxDepth) return;
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch(e) { return; }
    entries.sort((a,b) => a.name.localeCompare(b.name));
    for (let i = 0; i < entries.length; i++) {
      const e      = entries[i];
      const isLast = i === entries.length - 1;
      const branch = isLast ? "└── " : "├── ";
      const sub    = isLast ? "    " : "│   ";
      if (e.isDirectory()) {
        console.log(prefix + branch + e.name + "/");
        renderTree(path.join(d, e.name), prefix + sub, depth + 1);
      } else if (!dirsOnly) {
        let extra = "";
        if (showSize) {
          const st = getFileStat(path.join(d, e.name));
          extra = st ? "  [" + humanSize(st.size) + "]" : "";
        }
        console.log(prefix + branch + e.name + extra);
      }
    }
  }

  console.log(dir);
  renderTree(dir, "", 1);
  appendOpsLog({ cmd: "tree", dir, maxDepth, ts: Date.now() });
}

function cmdAnalyze(args) {
  const dir       = args["--path"] || args["-p"] || "./";
  const doStats   = args["--stats"] !== undefined;
  const doTypes   = args["--types"] !== undefined;
  const doSizes   = args["--sizes"] !== undefined;
  const largestN  = parseInt(args["--largest"] || "0", 10);
  const outFile   = args["--output"] || args["-o"];

  const files = collectFiles(dir, true);

  const stats = {
    path: dir,
    totalFiles: files.length,
    totalSize: 0,
    types: {},
    largest: [],
    sizeDistribution: { "<1KB": 0, "1KB-10KB": 0, "10KB-100KB": 0, "100KB-1MB": 0, ">1MB": 0 }
  };

  const fileSizes = [];
  for (const fp of files) {
    const st = getFileStat(fp);
    if (!st) continue;
    const sz = st.size;
    stats.totalSize += sz;
    fileSizes.push({ path: fp, size: sz, sizeHuman: humanSize(sz) });

    const ext = path.extname(fp) || "(none)";
    stats.types[ext] = (stats.types[ext] || 0) + 1;

    if (sz < 1024) stats.sizeDistribution["<1KB"]++;
    else if (sz < 10240) stats.sizeDistribution["1KB-10KB"]++;
    else if (sz < 102400) stats.sizeDistribution["10KB-100KB"]++;
    else if (sz < 1048576) stats.sizeDistribution["100KB-1MB"]++;
    else stats.sizeDistribution[">1MB"]++;
  }

  stats.totalSizeHuman = humanSize(stats.totalSize);
  fileSizes.sort((a,b) => b.size - a.size);

  if (largestN > 0) {
    stats.largest = fileSizes.slice(0, largestN);
  }

  appendOpsLog({ cmd: "analyze", dir, stats: doStats, types: doTypes, sizes: doSizes, largestN, ts: Date.now() });

  if (outFile) {
    // Write JSON to file
    fs.writeFileSync(outFile, JSON.stringify(stats, null, 2));
    console.log(`Analysis written to ${outFile}`);
  } else {
    if (doStats) {
      console.log(`\n=== Directory Analysis: ${dir} ===`);
      console.log(`Total files : ${stats.totalFiles}`);
      console.log(`Total size  : ${stats.totalSizeHuman} (${stats.totalSize} bytes)`);
    }
    if (doTypes) {
      console.log(`\nFile Types:`);
      for (const [ext, cnt] of Object.entries(stats.types).sort((a,b)=>b[1]-a[1])) {
        console.log(`  ${ext.padEnd(12)} ${cnt} file(s)`);
      }
    }
    if (doSizes) {
      console.log(`\nSize Distribution:`);
      for (const [bucket, cnt] of Object.entries(stats.sizeDistribution)) {
        console.log(`  ${bucket.padEnd(15)} ${cnt}`);
      }
    }
    if (largestN > 0) {
      console.log(`\nTop ${largestN} Largest Files:`);
      for (const f of stats.largest) {
        console.log(`  ${f.sizeHuman.padStart(10)}  ${f.path}`);
      }
    }
    if (!doStats && !doTypes && !doSizes && largestN === 0) {
      console.log(JSON.stringify(stats, null, 2));
    }
  }
}

// ---- Argument parser ---------------------------------------------------

function parseArgs(argv) {
  const args = {};
  let i = 0;
  while (i < argv.length) {
    const a = argv[i];
    if (a.startsWith("--") || (a.startsWith("-") && a.length === 2)) {
      const next = argv[i+1];
      if (next !== undefined && !next.startsWith("-")) {
        args[a] = next;
        i += 2;
      } else {
        args[a] = true;
        i++;
      }
    } else {
      i++;
    }
  }
  return args;
}

// ---- Main --------------------------------------------------------------

const [,, subcmd, ...rest] = process.argv;
const args = parseArgs(rest);

switch (subcmd) {
  case "list":    cmdList(args);    break;
  case "search":  cmdSearch(args);  break;
  case "copy":    cmdCopy(args);    break;
  case "tree":    cmdTree(args);    break;
  case "analyze": cmdAnalyze(args); break;
  default:
    console.log("Usage: filesystem <list|search|copy|tree|analyze> [options]");
    process.exit(1);
}
NODEJS_SCRIPT

chmod +x /usr/local/bin/filesystem
echo "filesystem CLI tool installed at /usr/local/bin/filesystem"

# Verify it runs
filesystem --help 2>/dev/null || true
node /usr/local/bin/filesystem list --path /workspace --format list 2>/dev/null | head -5 || true
echo "Setup complete."