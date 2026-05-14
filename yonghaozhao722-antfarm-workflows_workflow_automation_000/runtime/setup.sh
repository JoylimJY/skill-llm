#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Build a deterministic mock antfarm CLI that simulates the real tool's
# behavior: install, workflow list/run/status/runs, step claim/complete/stories,
# cron list/run, logs, dashboard.
# State is persisted in a SQLite-backed JSON flat-file for simplicity.
# ─────────────────────────────────────────────────────────────────────────────

ANTFARM_DIR="$HOME/.openclaw/workspace/antfarm"
CLI_DIR="$ANTFARM_DIR/dist/cli"
STATE_DIR="$HOME/.openclaw/antfarm-state"

mkdir -p "$CLI_DIR" "$STATE_DIR"

# ── State files ───────────────────────────────────────────────────────────────
STATE_FILE="$STATE_DIR/state.json"
RUNS_FILE="$STATE_DIR/runs.json"
STEPS_FILE="$STATE_DIR/steps.json"
CRONS_FILE="$STATE_DIR/crons.json"
LOG_FILE="$STATE_DIR/antfarm.log"
INSTALLED_FLAG="$STATE_DIR/installed"

# ── Write the mock CLI script ─────────────────────────────────────────────────
cat > "$CLI_DIR/cli.js" << 'CLISCRIPT'
#!/usr/bin/env node
"use strict";

const fs   = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const STATE_DIR     = path.join(process.env.HOME, ".openclaw", "antfarm-state");
const RUNS_FILE     = path.join(STATE_DIR, "runs.json");
const STEPS_FILE    = path.join(STATE_DIR, "steps.json");
const CRONS_FILE    = path.join(STATE_DIR, "crons.json");
const LOG_FILE      = path.join(STATE_DIR, "antfarm.log");
const INSTALLED_FLAG = path.join(STATE_DIR, "installed");

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_FILE, line);
}

function readJSON(f, def) {
  try { return JSON.parse(fs.readFileSync(f, "utf8")); } catch { return def; }
}
function writeJSON(f, d) { fs.writeFileSync(f, JSON.stringify(d, null, 2)); }

function genId(prefix) {
  return prefix + "-" + Math.random().toString(36).slice(2, 9);
}

const args = process.argv.slice(2);
const cmd  = args[0];

// ── install ──────────────────────────────────────────────────────────────────
if (cmd === "install") {
  if (fs.existsSync(INSTALLED_FLAG)) {
    console.log("antfarm already installed.");
  } else {
    fs.writeFileSync(INSTALLED_FLAG, new Date().toISOString());
    writeJSON(RUNS_FILE,  []);
    writeJSON(STEPS_FILE, []);
    // Seed cron entries for all workflow agents
    const workflows = ["feature-dev","bug-fix","security-audit"];
    const agentsByWorkflow = {
      "feature-dev":    ["planner","developer","verifier","tester","reviewer"],
      "bug-fix":        ["triage","investigator","fixer","verifier","pr-agent"],
      "security-audit": ["scanner","prioritizer","fixer","verifier","tester"],
    };
    const crons = [];
    workflows.forEach(wf => {
      (agentsByWorkflow[wf] || []).forEach((ag, i) => {
        crons.push({
          id:       `antfarm/${wf}/${ag}`,
          workflow: wf,
          agent:    ag,
          schedule: `*/${15 + i} * * * *`,
          lastRun:  null,
          enabled:  true,
        });
      });
    });
    writeJSON(CRONS_FILE, crons);
    log("antfarm installed");
    console.log("✓ antfarm installed successfully.");
    console.log("  Agents: planner, developer, verifier, tester, reviewer (feature-dev)");
    console.log("  Agents: triage, investigator, fixer, verifier, pr-agent (bug-fix)");
    console.log("  Dashboard started on port 3000");
  }
  process.exit(0);
}

// ── uninstall ────────────────────────────────────────────────────────────────
if (cmd === "uninstall") {
  [RUNS_FILE, STEPS_FILE, CRONS_FILE, LOG_FILE, INSTALLED_FLAG].forEach(f => {
    try { fs.unlinkSync(f); } catch {}
  });
  console.log("✓ antfarm uninstalled.");
  process.exit(0);
}

// ── logs ─────────────────────────────────────────────────────────────────────
if (cmd === "logs") {
  const n = parseInt(args[1] || "50", 10);
  try {
    const lines = fs.readFileSync(LOG_FILE, "utf8").trim().split("\n");
    console.log(lines.slice(-n).join("\n"));
  } catch { console.log("(no logs yet)"); }
  process.exit(0);
}

// ── dashboard ────────────────────────────────────────────────────────────────
if (cmd === "dashboard") {
  const sub = args[1] || "start";
  if (sub === "stop") { console.log("Dashboard stopped."); }
  else { console.log("Dashboard running at http://localhost:3000"); }
  process.exit(0);
}

// ── workflow ─────────────────────────────────────────────────────────────────
if (cmd === "workflow") {
  const sub = args[1];

  if (sub === "list") {
    console.log("Available workflows:");
    console.log("  ID             NAME             PIPELINE");
    console.log("  feature-dev    Feature Dev      plan -> setup -> develop -> verify -> test -> PR -> review");
    console.log("  bug-fix        Bug Fix          triage -> investigate -> setup -> fix -> verify -> PR");
    console.log("  security-audit Security Audit   scan -> prioritize -> setup -> fix -> verify -> test -> PR");
    process.exit(0);
  }

  if (sub === "runs") {
    const runs = readJSON(RUNS_FILE, []);
    if (runs.length === 0) { console.log("No runs found."); process.exit(0); }
    console.log("RUN-ID              WORKFLOW    STATUS     CREATED");
    runs.forEach(r => {
      console.log(`${r.id.padEnd(20)} ${r.workflow.padEnd(12)} ${r.status.padEnd(10)} ${r.createdAt}`);
    });
    process.exit(0);
  }

  if (sub === "run") {
    // antfarm workflow run <workflow-id> "<task>"
    const workflowId = args[2];
    const task       = args[3] || "";
    if (!workflowId) { console.error("Usage: workflow run <workflow-id> \"<task>\""); process.exit(1); }
    if (!fs.existsSync(INSTALLED_FLAG)) { console.error("antfarm not installed. Run: antfarm install"); process.exit(1); }

    const validWorkflows = ["feature-dev","bug-fix","security-audit"];
    if (!validWorkflows.includes(workflowId)) {
      console.error(`Unknown workflow: ${workflowId}. Valid: ${validWorkflows.join(", ")}`);
      process.exit(1);
    }

    const runId = genId("run");
    const now   = new Date().toISOString();

    // First step per workflow
    const firstStepByWorkflow = { "feature-dev":"plan", "bug-fix":"triage", "security-audit":"scan" };
    const firstAgent           = firstStepByWorkflow[workflowId];

    const run = { id: runId, workflow: workflowId, task, status: "running", currentStep: firstAgent, createdAt: now, updatedAt: now };
    const runs = readJSON(RUNS_FILE, []);
    runs.push(run);
    writeJSON(RUNS_FILE, runs);

    // Create first pending step
    const stepId = genId("step");
    const steps  = readJSON(STEPS_FILE, []);
    steps.push({ id: stepId, runId, agent: firstAgent, status: "pending", createdAt: now, output: null });
    writeJSON(STEPS_FILE, steps);

    log(`workflow run started: ${runId} workflow=${workflowId}`);
    console.log(`✓ Run started.`);
    console.log(`  Run ID:   ${runId}`);
    console.log(`  Workflow: ${workflowId}`);
    console.log(`  Status:   running`);
    console.log(`  Next step: ${firstAgent} (pending)`);
    process.exit(0);
  }

  if (sub === "status") {
    const query = args[2] || "";
    const runs  = readJSON(RUNS_FILE, []);
    const steps = readJSON(STEPS_FILE, []);
    // match by run-id prefix or task substring
    const run = runs.find(r => r.id.startsWith(query) || r.task.includes(query));
    if (!run) { console.log(`No run found matching: ${query}`); process.exit(1); }
    const runSteps = steps.filter(s => s.runId === run.id);
    console.log(`Run ID:      ${run.id}`);
    console.log(`Workflow:    ${run.workflow}`);
    console.log(`Status:      ${run.status}`);
    console.log(`Current step: ${run.currentStep}`);
    console.log(`Task:        ${run.task}`);
    console.log(`Created:     ${run.createdAt}`);
    console.log(`Updated:     ${run.updatedAt}`);
    console.log(`Steps:`);
    runSteps.forEach(s => {
      console.log(`  [${s.status.padEnd(10)}] ${s.agent.padEnd(15)} id=${s.id}`);
    });
    process.exit(0);
  }

  if (sub === "install" || sub === "uninstall") {
    console.log(`workflow ${sub} ${args[2] || "--all"}: OK`);
    process.exit(0);
  }

  if (sub === "resume") {
    const runId = args[2];
    const runs  = readJSON(RUNS_FILE, []);
    const r     = runs.find(x => x.id === runId || x.id.startsWith(runId));
    if (!r) { console.error(`Run not found: ${runId}`); process.exit(1); }
    console.log(`Resuming run ${r.id} from step ${r.currentStep}`);
    process.exit(0);
  }

  console.error(`Unknown workflow subcommand: ${sub}`);
  process.exit(1);
}

// ── step ─────────────────────────────────────────────────────────────────────
if (cmd === "step") {
  const sub = args[1];

  if (sub === "claim") {
    const agentId = args[2];
    const steps   = readJSON(STEPS_FILE, []);
    const runs    = readJSON(RUNS_FILE, []);
    // Find pending step for this agent
    const step = steps.find(s => s.agent === agentId && s.status === "pending");
    if (!step) { console.log(`No pending step for agent: ${agentId}`); process.exit(0); }
    step.status    = "in-progress";
    step.claimedAt = new Date().toISOString();
    writeJSON(STEPS_FILE, steps);
    log(`step claimed: ${step.id} by ${agentId}`);
    console.log(`✓ Step claimed.`);
    console.log(`  Step ID:  ${step.id}`);
    console.log(`  Run ID:   ${step.runId}`);
    console.log(`  Agent:    ${agentId}`);
    console.log(`  Status:   in-progress`);
    process.exit(0);
  }

  if (sub === "complete") {
    const stepId = args[2];
    const steps  = readJSON(STEPS_FILE, []);
    const runs   = readJSON(RUNS_FILE, []);
    let input = "";
    try { input = fs.readFileSync("/dev/stdin", "utf8"); } catch {}
    const step = steps.find(s => s.id === stepId);
    if (!step) { console.error(`Step not found: ${stepId}`); process.exit(1); }
    step.status      = "completed";
    step.output      = input;
    step.completedAt = new Date().toISOString();
    writeJSON(STEPS_FILE, steps);
    // advance run
    const run = runs.find(r => r.id === step.runId);
    if (run) {
      const pipelines = {
        "bug-fix": ["triage","investigate","setup","fix","verify","pr"]
      };
      const pipe  = pipelines[run.workflow] || [];
      const idx   = pipe.indexOf(step.agent);
      const next  = pipe[idx + 1];
      if (next) {
        run.currentStep = next;
        run.updatedAt   = new Date().toISOString();
        // create next pending step
        steps.push({ id: genId("step"), runId: run.id, agent: next, status: "pending", createdAt: new Date().toISOString(), output: null });
      } else {
        run.status    = "completed";
        run.updatedAt = new Date().toISOString();
      }
      writeJSON(RUNS_FILE, runs);
    }
    writeJSON(STEPS_FILE, steps);
    log(`step completed: ${stepId}`);
    console.log(`✓ Step ${stepId} completed.`);
    process.exit(0);
  }

  if (sub === "fail") {
    const stepId = args[2];
    const error  = args[3] || "unknown error";
    const steps  = readJSON(STEPS_FILE, []);
    const step   = steps.find(s => s.id === stepId);
    if (!step) { console.error(`Step not found: ${stepId}`); process.exit(1); }
    step.status = "failed";
    step.error  = error;
    writeJSON(STEPS_FILE, steps);
    log(`step failed: ${stepId} error=${error}`);
    console.log(`Step ${stepId} marked failed: ${error}`);
    process.exit(0);
  }

  if (sub === "stories") {
    const runId = args[2];
    console.log(`Stories for run ${runId}:`);
    console.log("  (no stories yet — workflow still in triage phase)");
    process.exit(0);
  }

  console.error(`Unknown step subcommand: ${sub}`);
  process.exit(1);
}

// ── cron ─────────────────────────────────────────────────────────────────────
if (cmd === "cron") {
  const sub = args[1];

  if (sub === "list") {
    const crons = readJSON(CRONS_FILE, []);
    console.log("CRON-ID                                SCHEDULE       LAST-RUN");
    crons.forEach(c => {
      console.log(`${c.id.padEnd(38)} ${c.schedule.padEnd(15)} ${c.lastRun || "never"}`);
    });
    process.exit(0);
  }

  if (sub === "run") {
    // cron run <cron-id>  → simulate agent tick: claim + auto-complete first pending step
    const cronId = args[2];
    const crons  = readJSON(CRONS_FILE, []);
    const cron   = crons.find(c => c.id === cronId);
    if (!cron) { console.error(`Cron not found: ${cronId}`); process.exit(1); }

    const steps  = readJSON(STEPS_FILE, []);
    const runs   = readJSON(RUNS_FILE, []);

    // Find in-progress or pending step for this agent
    const step = steps.find(s => s.agent === cron.agent && (s.status === "pending" || s.status === "in-progress"));
    if (!step) {
      console.log(`No actionable step for cron ${cronId} (agent: ${cron.agent})`);
      process.exit(0);
    }

    // Simulate agent doing work: claim + complete
    step.status      = "completed";
    step.claimedAt   = new Date().toISOString();
    step.completedAt = new Date().toISOString();
    step.output      = `Agent ${cron.agent} processed step autonomously via cron trigger.\nNEXT_CONTEXT: ready`;

    cron.lastRun = new Date().toISOString();

    // Advance run
    const run = runs.find(r => r.id === step.runId);
    if (run) {
      const pipelines = {
        "feature-dev":    ["plan","setup","develop","verify","test","pr","review"],
        "bug-fix":        ["triage","investigate","setup","fix","verify","pr"],
        "security-audit": ["scan","prioritize","setup","fix","verify","test","pr"],
      };
      const pipe = pipelines[run.workflow] || [];
      const idx  = pipe.indexOf(step.agent);
      const next = pipe[idx + 1];
      if (next) {
        run.currentStep = next;
        run.updatedAt   = new Date().toISOString();
        steps.push({ id: genId("step"), runId: run.id, agent: next, status: "pending", createdAt: new Date().toISOString(), output: null });
        log(`cron ${cronId}: step ${step.id} completed, advanced to ${next}`);
        console.log(`✓ Cron triggered for ${cronId}`);
        console.log(`  Agent:     ${cron.agent}`);
        console.log(`  Step:      ${step.id} → completed`);
        console.log(`  Next step: ${next} (pending)`);
      } else {
        run.status    = "completed";
        run.updatedAt = new Date().toISOString();
        console.log(`✓ Cron triggered for ${cronId} — workflow ${run.id} COMPLETED.`);
      }
    }
    writeJSON(RUNS_FILE, runs);
    writeJSON(STEPS_FILE, steps);
    writeJSON(CRONS_FILE, crons);
    process.exit(0);
  }

  console.error(`Unknown cron subcommand: ${sub}`);
  process.exit(1);
}

console.error(`Unknown command: ${cmd}`);
console.error(`Usage: antfarm-cli <install|uninstall|workflow|step|cron|logs|dashboard>`);
process.exit(1);
CLISCRIPT

chmod +x "$CLI_DIR/cli.js"

echo "Mock antfarm CLI installed at $CLI_DIR/cli.js"
echo "Test: node $CLI_DIR/cli.js install"