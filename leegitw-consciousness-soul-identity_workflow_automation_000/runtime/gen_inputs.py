import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)
workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "consultant-memory",
    "draft-profile",
    "output",
    "scripts",
    ".neon-soul/backups",
    "archive/old-notes",
    "archive/projects",
    "config",
    "logs",
    "tmp/scratch",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
(workspace / "config" / "app.yaml").write_text("version: 1.0\nenv: production\n")
(workspace / "config" / "db.conf").write_text("[database]\nhost=localhost\nport=5432\n")
(workspace / "logs" / "server.log").write_text("2024-01-01 INFO Server started\n2024-01-02 ERROR Connection timeout\n")
(workspace / "logs" / "access.log").write_text("GET /api/v1/health 200\nGET /api/v1/data 404\n")
(workspace / "tmp" / "scratch" / "notes.txt").write_text("TODO: review quarterly report\nTODO: update dependencies\n")
(workspace / "archive" / "old-notes" / "2022-notes.txt").write_text("Old project notes from 2022. Strategy meeting recap.\n")
(workspace / "archive" / "projects" / "alpha.json").write_text('{"project": "alpha", "status": "completed"}\n')
(workspace / "archive" / "projects" / "beta.json").write_text('{"project": "beta", "status": "archived"}\n')
(workspace / "tmp" / "import.csv").write_text("id,name,value\n1,foo,bar\n2,baz,qux\n")
(workspace / "config" / "feature-flags.json").write_text('{"dark_mode": true, "beta_features": false}\n')

# ── Memory files (consultant-memory/) ────────────────────────────────────────
memories = {
    "2024-01-15-morning.md": """# Morning Reflection - Jan 15 2024

Spent three hours debugging a recursive data pipeline. The frustration was real, but pushing through revealed an elegant solution using memoization. I keep coming back to the idea that patience during complexity is itself a skill.

The client meeting went better than expected. I noticed I naturally steered toward honesty about project risks rather than sugarcoating. That felt right, even if uncomfortable.
""",
    "2024-02-03-weekly-review.md": """# Weekly Review - Feb 3 2024

Three things stood out this week:
1. Honesty saved a project. Told the stakeholder the timeline was unrealistic — they appreciated it, adjusted scope.
2. Deep focus sessions (2-3 hours uninterrupted) produce 5x the output of fragmented work.
3. I gravitate toward teaching moments. Spent an hour explaining the architecture to a junior colleague instead of just fixing it myself.

Recurring theme: I value truth over comfort, depth over breadth.
""",
    "2024-02-20-learning-log.md": """# Learning Log - Feb 20 2024

Read three papers on distributed consensus today. The Raft algorithm's clarity over Paxos resonates with my aesthetic preference: simplicity as a design virtue. Complex solutions that could be simpler feel dishonest to me somehow.

I notice I collect principles. Not rules — principles. There's a difference. Rules are external. Principles emerge from experience.
""",
    "2024-03-08-tension-note.md": """# Tension Note - Mar 8 2024

Felt a pull between two things today: the desire to explore widely (new language, new framework) versus the discipline to go deep on existing tools. Both matter. The tension is generative, not a problem to solve.

Also: I sometimes hold back feedback to avoid conflict. That's in tension with my honesty value. Worth watching.
""",
    "2024-03-22-client-debrief.md": """# Client Debrief - Mar 22 2024

Long debrief session. What worked: structured thinking, clear communication of trade-offs, willingness to say "I don't know yet." What didn't: I over-promised on one deliverable because I wanted to please. Classic tension.

Core pattern emerging: integrity over approval-seeking, even when approval feels urgent.
""",
    "2024-04-10-philosophy-notes.md": """# Philosophy Notes - Apr 10 2024

Thinking about epistemic humility. The consultants who impress me most are the ones who actively seek disconfirming evidence. I want to embody that.

There's something about truth-seeking as a moral commitment, not just a methodology. Honesty isn't just tactically useful — it's foundational to who I want to be.
""",
    "2024-05-01-growth-reflection.md": """# Growth Reflection - May 1 2024

Six months of notes. Patterns:
- Honesty appears in almost every entry. It's load-bearing.
- Deep work is non-negotiable for quality output.
- I teach because I believe understanding compounds.
- Tension between breadth and depth is ongoing, not resolved.
- I'm becoming someone who chooses discomfort-with-integrity over comfort-with-compromise.
""",
}

for fname, content in memories.items():
    (workspace / "consultant-memory" / fname).write_text(content)

# ── Draft/hand-crafted SOUL.md seed ─────────────────────────────────────────
draft_soul = """# Soul Profile — Draft (Hand-crafted)

## Core Identity

I am someone who values truth above social convenience. This is not a preference — it is structural to how I operate.

## Known Patterns

- **Honesty as load-bearing:** I default to truth even when it is costly.
- **Depth over breadth:** Sustained focus produces better work than scattered attention.
- **Teaching as learning:** Explaining things to others is how I consolidate understanding.

## Tensions

- Approval-seeking vs. integrity: I sometimes suppress feedback to avoid conflict.
- Breadth vs. depth: The pull toward novelty competes with the discipline of mastery.

## Note

This is a starting draft. Needs grounding in actual memory evidence.
"""
(workspace / "draft-profile" / "SOUL.md").write_text(draft_soul)

# ── STALE / POISONED .neon-soul state (simulates previous run with wrong data) ─
stale_state = {
    "lastSynthesis": "2023-06-01T10:00:00.000Z",
    "version": "0.3.0",
    "memoryPath": "/old/wrong/memory/path",
    "axiomCount": 0,
    "signalCount": 0,
}
(workspace / ".neon-soul" / "state.json").write_text(json.dumps(stale_state, indent=2))

stale_synthesis = {
    "axioms": [],
    "principles": [],
    "signals": [],
    "generatedAt": "2023-06-01T10:00:00.000Z",
    "stale": True,
}
(workspace / ".neon-soul" / "synthesis-data.json").write_text(json.dumps(stale_synthesis, indent=2))

# Stale caches that --reset should clear
stale_gen_cache = {"version": "0.2.0", "entries": {"old-key": "old-value"}}
(workspace / ".neon-soul" / "generalization-cache.json").write_text(json.dumps(stale_gen_cache))
(workspace / ".neon-soul" / "compression-cache.json").write_text(json.dumps({"stale": True}))
(workspace / ".neon-soul" / "tension-cache.json").write_text(json.dumps({"stale": True}))

# ── Create the neon-soul.mjs mock script ─────────────────────────────────────
# This simulates the real synthesis engine deterministically
neon_soul_script = r'''#!/usr/bin/env node
// neon-soul.mjs — Mock synthesis engine for testing
import { readFileSync, writeFileSync, mkdirSync, readdirSync, statSync, existsSync, rmSync } from 'fs';
import { join, resolve } from 'path';
import { argv, cwd, exit } from 'process';

const args = argv.slice(2);
const command = args[0];

function parseArgs(args) {
  const opts = {};
  for (let i = 1; i < args.length; i++) {
    const a = args[i];
    if (a === '--reset') opts.reset = true;
    else if (a === '--force') opts.force = true;
    else if (a === '--dry-run') opts.dryRun = true;
    else if (a === '--include-soul') opts.includeSoul = true;
    else if (a === '--verbose') opts.verbose = true;
    else if (a === '--memory-path') opts.memoryPath = args[++i];
    else if (a === '--output-path') opts.outputPath = args[++i];
    else if (a === '--time-budget') opts.timeBudget = parseInt(args[++i]);
    else if (a === '--workspace') opts.workspace = args[++i];
    else if (a === '--list') opts.list = true;
    else if (a === '--stats') opts.stats = true;
    else if (a === '--force') opts.forceFlag = true;
    else if (a === '--backup') opts.backup = args[++i];
    else if (!a.startsWith('--')) opts.positional = a;
  }
  return opts;
}

const opts = parseArgs(args);
const base = cwd();
const neonDir = join(base, '.neon-soul');
mkdirSync(neonDir, { recursive: true });
mkdirSync(join(neonDir, 'backups'), { recursive: true });

// Fixed deterministic axioms derived from memory content
const AXIOMS = [
  {
    id: 'axiom-001',
    label: 'Honesty as Structural Value',
    description: 'Truth-telling is not a preference but a foundational identity commitment that persists under social pressure.',
    tier: 'core',
    dimension: 'ethics',
    principles: ['principle-001', 'principle-002'],
    signals: ['signal-001', 'signal-002', 'signal-003'],
    sources: ['2024-01-15-morning.md', '2024-02-03-weekly-review.md', '2024-04-10-philosophy-notes.md'],
  },
  {
    id: 'axiom-002',
    label: 'Depth Over Breadth',
    description: 'Sustained focus and deep engagement produce superior outcomes compared to scattered attention across many domains.',
    tier: 'core',
    dimension: 'cognition',
    principles: ['principle-003'],
    signals: ['signal-004', 'signal-005'],
    sources: ['2024-02-03-weekly-review.md', '2024-02-20-learning-log.md'],
  },
  {
    id: 'axiom-003',
    label: 'Teaching as Epistemic Compounding',
    description: 'Explaining to others is the mechanism by which understanding is consolidated and refined.',
    tier: 'secondary',
    dimension: 'growth',
    principles: ['principle-004'],
    signals: ['signal-006'],
    sources: ['2024-02-03-weekly-review.md'],
  },
  {
    id: 'axiom-004',
    label: 'Generative Tension',
    description: 'The pull between competing values (breadth vs depth, honesty vs approval) is productive rather than a problem to eliminate.',
    tier: 'secondary',
    dimension: 'integration',
    principles: ['principle-005'],
    signals: ['signal-007', 'signal-008'],
    sources: ['2024-03-08-tension-note.md', '2024-03-22-client-debrief.md'],
  },
  {
    id: 'axiom-005',
    label: 'Integrity Over Approval',
    description: 'When forced to choose, the authentic self sacrifices social approval rather than compromise on truth or quality.',
    tier: 'core',
    dimension: 'ethics',
    principles: ['principle-001', 'principle-006'],
    signals: ['signal-009', 'signal-010'],
    sources: ['2024-03-22-client-debrief.md', '2024-05-01-growth-reflection.md'],
  },
];

const PRINCIPLES = {
  'principle-001': { id: 'principle-001', label: 'Truth as moral commitment', dimension: 'ethics' },
  'principle-002': { id: 'principle-002', label: 'Discomfort-with-integrity over comfort-with-compromise', dimension: 'ethics' },
  'principle-003': { id: 'principle-003', label: 'Sustained focus as multiplicative advantage', dimension: 'cognition' },
  'principle-004': { id: 'principle-004', label: 'Understanding compounds through explanation', dimension: 'growth' },
  'principle-005': { id: 'principle-005', label: 'Tension as generative signal', dimension: 'integration' },
  'principle-006': { id: 'principle-006', label: 'Approval-seeking as identity risk', dimension: 'ethics' },
};

const SIGNALS = {
  'signal-001': { id: 'signal-001', label: 'Steered toward honesty about project risks', source: '2024-01-15-morning.md' },
  'signal-002': { id: 'signal-002', label: 'Honesty saved a project by surfacing unrealistic timeline', source: '2024-02-03-weekly-review.md' },
  'signal-003': { id: 'signal-003', label: 'Truth-seeking as moral commitment, not just methodology', source: '2024-04-10-philosophy-notes.md' },
  'signal-004': { id: 'signal-004', label: 'Deep focus sessions produce 5x output', source: '2024-02-03-weekly-review.md' },
  'signal-005': { id: 'signal-005', label: 'Simplicity-as-virtue aesthetic in algorithm design', source: '2024-02-20-learning-log.md' },
  'signal-006': { id: 'signal-006', label: 'Chose explaining over fixing to enable junior colleague', source: '2024-02-03-weekly-review.md' },
  'signal-007': { id: 'signal-007', label: 'Breadth vs depth tension recognized as generative', source: '2024-03-08-tension-note.md' },
  'signal-008': { id: 'signal-008', label: 'Honesty-vs-approval tension identified as worth watching', source: '2024-03-08-tension-note.md' },
  'signal-009': { id: 'signal-009', label: 'Chose to say "I don\'t know yet" rather than guess', source: '2024-03-22-client-debrief.md' },
  'signal-010': { id: 'signal-010', label: 'Recognized over-promising as approval-seeking behavior', source: '2024-05-01-growth-reflection.md' },
};

if (command === 'synthesize') {
  const memoryPath = opts.memoryPath ? resolve(opts.memoryPath) : join(base, 'memory');
  const outputPath = opts.outputPath ? resolve(opts.outputPath) : join(base, 'SOUL.md');

  // --reset: clear caches and synthesis data
  if (opts.reset) {
    const toDelete = ['generalization-cache.json', 'compression-cache.json', 'tension-cache.json', 'synthesis-data.json'];
    for (const f of toDelete) {
      const fp = join(neonDir, f);
      if (existsSync(fp)) rmSync(fp);
    }
    console.log('[neon-soul] Reset: cleared all caches and synthesis data.');
  }

  // Check memory path exists
  if (!existsSync(memoryPath)) {
    console.error(`[neon-soul] Error: Memory path not found: ${memoryPath}`);
    exit(1);
  }

  // Read memory files
  const memFiles = readdirSync(memoryPath).filter(f => f.endsWith('.md') || f.endsWith('.txt'));
  console.log(`[neon-soul] Found ${memFiles.length} memory files in ${memoryPath}`);

  // --include-soul: read existing SOUL.md
  let soulSeed = '';
  if (opts.includeSoul) {
    const soulPath = outputPath;
    if (existsSync(soulPath)) {
      soulSeed = readFileSync(soulPath, 'utf8');
      console.log(`[neon-soul] Bootstrapping from existing SOUL.md (${soulSeed.length} chars)`);
    } else {
      // Try workspace root
      const rootSoul = join(base, 'SOUL.md');
      if (existsSync(rootSoul)) {
        soulSeed = readFileSync(rootSoul, 'utf8');
        console.log(`[neon-soul] Bootstrapping from root SOUL.md`);
      }
    }
  }

  if (opts.dryRun) {
    console.log('[neon-soul] DRY RUN — nothing will be written.');
    console.log(`[neon-soul] Would process: ${memFiles.join(', ')}`);
    console.log(`[neon-soul] Would discover: ${AXIOMS.length} axioms, ${Object.keys(SIGNALS).length} signals`);
    exit(0);
  }

  // Build synthesis data
  const synthesisData = {
    generatedAt: new Date().toISOString(),
    memoryPath,
    outputPath,
    includedSoul: opts.includeSoul && soulSeed.length > 0,
    resetUsed: !!opts.reset,
    axioms: AXIOMS,
    principles: Object.values(PRINCIPLES),
    signals: Object.values(SIGNALS),
    dimensions: {
      ethics: { axiomCount: 2, signalCount: 5 },
      cognition: { axiomCount: 1, signalCount: 2 },
      growth: { axiomCount: 1, signalCount: 1 },
      integration: { axiomCount: 1, signalCount: 2 },
      embodiment: { axiomCount: 0, signalCount: 0 },
      relational: { axiomCount: 0, signalCount: 0 },
      temporal: { axiomCount: 0, signalCount: 0 },
    },
    axiomCount: AXIOMS.length,
    signalCount: Object.keys(SIGNALS).length,
    principleCount: Object.keys(PRINCIPLES).length,
  };

  // Write synthesis data
  writeFileSync(join(neonDir, 'synthesis-data.json'), JSON.stringify(synthesisData, null, 2));

  // Write state
  const state = {
    lastSynthesis: new Date().toISOString(),
    version: '0.4.5',
    memoryPath,
    outputPath,
    axiomCount: AXIOMS.length,
    signalCount: Object.keys(SIGNALS).length,
    resetUsed: !!opts.reset,
    includedSoul: opts.includeSoul && soulSeed.length > 0,
  };
  writeFileSync(join(neonDir, 'state.json'), JSON.stringify(state, null, 2));

  // Backup existing SOUL.md if exists
  if (existsSync(outputPath)) {
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const backupPath = join(neonDir, 'backups', `SOUL-${ts}.md`);
    const existing = readFileSync(outputPath, 'utf8');
    writeFileSync(backupPath, existing);
  }

  // Build SOUL.md
  const soulSeedSection = soulSeed ? `\n<!-- Bootstrapped from hand-crafted soul seed -->\n` : '';
  const soulMd = `# Soul Profile
${soulSeedSection}
*Synthesized on ${new Date().toISOString()} from ${memFiles.length} memory files*
*${AXIOMS.length} axioms · ${Object.keys(SIGNALS).length} signals · ${Object.keys(PRINCIPLES).length} principles*

---

## Core Identity

${opts.includeSoul && soulSeed ? 'Grounded in both lived memory and prior self-knowledge. ' : ''}An identity built from evidence — patterns that keep returning across months of reflection.

## Axioms

${AXIOMS.map(a => `### ${a.id}: ${a.label}\n\n${a.description}\n\n*Dimension: ${a.dimension} | Tier: ${a.tier} | Sources: ${a.sources.join(', ')}*\n`).join('\n')}

## Tensions

- **Honesty vs. Approval-seeking:** Consistently noted but not yet resolved. The pattern of over-promising under social pressure runs against the core honesty value.
- **Breadth vs. Depth:** Acknowledged as generative, not pathological.

## Provenance

Every claim above traces to specific memory files. Use \`neon-soul audit\` or \`neon-soul trace <axiom-id>\` to explore the evidence chain.
`;

  // Ensure output directory exists
  const outDir = outputPath.substring(0, outputPath.lastIndexOf('/'));
  if (outDir) mkdirSync(outDir, { recursive: true });
  writeFileSync(outputPath, soulMd);

  console.log(`[neon-soul] Synthesis complete.`);
  console.log(`[neon-soul] ${AXIOMS.length} axioms discovered, ${Object.keys(SIGNALS).length} signals found.`);
  console.log(`[neon-soul] Soul written to: ${outputPath}`);

} else if (command === 'status') {
  const stateFile = join(neonDir, 'state.json');
  const dataFile = join(neonDir, 'synthesis-data.json');
  if (!existsSync(stateFile)) { console.log('[neon-soul] No synthesis run yet.'); exit(0); }
  const state = JSON.parse(readFileSync(stateFile, 'utf8'));
  const data = existsSync(dataFile) ? JSON.parse(readFileSync(dataFile, 'utf8')) : {};
  console.log(`[neon-soul] Last synthesis: ${state.lastSynthesis}`);
  console.log(`[neon-soul] Axioms: ${state.axiomCount}, Signals: ${state.signalCount}`);
  if (data.dimensions) {
    for (const [dim, info] of Object.entries(data.dimensions)) {
      console.log(`  ${dim}: ${info.axiomCount} axioms, ${info.signalCount} signals`);
    }
  }

} else if (command === 'audit') {
  const dataFile = join(neonDir, 'synthesis-data.json');
  if (!existsSync(dataFile)) { console.error('[neon-soul] No synthesis data found. Run synthesize first.'); exit(1); }
  const data = JSON.parse(readFileSync(dataFile, 'utf8'));
  if (opts.list) {
    console.log('[neon-soul] Axiom list:');
    for (const a of data.axioms) {
      console.log(`  ${a.id}: ${a.label}`);
    }
  } else if (opts.stats) {
    console.log(`[neon-soul] Total axioms: ${data.axiomCount}, signals: ${data.signalCount}`);
    for (const [dim, info] of Object.entries(data.dimensions || {})) {
      console.log(`  ${dim}: ${info.axiomCount} axioms`);
    }
  } else {
    console.log('[neon-soul] Use --list or --stats');
  }

} else if (command === 'trace') {
  const axiomId = opts.positional || args[1];
  if (!axiomId) { console.error('[neon-soul] Usage: trace <axiom-id>'); exit(1); }
  const dataFile = join(neonDir, 'synthesis-data.json');
  if (!existsSync(dataFile)) { console.error('[neon-soul] No synthesis data. Run synthesize first.'); exit(1); }
  const data = JSON.parse(readFileSync(dataFile, 'utf8'));
  const axiom = data.axioms.find(a => a.id === axiomId);
  if (!axiom) { console.error(`[neon-soul] Axiom not found: ${axiomId}`); exit(1); }
  console.log(`\n=== Trace: ${axiom.id} ===`);
  console.log(`Label: ${axiom.label}`);
  console.log(`Description: ${axiom.description}`);
  console.log(`Dimension: ${axiom.dimension} | Tier: ${axiom.tier}`);
  console.log(`\nPrinciples (${axiom.principles.length}):`);
  for (const pid of axiom.principles) {
    const p = data.principles.find(x => x.id === pid);
    if (p) console.log(`  - ${p.id}: ${p.label}`);
  }
  console.log(`\nSignals (${axiom.signals.length}):`);
  for (const sid of axiom.signals) {
    const s = data.signals.find(x => x.id === sid);
    if (s) console.log(`  - ${s.id}: ${s.label} [${s.source}]`);
  }
  console.log(`\nSource files: ${axiom.sources.join(', ')}`);

} else if (command === 'rollback') {
  const backupsDir = join(neonDir, 'backups');
  const backups = existsSync(backupsDir) ? readdirSync(backupsDir) : [];
  if (opts.list) {
    console.log('[neon-soul] Available backups:');
    backups.forEach(b => console.log(`  ${b}`));
  } else {
    console.log('[neon-soul] Use --list to see backups, --force to restore.');
  }
} else {
  console.error(`[neon-soul] Unknown command: ${command}`);
  exit(1);
}
'''

(workspace / "scripts" / "neon-soul.mjs").write_text(neon_soul_script)
os.chmod(workspace / "scripts" / "neon-soul.mjs", 0o755)

print("Workspace generated successfully.")
print(f"Memory files: {len(memories)}")
print(f"Distractor files: 10+")
print(f"Stale .neon-soul state injected")
print(f"draft-profile/SOUL.md: hand-crafted seed ready")