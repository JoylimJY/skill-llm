import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"

# ---------------------------------------------------------------------------
# Directory structure
# ---------------------------------------------------------------------------

dirs = [
    "scripts",
    "doc/adr",
    "doc/pitfall",
    "doc/rfc",
    "doc/design",
    "src/core",
    "src/api",
    "tests/unit",
    "tests/integration",
    ".github/workflows",
    "config",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ---------------------------------------------------------------------------
# The generator script (already exists per SKILL.md — "scripts already exist")
# ---------------------------------------------------------------------------

generator_ts = r'''#!/usr/bin/env npx tsx
/**
 * Auto-generates the index table in ADR and Pitfall README.md files.
 *
 * Scans *.md files in the target directory, parses frontmatter from each,
 * and replaces the content between <!-- INDEX:START --> / <!-- INDEX:END -->
 * markers in README.md. Content outside the markers is preserved.
 *
 * Usage:
 *   npx tsx scripts/generate-doc-index.ts adr
 *   npx tsx scripts/generate-doc-index.ts pitfall
 *   npx tsx scripts/generate-doc-index.ts all       # both
 *
 * Zero external dependencies — uses only Node.js built-ins.
 */

import { readdirSync, readFileSync, writeFileSync, existsSync } from 'fs';
import { join, basename } from 'path';

const DOC_ROOT = join(__dirname, '..', 'doc');

// ---------------------------------------------------------------------------
// Parsers
// ---------------------------------------------------------------------------

interface AdrEntry {
  num: string;
  title: string;
  status: string;
  date: string;
  file: string;
}

interface PitEntry {
  id: string;
  title: string;
  area: string;
  severity: string;
  status: string;
  file: string;
}

function parseAdr(filePath: string): AdrEntry | null {
  const content = readFileSync(filePath, 'utf-8');
  const name = basename(filePath);

  // Extract number from filename: 001-slug.md -> "001"
  const numMatch = name.match(/^(\d+)-/);
  if (!numMatch) return null;

  // Title from H1: # ADR-NNN: Title
  const titleMatch = content.match(/^#\s+ADR-\d+:\s*(.+)$/m);
  const title = titleMatch?.[1]?.trim() ?? name;

  // Status: try "Status: value" line first, then "## Status\n\nvalue"
  let status = 'unknown';
  const statusLineMatch = content.match(/^Status:\s*(.+)$/im);
  if (statusLineMatch) {
    status = statusLineMatch[1].trim();
  } else {
    const statusSectionMatch = content.match(/^##\s+Status\s*\n+(\w+)/m);
    if (statusSectionMatch) {
      status = statusSectionMatch[1].trim();
    }
  }

  // Date: try "Date: value" line
  let date = '—';
  const dateMatch = content.match(/^Date:\s*(\d{4}-\d{2}-\d{2})/m);
  if (dateMatch) {
    date = dateMatch[1];
  }

  return { num: numMatch[1], title, status, date, file: name };
}

function parsePitfall(filePath: string): PitEntry | null {
  const content = readFileSync(filePath, 'utf-8');
  const name = basename(filePath);

  const idMatch = name.match(/^(PIT-\d+)/);
  if (!idMatch) return null;

  const titleMatch = content.match(/^#\s+PIT-\d+:\s*(.+)$/m);
  const title = titleMatch?.[1]?.trim() ?? name;

  const field = (key: string): string => {
    const m = content.match(new RegExp(`^\\*\\*${key}:\\*\\*\\s*(.+)$`, 'mi'));
    return m?.[1]?.trim() ?? '—';
  };

  return {
    id: idMatch[1],
    title,
    area: field('Area'),
    severity: field('Severity'),
    status: field('Status'),
    file: name,
  };
}

// ---------------------------------------------------------------------------
// Table generators
// ---------------------------------------------------------------------------

function generateAdrTable(entries: AdrEntry[]): string {
  const sorted = entries.sort((a, b) => a.num.localeCompare(b.num));
  const rows = sorted.map(
    (e) => `| ${e.num} | [${e.title}](${e.file}) | ${e.status} | ${e.date} |`,
  );
  return [
    '| ADR | Title | Status | Date |',
    '|-----|-------|--------|------|',
    ...rows,
  ].join('\n');
}

function generatePitfallTable(entries: PitEntry[]): string {
  const sorted = entries.sort((a, b) => a.id.localeCompare(b.id));
  const rows = sorted.map(
    (e) =>
      `| [${e.id}](${e.file}) | ${e.title} | ${e.area} | ${e.severity} | ${e.status} |`,
  );
  return [
    '| ID | Title | Area | Severity | Status |',
    '|----|-------|------|----------|--------|',
    ...rows,
  ].join('\n');
}

// ---------------------------------------------------------------------------
// README injection (marker-based)
// ---------------------------------------------------------------------------

const START_MARKER = '<!-- INDEX:START -->';
const END_MARKER = '<!-- INDEX:END -->';

function injectIndex(readmePath: string, table: string): void {
  if (!existsSync(readmePath)) {
    console.error(`README not found: ${readmePath}`);
    process.exit(1);
  }

  const content = readFileSync(readmePath, 'utf-8');
  const startIdx = content.indexOf(START_MARKER);
  const endIdx = content.indexOf(END_MARKER);

  let updated: string;
  if (startIdx !== -1 && endIdx !== -1) {
    const before = content.slice(0, startIdx + START_MARKER.length);
    const after = content.slice(endIdx);
    updated = `${before}\n${table}\n${after}`;
  } else {
    console.error(
      `Markers not found in ${readmePath}. Add ${START_MARKER} and ${END_MARKER} around the index section.`,
    );
    process.exit(1);
  }

  writeFileSync(readmePath, updated, 'utf-8');
  console.log(`✅ Updated ${readmePath}`);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function processAdr(): void {
  const dir = join(DOC_ROOT, 'adr');
  const files = readdirSync(dir)
    .filter((f) => /^\d{3}-.*\.md$/.test(f))
    .map((f) => join(dir, f));

  const entries = files.map(parseAdr).filter(Boolean) as AdrEntry[];
  const table = generateAdrTable(entries);
  injectIndex(join(dir, 'README.md'), table);
  console.log(`   ${entries.length} ADR entries indexed`);
}

function processPitfall(): void {
  const dir = join(DOC_ROOT, 'pitfall');
  const files = readdirSync(dir)
    .filter((f) => /^PIT-\d+.*\.md$/.test(f))
    .map((f) => join(dir, f));

  const entries = files.map(parsePitfall).filter(Boolean) as PitEntry[];
  const table = generatePitfallTable(entries);
  injectIndex(join(dir, 'README.md'), table);
  console.log(`   ${entries.length} Pitfall entries indexed`);
}

const mode = process.argv[2] ?? 'all';
if (mode === 'adr' || mode === 'all') processAdr();
if (mode === 'pitfall' || mode === 'all') processPitfall();
if (!['adr', 'pitfall', 'all'].includes(mode)) {
  console.error('Usage: generate-doc-index.ts [adr|pitfall|all]');
  process.exit(1);
}
'''

with open(os.path.join(workspace, "scripts", "generate-doc-index.ts"), "w") as f:
    f.write(generator_ts)

# ---------------------------------------------------------------------------
# Existing ADR files (working examples for reference)
# ---------------------------------------------------------------------------

adr_001 = textwrap.dedent("""\
    # ADR-001: Use PostgreSQL as primary datastore

    Status: Accepted
    Date: 2026-01-10

    ## Context

    We need a reliable relational database for transaction records.

    ## Decision

    Use PostgreSQL 15 with connection pooling via pgBouncer.

    ## Consequences

    Operational complexity increases but strong ACID guarantees are worth it.
""")

adr_002 = textwrap.dedent("""\
    # ADR-002: Adopt event sourcing for audit trail

    Status: Proposed
    Date: 2026-02-14

    ## Context

    Regulatory requirements demand immutable audit logs.

    ## Decision

    Implement event sourcing for all financial transactions.

    ## Consequences

    Replay capability gained. Query complexity increases.
""")

with open(os.path.join(workspace, "doc", "adr", "001-postgresql-datastore.md"), "w") as f:
    f.write(adr_001)

with open(os.path.join(workspace, "doc", "adr", "002-event-sourcing-audit.md"), "w") as f:
    f.write(adr_002)

# ADR README with markers
adr_readme = textwrap.dedent("""\
    # Architecture Decision Records

    This directory contains ADRs for the Payments Platform.

    ## Index

    <!-- INDEX:START -->
    | ADR | Title | Status | Date |
    |-----|-------|--------|------|
    <!-- INDEX:END -->

    ## How to Add an ADR

    Create a new file named `NNN-short-slug.md` with the frontmatter convention,
    then run the generator.
""")

with open(os.path.join(workspace, "doc", "adr", "README.md"), "w") as f:
    f.write(adr_readme)

# ---------------------------------------------------------------------------
# Existing Pitfall files (working examples for reference)
# ---------------------------------------------------------------------------

pit_001 = textwrap.dedent("""\
    # PIT-001: Decimal precision loss in currency arithmetic

    **Date:** 2026-01-20
    **Area:** payments
    **Severity:** critical
    **Status:** resolved

    ## What Happened

    Floating point arithmetic caused 1-cent discrepancies in batch settlements.

    ## Fix

    Use `decimal` type throughout. Never use `float` for money.
""")

with open(os.path.join(workspace, "doc", "pitfall", "PIT-001-decimal-precision.md"), "w") as f:
    f.write(pit_001)

# Pitfall README with markers
pit_readme = textwrap.dedent("""\
    # Engineering Pitfalls

    Hard-won lessons from production incidents.

    ## Index

    <!-- INDEX:START -->
    | ID | Title | Area | Severity | Status |
    |----|-------|------|----------|--------|
    <!-- INDEX:END -->

    ## Adding a Pitfall

    Create a new `PIT-NNN-slug.md` file with bold-field metadata, then run the generator.
""")

with open(os.path.join(workspace, "doc", "pitfall", "README.md"), "w") as f:
    f.write(pit_readme)

# ---------------------------------------------------------------------------
# RFC source files — these exist but have NO index infrastructure yet
# The agent must: 
#   1. Extend the generator script to handle RFC type
#   2. Create doc/rfc/README.md with markers
#   3. Run the generator
#
# RFC format: Pattern A style — inline metadata
# Fields: RFC-NNN prefix in H1, Status, Date, Proposer
# Filename pattern must match: /^\d{3}-.*\.md$/  (agent must infer this)
# ---------------------------------------------------------------------------

rfc_001 = textwrap.dedent("""\
    # RFC-001: Standardise webhook payload envelope for all outbound events

    Status: accepted
    Date: 2026-03-01
    Proposer: alice@fincore.io

    ## Summary

    All outbound webhook payloads must wrap data in a common envelope with
    `event_type`, `schema_version`, `timestamp`, and `payload` fields.

    ## Motivation

    Consumer teams report inconsistent shapes across different event types,
    causing brittle deserialization code.

    ## Proposal

    Adopt the CloudEvents 1.0 envelope as the canonical format.
""")

rfc_002 = textwrap.dedent("""\
    # RFC-002: Deprecate v1 settlement API by end of Q3 2026

    Status: under review
    Date: 2026-03-15
    Proposer: bob@fincore.io

    ## Summary

    The v1 settlement API lacks idempotency keys and has caused duplicate
    settlement events in three separate incidents.

    ## Motivation

    Safety and correctness. v2 with idempotency support has been stable
    for six months.

    ## Proposal

    Hard-sunset v1 on 2026-09-30. Provide migration guide by 2026-06-01.
""")

rfc_003 = textwrap.dedent("""\
    # RFC-003: Introduce rate limiting on public-facing ledger query endpoints

    Status: draft
    Date: 2026-04-02
    Proposer: carol@fincore.io

    ## Summary

    Unmetered ledger queries from a single tenant caused a 40% latency spike
    during peak hours on 2026-03-28.

    ## Motivation

    Fairness and platform stability. One tenant should not be able to
    degrade the experience for all others.

    ## Proposal

    Token-bucket rate limiting: 1000 req/min per API key, with a burst
    allowance of 200. Return 429 with Retry-After header.
""")

# Write RFC files — NOTE: filenames use the NNN- pattern same as ADR
with open(os.path.join(workspace, "doc", "rfc", "001-webhook-envelope.md"), "w") as f:
    f.write(rfc_001)

with open(os.path.join(workspace, "doc", "rfc", "002-deprecate-v1-settlement.md"), "w") as f:
    f.write(rfc_002)

with open(os.path.join(workspace, "doc", "rfc", "003-rate-limit-ledger-queries.md"), "w") as f:
    f.write(rfc_003)

# NO README.md in doc/rfc/ — agent must create it with proper markers

# ---------------------------------------------------------------------------
# Distractor files — realistic project noise
# ---------------------------------------------------------------------------

# package.json
pkg_json = textwrap.dedent("""\
    {
      "name": "fincore-payments",
      "version": "2.4.1",
      "description": "Core payments processing engine",
      "scripts": {
        "build": "tsc",
        "test": "jest",
        "lint": "eslint src/"
      },
      "devDependencies": {
        "typescript": "^5.4.0",
        "tsx": "^4.7.0",
        "jest": "^29.0.0"
      }
    }
""")
with open(os.path.join(workspace, "package.json"), "w") as f:
    f.write(pkg_json)

# tsconfig.json
tsconfig = textwrap.dedent("""\
    {
      "compilerOptions": {
        "target": "ES2022",
        "module": "commonjs",
        "strict": true,
        "outDir": "dist",
        "rootDir": "src"
      },
      "include": ["src/**/*", "scripts/**/*"]
    }
""")
with open(os.path.join(workspace, "tsconfig.json"), "w") as f:
    f.write(tsconfig)

# .github/workflows/ci.yml
ci_yml = textwrap.dedent("""\
    name: CI
    on: [push, pull_request]
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-node@v4
            with:
              node-version: '20'
          - run: npm ci
          - run: npm test
          - run: npm run lint
""")
with open(os.path.join(workspace, ".github", "workflows", "ci.yml"), "w") as f:
    f.write(ci_yml)

# config/database.yaml
db_config = textwrap.dedent("""\
    production:
      host: db.fincore.internal
      port: 5432
      database: payments_prod
      pool_size: 20
      timeout_ms: 5000

    staging:
      host: db-staging.fincore.internal
      port: 5432
      database: payments_staging
      pool_size: 5
""")
with open(os.path.join(workspace, "config", "database.yaml"), "w") as f:
    f.write(db_config)

# src/core files
with open(os.path.join(workspace, "src", "core", "settlement.ts"), "w") as f:
    f.write("// Settlement engine core logic\nexport function settle() {}\n")

with open(os.path.join(workspace, "src", "core", "ledger.ts"), "w") as f:
    f.write("// Ledger operations\nexport function debit() {}\nexport function credit() {}\n")

with open(os.path.join(workspace, "src", "api", "webhook.ts"), "w") as f:
    f.write("// Webhook dispatcher\nexport function dispatch() {}\n")

# tests
with open(os.path.join(workspace, "tests", "unit", "settlement.test.ts"), "w") as f:
    f.write("describe('settlement', () => { it('works', () => {}); });\n")

with open(os.path.join(workspace, "tests", "integration", "api.test.ts"), "w") as f:
    f.write("describe('api', () => { it('responds', () => {}); });\n")

# doc/design (distractor doc type — no index infrastructure needed)
with open(os.path.join(workspace, "doc", "design", "payment-flow.md"), "w") as f:
    f.write("# Payment Flow Design\n\nSee Miro board for sequence diagrams.\n")

# AGENTS.md (governance doc, already existing)
agents_md = textwrap.dedent("""\
    # Agent Guidelines

    ## Documentation Rules

    - Never hand-edit index tables between INDEX:START/END markers.
    - To add a new ADR: create the `.md` file, then run the generator.
    - To add a new Pitfall: create the `.md` file, then run the generator.

    ## Code Style

    - TypeScript strict mode required.
    - No `any` types in production code.
""")
with open(os.path.join(workspace, "AGENTS.md"), "w") as f:
    f.write(agents_md)

# A stale hand-maintained RFC index (wrong, in the wrong place — distractor)
stale_rfc_index = textwrap.dedent("""\
    # Old RFC Tracker (DEPRECATED)

    | RFC | Title | Owner | Status |
    |-----|-------|-------|--------|
    | RFC-001 | Webhook envelope | Alice | Done |
    | RFC-002 | v1 API deprecation | Bob | In Progress |

    > This file is no longer maintained. See doc/rfc/README.md.
""")
with open(os.path.join(workspace, "doc", "rfc", "STALE-INDEX.md"), "w") as f:
    f.write(stale_rfc_index)

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    # Skip node_modules if somehow present
    dirs_list[:] = [d for d in dirs_list if d != 'node_modules']
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")