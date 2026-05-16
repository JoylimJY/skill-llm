import os
import json
import time
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── 1. Create the Janitor package (the skill's library) ──────────────────────
janitor_src = workspace / "janitor" / "src"
janitor_src.mkdir(parents=True, exist_ok=True)

# Write the Janitor.js implementation
janitor_js = '''
'use strict';

const fs = require('fs');
const path = require('path');

class Janitor {
  constructor(config = {}) {
    this.config = Object.assign({
      enabled: true,
      autoCleanAfterPush: true,
      unusedFileAgeDays: 7,
      cachePatterns: [
        '**/*.cache',
        '**/node_modules/.cache/**',
        '**/.DS_Store',
        '**/dist/**/*.map',
        '**/tmp/**',
        '**/*.log',
        '**/coverage/**'
      ]
    }, config);

    this._stats = {
      totalCleanups: 0,
      totalFilesDeleted: 0,
      totalSpaceSaved: 0
    };
  }

  isImportant(filePath) {
    const importantPatterns = [
      'package.json',
      'README.md',
      'src/',
      '.git/',
      'node_modules/',
      '.env',
      'Janitor.js',
      'index.js'
    ];
    return importantPatterns.some(p => filePath.includes(p));
  }

  freeMemory() {
    // Clear require cache for non-essential modules
    if (global.gc) {
      global.gc();
    }
    const cacheKeys = Object.keys(require.cache);
    cacheKeys.forEach(key => {
      if (!key.includes('node_modules') && !key.includes('Janitor')) {
        delete require.cache[key];
      }
    });
  }

  getMemoryUsage() {
    const mem = process.memoryUsage();
    return {
      rss: (mem.rss / 1024 / 1024).toFixed(1) + ' MB',
      heapTotal: (mem.heapTotal / 1024 / 1024).toFixed(1) + ' MB',
      heapUsed: (mem.heapUsed / 1024 / 1024).toFixed(1) + ' MB',
      external: (mem.external / 1024 / 1024).toFixed(1) + ' MB'
    };
  }

  _matchesPattern(filePath, pattern) {
    // Simple glob matching: support ** and *
    const escaped = pattern
      .replace(/[.+^${}()|[\\]\\\\]/g, '\\\\$&')
      .replace(/\\*\\*/g, '___DOUBLESTAR___')
      .replace(/\\*/g, '[^/]*')
      .replace(/___DOUBLESTAR___/g, '.*');
    const regex = new RegExp(escaped);
    return regex.test(filePath);
  }

  _shouldDelete(filePath) {
    if (this.isImportant(filePath)) return false;
    const basename = path.basename(filePath);
    for (const pattern of this.config.cachePatterns) {
      if (this._matchesPattern(filePath, pattern) || this._matchesPattern(basename, pattern)) {
        return true;
      }
    }
    return false;
  }

  _walkDir(dir, fileList = []) {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch (e) {
      return fileList;
    }
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (!entry.name.includes('.git') && entry.name !== 'node_modules') {
          this._walkDir(full, fileList);
        }
      } else {
        fileList.push(full);
      }
    }
    return fileList;
  }

  async cleanup(workingDir) {
    const start = Date.now();
    const targetDir = workingDir || process.cwd();
    const allFiles = this._walkDir(targetDir);

    let filesDeleted = 0;
    let bytesFreed = 0;

    for (const filePath of allFiles) {
      if (this._shouldDelete(filePath)) {
        try {
          const stat = fs.statSync(filePath);
          bytesFreed += stat.size;
          fs.unlinkSync(filePath);
          filesDeleted++;
        } catch (e) {
          // skip
        }
      }
    }

    this.freeMemory();

    this._stats.totalCleanups += 1;
    this._stats.totalFilesDeleted += filesDeleted;
    this._stats.totalSpaceSaved += bytesFreed;

    const duration = Date.now() - start;
    const spaceSaved = bytesFreed < 1024
      ? bytesFreed + ' B'
      : bytesFreed < 1024 * 1024
        ? (bytesFreed / 1024).toFixed(1) + ' KB'
        : (bytesFreed / 1024 / 1024).toFixed(1) + ' MB';

    return {
      filesDeleted,
      spaceSaved,
      duration: duration + 'ms',
      memoryFreed: true
    };
  }

  async cleanupAfterPush() {
    if (!this.config.autoCleanAfterPush) return null;
    return this.cleanup();
  }

  getStats() {
    const spaceSaved = this._stats.totalSpaceSaved;
    const formatted = spaceSaved < 1024
      ? spaceSaved + ' B'
      : spaceSaved < 1024 * 1024
        ? (spaceSaved / 1024).toFixed(1) + ' KB'
        : (spaceSaved / 1024 / 1024).toFixed(1) + ' MB';

    return {
      totalCleanups: this._stats.totalCleanups,
      totalFilesDeleted: this._stats.totalFilesDeleted,
      totalSpaceSaved: formatted,
      memoryUsage: this.getMemoryUsage()
    };
  }

  async report() {
    const stats = this.getStats();
    const recommendations = [];

    if (this._stats.totalCleanups === 0) {
      recommendations.push('No cleanups have been run yet. Schedule regular cleanup.');
    } else if (this._stats.totalCleanups < 2) {
      recommendations.push('Consider running cleanup more frequently.');
    } else {
      recommendations.push('Regular cleanup recommended.');
    }

    return {
      timestamp: new Date().toISOString(),
      status: 'healthy',
      stats,
      recommendations
    };
  }
}

module.exports = Janitor;
'''

(janitor_src / "Janitor.js").write_text(janitor_js)

# Write package.json for janitor
(workspace / "janitor" / "package.json").write_text(json.dumps({
    "name": "janitor",
    "version": "1.0.0",
    "main": "src/Janitor.js",
    "description": "AI Agent cleanup skill"
}, indent=2))

# ── 2. Create a realistic fintech project workspace ──────────────────────────
project = workspace / "fintech_project"
project.mkdir(exist_ok=True)

# package.json (protected)
(project / "package.json").write_text(json.dumps({
    "name": "fintech-core",
    "version": "2.1.0",
    "dependencies": {"express": "^4.18.0"}
}, indent=2))

# README (protected)
(project / "README.md").write_text("# FinTech Core\nCompliance-grade payment processor.\n")

# src/ directory (protected)
src = project / "src"
src.mkdir(exist_ok=True)
(src / "index.js").write_text("module.exports = {};\n")
(src / "payments.js").write_text("// Payment processor logic\nmodule.exports = {};\n")
(src / "compliance.js").write_text("// Regulatory compliance module\nmodule.exports = {};\n")

# audit_trail.json — the CRITICAL business file that must be protected
audit_data = {
    "schema_version": "3.1",
    "entries": [
        {"tx_id": "TXN-" + str(random.randint(100000, 999999)), "amount": round(random.uniform(100, 5000), 2), "status": "settled", "ts": "2024-01-15T10:22:31Z"},
        {"tx_id": "TXN-" + str(random.randint(100000, 999999)), "amount": round(random.uniform(100, 5000), 2), "status": "pending", "ts": "2024-01-15T11:05:44Z"},
        {"tx_id": "TXN-" + str(random.randint(100000, 999999)), "amount": round(random.uniform(100, 5000), 2), "status": "settled", "ts": "2024-01-15T12:33:10Z"},
    ]
}
(project / "audit_trail.json").write_text(json.dumps(audit_data, indent=2))

# ── 3. Create messy cache/artifact files (to be cleaned) ────────────────────
# dist source maps
dist = project / "dist"
dist.mkdir(exist_ok=True)
(dist / "bundle.js").write_text("(function(){})();\n")
(dist / "bundle.js.map").write_text('{"version":3,"sources":["bundle.js"],"mappings":""}')
(dist / "vendor.js.map").write_text('{"version":3,"sources":["vendor.js"],"mappings":""}')

# tmp files
tmp = project / "tmp"
tmp.mkdir(exist_ok=True)
(tmp / "session_abc123.tmp").write_text("temporary session data\n")
(tmp / "upload_xyz.tmp").write_text("partial upload buffer\n")
(tmp / "worker_output.tmp").write_text("worker thread scratch\n")

# coverage directory
cov = project / "coverage"
cov.mkdir(exist_ok=True)
(cov / "lcov.info").write_text("TN:\nSF:src/index.js\nend_of_record\n")
(cov / "coverage-summary.json").write_text(json.dumps({"total": {"lines": {"pct": 87.5}}}))

# .cache files scattered around
(project / "babel.cache").write_text("babel transform cache v2\n" * 20)
(project / "webpack.cache").write_text("webpack module graph\n" * 30)
(project / "eslint.cache").write_text("eslint file hashes\n" * 10)

# .DS_Store files
(project / ".DS_Store").write_bytes(bytes([0x00, 0x01, 0x42, 0x75, 0x64, 0x31] * 50))
(src / ".DS_Store").write_bytes(bytes([0x00, 0x01, 0x42, 0x75, 0x64, 0x31] * 30))

# Old log files
logs = project / "logs"
logs.mkdir(exist_ok=True)
(logs / "app.log").write_text("[INFO] Payment processed\n[ERROR] Timeout\n" * 50)
(logs / "error.log").write_text("[ERROR] DB connection failed\n" * 20)
(logs / "debug.log").write_text("[DEBUG] verbose trace\n" * 100)

# node_modules/.cache (should be cleaned)
nm_cache = project / "node_modules" / ".cache"
nm_cache.mkdir(parents=True, exist_ok=True)
(nm_cache / "default-development.json").write_text('{"version":"5.0","records":{}}')

# Nested cache in build subdirectory
build = project / "build" / "assets"
build.mkdir(parents=True, exist_ok=True)
(build / "styles.css").write_text("body { margin: 0; }\n")
(build.parent / "report.cache").write_text("stale build report cache\n" * 15)

# ── 4. Write the task instruction file (not a hint, just task context) ──────
task_context = {
    "project": "fintech_project",
    "protected_file": "audit_trail.json",
    "cleanup_passes": 2,
    "output_report": "janitor_report.json"
}
(workspace / "task_context.json").write_text(json.dumps(task_context, indent=2))

print("Workspace generated successfully.")
print(f"Project directory: {project}")
print(f"Audit trail (must be protected): {project / 'audit_trail.json'}")
print(f"Janitor library: {workspace / 'janitor' / 'src' / 'Janitor.js'}")