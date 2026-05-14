import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── 1. Create fetch-docs.js (the main tool) ──────────────────────────────────
fetch_docs_js = r"""#!/usr/bin/env node
'use strict';

const https = require('https');
const http  = require('http');
const fs    = require('fs');
const path  = require('path');
const url   = require('url');

const REGISTRY_PATH = path.join(__dirname, 'docs-registry.json');
const SIZE_WARNING_BYTES = 500 * 1024;

function loadRegistry() {
  try {
    return JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
  } catch (e) {
    return {};
  }
}

function fetchUrl(rawUrl) {
  return new Promise((resolve, reject) => {
    const parsed = url.parse(rawUrl);
    const lib = parsed.protocol === 'https:' ? https : http;
    lib.get(rawUrl, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        return fetchUrl(res.headers.location).then(resolve).catch(reject);
      }
      if (res.statusCode !== 200) {
        return reject(new Error(`HTTP ${res.statusCode} for ${rawUrl}`));
      }
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

function listProjects(registry) {
  const projects = Object.keys(registry).sort();
  console.log(`\nSupported projects (${projects.length}):\n`);
  projects.forEach(p => {
    const entry = registry[p];
    console.log(`  ${p.padEnd(20)} ${entry.url || entry.local || ''}`);
  });
  console.log('');
}

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--list') || args.length === 0) {
    const registry = loadRegistry();
    listProjects(registry);
    return;
  }

  const raw  = args.includes('--raw');
  const save = args.includes('--save');
  const target = args.find(a => !a.startsWith('--'));

  if (!target) {
    console.error('Usage: node fetch-docs.js <project|URL> [--raw] [--save]');
    process.exit(1);
  }

  const registry = loadRegistry();
  let fetchedContent = null;
  let sourceLabel   = target;
  let docUrl        = null;

  // Determine the URL to fetch
  if (target.startsWith('http://') || target.startsWith('https://')) {
    docUrl = target;
  } else if (registry[target]) {
    const entry = registry[target];

    // Check for local path first
    if (entry.local && fs.existsSync(entry.local)) {
      fetchedContent = fs.readFileSync(entry.local, 'utf8');
      sourceLabel = `local:${entry.local}`;
    } else if (entry.url) {
      // Fetch priority: llms-full.txt → llms.txt → GitHub README
      const llmsFullPath = (entry.llms && entry.llms.includes('full')) ? entry.llms : '/llms-full.txt';
      const llmsPath     = '/llms.txt';

      let fetched = false;

      // Try llms-full.txt
      try {
        const fullUrl = entry.url.replace(/\/$/, '') + llmsFullPath;
        fetchedContent = await fetchUrl(fullUrl);
        sourceLabel = fullUrl;
        fetched = true;
      } catch (_) {}

      // Try llms.txt
      if (!fetched) {
        try {
          const compactUrl = entry.url.replace(/\/$/, '') + llmsPath;
          fetchedContent = await fetchUrl(compactUrl);
          sourceLabel = compactUrl;
          fetched = true;
        } catch (_) {}
      }

      // Try GitHub README fallback
      if (!fetched && entry.github) {
        try {
          const ghUrl = `https://raw.githubusercontent.com/${entry.github}/main/README.md`;
          fetchedContent = await fetchUrl(ghUrl);
          sourceLabel = ghUrl;
          fetched = true;
        } catch (_) {}
      }

      if (!fetched) {
        console.error(`Failed to fetch docs for '${target}'.`);
        process.exit(1);
      }
    }
  } else {
    // Smart discovery for unknown projects
    const patterns = [
      `https://docs.${target}.com/llms-full.txt`,
      `https://docs.${target}.com/llms.txt`,
      `https://${target}.dev/llms-full.txt`,
      `https://${target}.dev/llms.txt`,
    ];
    let fetched = false;
    for (const p of patterns) {
      try {
        fetchedContent = await fetchUrl(p);
        sourceLabel = p;
        fetched = true;
        break;
      } catch (_) {}
    }
    if (!fetched) {
      console.error(`Unknown project '${target}' and smart discovery failed.`);
      process.exit(1);
    }
  }

  // If we have a direct URL (not looked up via registry with url field)
  if (!fetchedContent && docUrl) {
    fetchedContent = await fetchUrl(docUrl);
  }

  // Size warning
  const byteSize = Buffer.byteLength(fetchedContent, 'utf8');
  if (byteSize > SIZE_WARNING_BYTES) {
    process.stderr.write(`⚠ Warning: docs exceed 500KB (${(byteSize/1024).toFixed(1)}KB)\n`);
  }

  let output = fetchedContent;
  if (!raw) {
    const header = [
      `# Docs: ${target}`,
      `# Source: ${sourceLabel}`,
      `# Size: ${(byteSize/1024).toFixed(1)}KB`,
      `# Fetched: ${new Date().toISOString()}`,
      '',
    ].join('\n');
    output = header + fetchedContent;
  }

  if (save) {
    const filename = `${target}-docs.txt`;
    fs.writeFileSync(path.join(process.cwd(), filename), output, 'utf8');
    console.log(`Saved to ${filename}`);
  } else {
    process.stdout.write(output);
  }
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
"""

with open(os.path.join(workspace, "fetch-docs.js"), "w") as f:
    f.write(fetch_docs_js)

os.chmod(os.path.join(workspace, "fetch-docs.js"), 0o755)

# ── 2. Create docs-registry.json (WITHOUT meridian) ─────────────────────────
registry = {
  "react": {
    "url": "https://react.dev",
    "llms": "/llms-full.txt",
    "github": "facebook/react"
  },
  "nextjs": {
    "url": "https://nextjs.org",
    "llms": "/llms-full.txt",
    "github": "vercel/next.js"
  },
  "vue": {
    "url": "https://vuejs.org",
    "llms": "/llms.txt",
    "github": "vuejs/core"
  },
  "svelte": {
    "url": "https://svelte.dev",
    "llms": "/llms-full.txt",
    "github": "sveltejs/svelte"
  },
  "astro": {
    "url": "https://docs.astro.build",
    "llms": "/llms-full.txt",
    "github": "withastro/astro"
  },
  "hono": {
    "url": "https://hono.dev",
    "llms": "/llms-full.txt",
    "github": "honojs/hono"
  },
  "prisma": {
    "url": "https://www.prisma.io/docs",
    "llms": "/llms-full.txt",
    "github": "prisma/prisma"
  },
  "drizzle": {
    "url": "https://orm.drizzle.team",
    "llms": "/llms-full.txt",
    "github": "drizzle-team/drizzle-orm"
  },
  "zod": {
    "url": "https://zod.dev",
    "llms": "/llms-full.txt",
    "github": "colinhacks/zod"
  },
  "tailwind": {
    "url": "https://tailwindcss.com",
    "llms": "/llms.txt",
    "github": "tailwindlabs/tailwindcss"
  },
  "typescript": {
    "url": "https://www.typescriptlang.org",
    "llms": "/llms-full.txt",
    "github": "microsoft/TypeScript"
  },
  "vite": {
    "url": "https://vitejs.dev",
    "llms": "/llms-full.txt",
    "github": "vitejs/vite"
  },
  "bun": {
    "url": "https://bun.sh/docs",
    "llms": "/llms-full.txt",
    "github": "oven-sh/bun"
  },
  "fastapi": {
    "url": "https://fastapi.tiangolo.com",
    "llms": "/llms-full.txt",
    "github": "tiangolo/fastapi"
  },
  "django": {
    "url": "https://docs.djangoproject.com",
    "llms": "/llms.txt",
    "github": "django/django"
  },
  "playwright": {
    "url": "https://playwright.dev",
    "llms": "/llms-full.txt",
    "github": "microsoft/playwright"
  }
}

with open(os.path.join(workspace, "docs-registry.json"), "w") as f:
    json.dump(registry, f, indent=2)

# ── 3. Create mock llms-full.txt content for the meridian project ────────────
mock_llms_content = """# Meridian Framework — Full LLM Documentation

## Overview
Meridian is a high-performance, reactive data-pipeline framework designed for real-time stream processing.

## Core Concepts

### Pipelines
A pipeline is a directed acyclic graph (DAG) of processing nodes.

```js
const pipeline = meridian.createPipeline({
  name: 'etl-main',
  nodes: [sourceNode, transformNode, sinkNode],
});
```

### Nodes
- **SourceNode**: Ingests raw data from queues or files.
- **TransformNode**: Applies user-defined transformations.
- **SinkNode**: Emits processed records downstream.

### Schemas
Define schemas using the Meridian Schema Definition Language (MSDL):

```
schema UserEvent {
  id:       uuid    required
  ts:       epoch   required
  payload:  json    optional
}
```

## API Reference

### `meridian.createPipeline(config)`
Returns a `Pipeline` instance.

### `pipeline.run(options)`
Starts the pipeline. Options:
- `concurrency` (int, default 4)
- `bufferSize` (int, default 1024)
- `timeout` (ms, default 30000)

### `pipeline.pause()` / `pipeline.resume()`
Pause/resume all source nodes.

## Configuration

```json
{
  "meridian": {
    "logLevel": "info",
    "metrics": { "enabled": true, "port": 9090 }
  }
}
```

## Changelog
- v2.4.0 — Added MSDL schema validation
- v2.3.1 — Fixed memory leak in TransformNode
- v2.2.0 — Introduced pipeline-level concurrency controls
"""

mock_dir = os.path.join(workspace, "mock-server-content")
os.makedirs(mock_dir, exist_ok=True)
with open(os.path.join(mock_dir, "llms-full.txt"), "w") as f:
    f.write(mock_llms_content)

# ── 4. Distractor files ───────────────────────────────────────────────────────
distractor_structure = {
    "src/pipeline/core.js":           "// Core pipeline engine\nconst MERIDIAN_VERSION = '2.4.0';\n",
    "src/pipeline/nodes/source.js":   "// SourceNode implementation\n",
    "src/pipeline/nodes/transform.js":"// TransformNode implementation\n",
    "src/pipeline/nodes/sink.js":     "// SinkNode implementation\n",
    "src/schemas/user-event.msdl":    "schema UserEvent { id: uuid required }\n",
    "src/schemas/order-event.msdl":   "schema OrderEvent { order_id: uuid required }\n",
    "src/utils/logger.js":            "const log = (msg) => console.log(`[meridian] ${msg}`);\n",
    "src/utils/metrics.js":           "// Prometheus metrics exporter\n",
    "src/index.js":                   "const { createPipeline } = require('./pipeline/core');\nmodule.exports = { createPipeline };\n",
    "tests/pipeline.test.js":         "// Unit tests for pipeline\n",
    "tests/node.test.js":             "// Unit tests for nodes\n",
    "config/default.json":            '{"meridian":{"logLevel":"warn","metrics":{"enabled":false,"port":9090}}}\n',
    "config/production.json":         '{"meridian":{"logLevel":"error","metrics":{"enabled":true,"port":9090}}}\n',
    "scripts/bench.js":               "// Benchmark script\n",
    "scripts/migrate.js":             "// Data migration helper\n",
    ".github/workflows/ci.yml":       "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
    "package.json":                   '{"name":"meridian-app","version":"1.0.0","scripts":{"test":"node tests/pipeline.test.js"}}\n',
    "CHANGELOG.md":                   "# Changelog\n## v2.4.0\n- MSDL schema validation\n",
}

for rel_path, content in distractor_structure.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Registry entries: {len(registry)} projects (meridian NOT included)")
print(f"Mock content: {os.path.join(mock_dir, 'llms-full.txt')} created")