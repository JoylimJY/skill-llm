import os
import json
import random
import string

random.seed(42)

workspace = "/workspace"

# ── Directory structure (distractors) ─────────────────────────────────────────
dirs = [
    "skills/hle-benchmark-evolver",
    "skills/capability-evolver/assets/gep",
    "skills/capability-evolver/src",
    "skills/capability-evolver/data/checkpoints",
    "data/raw_evals",
    "data/processed",
    "logs/runs",
    "configs",
    "reports/archive",
    "tmp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractor_files = {
    "configs/evolver_config.yaml": "model: gpt-4\nmax_cycles: 10\ntarget_accuracy: 0.60\n",
    "configs/curriculum_params.json": json.dumps({"easy_first": True, "batch_size": 16}),
    "data/raw_evals/old_report_2023.json": json.dumps({"questions": [], "meta": {"version": "0.1"}}),
    "data/processed/aggregated_scores.csv": "subject,score\nmath,0.45\nscience,0.52\nhistory,0.38\n",
    "logs/runs/run_001.log": "2024-01-01 INFO starting evolution cycle\n2024-01-01 INFO cycle complete\n",
    "logs/runs/run_002.log": "2024-01-02 INFO benchmark ingested\n",
    "reports/archive/snapshot_old.json": json.dumps({"benchmark_id": "cais/hle", "accuracy": 0.31}),
    "tmp/scratch/notes.txt": "TODO: check question modality filtering\n",
    "skills/capability-evolver/src/evolve.js": "// placeholder evolve module\nmodule.exports = {};\n",
    "skills/capability-evolver/data/checkpoints/ckpt_0001.bin": "FAKE_BINARY_DATA_0001",
    "skills/capability-evolver/data/checkpoints/ckpt_0002.bin": "FAKE_BINARY_DATA_0002",
}
for path, content in distractor_files.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# ── HLE report template (what the skill defaults to) ─────────────────────────
subjects = ["mathematics", "physics", "chemistry", "biology", "history", "literature", "computer_science", "economics"]
modalities = ["text", "image", "table", "code"]

def make_question(qid, correct_prob=0.5):
    return {
        "question_id": f"hle_{qid:04d}",
        "subject": random.choice(subjects),
        "modality": random.choice(modalities),
        "difficulty": random.choice(["easy", "medium", "hard"]),
        "correct": random.random() < correct_prob,
        "model_answer": "".join(random.choices(string.ascii_lowercase, k=8)),
        "gold_answer": "".join(random.choices(string.ascii_lowercase, k=8)),
    }

template_questions = [make_question(i, correct_prob=0.42) for i in range(1, 201)]
template_report = {
    "benchmark_id": "cais/hle",
    "version": "1.0",
    "timestamp": "2024-06-01T00:00:00Z",
    "total_questions": len(template_questions),
    "questions": template_questions,
    "metadata": {
        "model": "openclaw-v1",
        "eval_batch": "batch_001",
    }
}
template_path = os.path.join(workspace, "skills/capability-evolver/assets/gep/hle_report.template.json")
with open(template_path, "w") as f:
    json.dump(template_report, f, indent=2)

# ── A "raw" HLE report the agent will use as their actual input ───────────────
# This is messier: mixed correctness, some fields that may trip up naive parsers
raw_questions = [make_question(i, correct_prob=0.55) for i in range(1, 151)]
# Inject some edge-case questions
raw_questions.append({
    "question_id": "hle_9901",
    "subject": "mathematics",
    "modality": "text",
    "difficulty": "easy",
    "correct": True,
    "model_answer": "42",
    "gold_answer": "42",
})
raw_questions.append({
    "question_id": "hle_9902",
    "subject": "computer_science",
    "modality": "code",
    "difficulty": "easy",
    "correct": True,
    "model_answer": "O(n log n)",
    "gold_answer": "O(n log n)",
})
# One question with missing fields (stress test)
raw_questions.append({
    "question_id": "hle_9903",
    "subject": "physics",
    "modality": "table",
    "difficulty": "hard",
    "correct": False,
})

raw_report = {
    "benchmark_id": "cais/hle",
    "version": "1.0",
    "timestamp": "2024-07-15T12:34:56Z",
    "total_questions": len(raw_questions),
    "questions": raw_questions,
    "metadata": {
        "model": "openclaw-v2-candidate",
        "eval_batch": "batch_007",
        "notes": "Candidate evaluation run — do not distribute",
    }
}
raw_report_path = os.path.join(workspace, "data/raw_evals/hle_candidate_run.json")
with open(raw_report_path, "w") as f:
    json.dump(raw_report, f, indent=2)

# ── The Node.js skill scripts ─────────────────────────────────────────────────
# run_result.js: ingests report, prints Output Contract JSON
run_result_js = r"""
#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function parseArgs() {
  const args = {};
  process.argv.slice(2).forEach(a => {
    const m = a.match(/^--([^=]+)=(.*)$/);
    if (m) args[m[1]] = m[2];
  });
  return args;
}

const args = parseArgs();
const defaultReport = path.join(__dirname, '../../capability-evolver/assets/gep/hle_report.template.json');
const reportPath = args['report'] || defaultReport;

// Validate
if (!fs.existsSync(reportPath)) {
  console.error(JSON.stringify({error: 'Report not found', path: reportPath}));
  process.exit(1);
}

let report;
try {
  report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
} catch(e) {
  console.error(JSON.stringify({error: 'Invalid JSON', detail: e.message}));
  process.exit(1);
}

const benchmarkId = report.benchmark_id || 'cais/hle';
const questions = report.questions || [];
const total = questions.length;
const correct = questions.filter(q => q.correct === true).length;
const accuracy = total > 0 ? correct / total : 0;

// Reward function: sigmoid-like, scaled so 60% -> ~0.8 reward
const reward = Math.min(1.0, accuracy / 0.6);

// Trend: compare to template baseline (42% correct)
const baseline = 0.42;
const trend = accuracy > baseline ? 'improving' : accuracy < baseline ? 'declining' : 'stable';

// Curriculum stage
let curriculumStage;
if (accuracy < 0.30) curriculumStage = 'foundational';
else if (accuracy < 0.50) curriculumStage = 'developing';
else if (accuracy < 0.70) curriculumStage = 'proficient';
else curriculumStage = 'advanced';

// Easy-first queue: find incorrect questions sorted by difficulty (easy first)
const diffOrder = {easy: 0, medium: 1, hard: 2};
const incorrectQ = questions
  .filter(q => q.correct === false)
  .sort((a, b) => (diffOrder[a.difficulty] || 1) - (diffOrder[b.difficulty] || 1));

const queueSize = incorrectQ.length;

// Focus subjects: top 3 subjects with most incorrect answers
const subjectFails = {};
incorrectQ.forEach(q => {
  if (q.subject) subjectFails[q.subject] = (subjectFails[q.subject] || 0) + 1;
});
const focusSubjects = Object.entries(subjectFails)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 3)
  .map(e => e[0]);

// Focus modalities
const modalityFails = {};
incorrectQ.forEach(q => {
  if (q.modality) modalityFails[q.modality] = (modalityFails[q.modality] || 0) + 1;
});
const focusModalities = Object.entries(modalityFails)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 2)
  .map(e => e[0]);

// Next questions: first 5 from easy-first queue
const nextQuestions = incorrectQ.slice(0, 5).map(q => q.question_id);

// Run ID
const runId = crypto.createHash('sha256')
  .update(benchmarkId + (report.timestamp || Date.now().toString()) + accuracy.toString())
  .digest('hex')
  .slice(0, 16);

const result = {
  benchmark_id: benchmarkId,
  run_id: runId,
  accuracy: parseFloat(accuracy.toFixed(4)),
  reward: parseFloat(reward.toFixed(4)),
  trend,
  curriculum_stage: curriculumStage,
  queue_size: queueSize,
  focus_subjects: focusSubjects,
  focus_modalities: focusModalities,
  next_questions: nextQuestions,
};

console.log(JSON.stringify(result, null, 2));
"""

run_pipeline_js = r"""
#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const {execSync, spawnSync} = require('child_process');
const crypto = require('crypto');

function parseArgs() {
  const args = {};
  process.argv.slice(2).forEach(a => {
    const m = a.match(/^--([^=]+)=(.*)$/);
    if (m) args[m[1]] = m[2];
  });
  return args;
}

const args = parseArgs();
const defaultReport = path.join(__dirname, '../../capability-evolver/assets/gep/hle_report.template.json');
const reportPath = args['report'] || defaultReport;
const cycles = parseInt(args['cycles'] || '1', 10);
const intervalMs = parseInt(args['interval_ms'] || '1000', 10);
const evalCmd = args['eval_cmd'] || null;

const runResultScript = path.join(__dirname, 'run_result.js');

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function runCycle(cycleNum) {
  // If eval_cmd provided, run it first to regenerate report
  if (evalCmd) {
    const cmd = evalCmd.replace('{{report}}', reportPath);
    console.error(`[pipeline] cycle ${cycleNum}: running eval_cmd: ${cmd}`);
    try {
      spawnSync('sh', ['-c', cmd], {stdio: 'inherit'});
    } catch(e) {
      console.error(`[pipeline] eval_cmd failed: ${e.message}`);
    }
  }

  // Ingest
  const r = spawnSync('node', [runResultScript, `--report=${reportPath}`], {encoding: 'utf8'});
  if (r.error) { console.error('[pipeline] run_result error:', r.error); return null; }
  
  let result;
  try { result = JSON.parse(r.stdout); } catch(e) {
    console.error('[pipeline] Failed to parse run_result output:', r.stdout);
    return null;
  }

  // Solidify: write checkpoint
  const ckptDir = path.join(__dirname, '../../capability-evolver/data/checkpoints');
  fs.mkdirSync(ckptDir, {recursive: true});
  const ckptPath = path.join(ckptDir, `ckpt_cycle${cycleNum}_${result.run_id}.json`);
  fs.writeFileSync(ckptPath, JSON.stringify({cycle: cycleNum, ...result}, null, 2));
  console.error(`[pipeline] cycle ${cycleNum}: checkpoint written to ${ckptPath}`);

  return result;
}

(async () => {
  let lastResult = null;
  for (let i = 1; i <= cycles; i++) {
    lastResult = await runCycle(i);
    if (i < cycles) await sleep(intervalMs);
  }
  if (lastResult) {
    console.log(JSON.stringify(lastResult, null, 2));
  } else {
    console.error('[pipeline] No result produced');
    process.exit(1);
  }
})();
"""

with open(os.path.join(workspace, "skills/hle-benchmark-evolver/run_result.js"), "w") as f:
    f.write(run_result_js)

with open(os.path.join(workspace, "skills/hle-benchmark-evolver/run_pipeline.js"), "w") as f:
    f.write(run_pipeline_js)

# ── package.json so node can find modules ────────────────────────────────────
pkg = {"name": "hle-benchmark-evolver", "version": "1.0.0", "main": "run_result.js"}
with open(os.path.join(workspace, "skills/hle-benchmark-evolver/package.json"), "w") as f:
    json.dump(pkg, f, indent=2)

print("Workspace setup complete.")
print(f"Raw HLE report: {raw_report_path}")
print(f"Template report: {template_path}")
print(f"Skills dir: {os.path.join(workspace, 'skills/hle-benchmark-evolver/')}")