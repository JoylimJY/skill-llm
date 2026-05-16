import os
import random
import json
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── distractor files to test contextual awareness ──────────────────────────
distractor_dirs = [
    "archive/old_logs",
    "archive/backups",
    "system/config",
    "system/cache",
    "tmp/scratch",
    "docs/api",
    "docs/internal",
    "scripts/deprecated",
    "tests/unit",
    "tests/integration",
    "vendor/libs",
]
for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "archive/old_logs/session_2023.log": "session ended at 2023-11-01T12:00:00Z\nno errors",
    "archive/old_logs/debug_dump.txt": "HEAP DUMP\n[object Object]\nundefined",
    "archive/backups/snapshot_v1.tar.gz.md": "backup manifest — do not delete",
    "system/config/runtime.json": json.dumps({"version": "1.0", "debug": False, "max_mem": 512}),
    "system/config/flags.yaml": "feature_flags:\n  emotion_module: false\n  decay_enabled: true",
    "system/cache/embeddings.bin.stub": "BINARY_PLACEHOLDER_0xDEADBEEF",
    "tmp/scratch/notes.txt": "TODO: migrate old data\ncheck retention policy",
    "docs/api/endpoints.md": "# API\nGET /status\nPOST /ingest",
    "docs/internal/onboarding.md": "# Onboarding\nAsk your manager for access.",
    "scripts/deprecated/old_memlog.sh": "#!/bin/bash\necho 'deprecated'",
    "tests/unit/test_decay.py": "# placeholder test\ndef test_noop(): pass",
    "tests/integration/test_pipeline.py": "# integration stub\nimport os",
    "vendor/libs/utils.js": "module.exports = { noop: () => {} };",
    "CHANGELOG.md": "## v1.0.0\n- initial release\n\n## v1.1.0\n- minor fixes",
    "package.json": json.dumps({"name": "memory-system", "version": "2.0.0", "scripts": {"decay": "node memory-decay.js"}}),
}
for rel_path, content in distractor_files.items():
    fp = workspace / rel_path
    fp.write_text(content)

# ── the scripts that "already exist in the workspace" ─────────────────────
scripts_dir = workspace  # scripts live at root per SKILL.md usage examples

memlog_sh = r"""#!/bin/bash
# memlog.sh — writes episodic memory entries
# Usage: memlog.sh "TITLE" "CONTENT"
set -euo pipefail
TITLE="$1"
CONTENT="$2"
DATE=$(date +%Y-%m-%d)
TARGET="memory/${DATE}.md"
mkdir -p memory
if [ ! -f "$TARGET" ]; then
  echo "# Memory Log — ${DATE}" > "$TARGET"
  echo "" >> "$TARGET"
fi
echo "## ${TITLE}" >> "$TARGET"
echo "" >> "$TARGET"
echo "${CONTENT}" >> "$TARGET"
echo "" >> "$TARGET"
echo "---" >> "$TARGET"
echo "" >> "$TARGET"
echo "[memlog] Written to ${TARGET}"
"""

memory_decay_js = r"""// memory-decay.js — applies Hot/Warm/Cold temperature labels
// Reads memory/short-term/*.md files and updates temperature metadata
const fs = require('fs');
const path = require('path');

const SHORT_TERM_DIR = path.join('memory', 'short-term');
if (!fs.existsSync(SHORT_TERM_DIR)) {
  console.log('[decay] No short-term directory found, skipping.');
  process.exit(0);
}

const files = fs.readdirSync(SHORT_TERM_DIR).filter(f => f.endsWith('.md'));
let processed = 0;
files.forEach(file => {
  const fp = path.join(SHORT_TERM_DIR, file);
  let content = fs.readFileSync(fp, 'utf8');
  // Mark as Warm if already Hot (simulated decay step)
  if (content.includes('temperature: Hot')) {
    content = content.replace('temperature: Hot', 'temperature: Warm');
    fs.writeFileSync(fp, content);
    console.log(`[decay] ${file}: Hot -> Warm`);
    processed++;
  } else if (content.includes('temperature: Warm')) {
    content = content.replace('temperature: Warm', 'temperature: Cold');
    fs.writeFileSync(fp, content);
    console.log(`[decay] ${file}: Warm -> Cold`);
    processed++;
  }
});
console.log(`[decay] Processed ${processed} file(s).`);
"""

memory_gc_sh = r"""#!/bin/bash
# memory-gc.sh — archives Cold short-term memories to archive/
set -euo pipefail
SHORT_TERM="memory/short-term"
ARCHIVE="archive/old_logs"
mkdir -p "$ARCHIVE"
count=0
for f in "$SHORT_TERM"/*.md 2>/dev/null; do
  [ -f "$f" ] || continue
  if grep -q "temperature: Cold" "$f"; then
    mv "$f" "$ARCHIVE/"
    echo "[gc] Archived: $f"
    count=$((count+1))
  fi
done
echo "[gc] Archived ${count} Cold memory file(s)."
"""

(workspace / "memlog.sh").write_text(memlog_sh)
(workspace / "memory-decay.js").write_text(memory_decay_js)
(workspace / "memory-gc.sh").write_text(memory_gc_sh)
os.chmod(workspace / "memlog.sh", 0o755)
os.chmod(workspace / "memory-gc.sh", 0o755)

# ── RAW MESSY INPUT: interaction logs (what agent must process) ────────────
raw_logs_dir = workspace / "raw_inputs"
raw_logs_dir.mkdir(exist_ok=True)

# Raw interaction log 1 — mix of facts, session tasks, emotion cues
(raw_logs_dir / "interaction_log_001.txt").write_text("""=== AI Assistant Interaction Log ===
Date: 2024-06-10
Session ID: sess-8821

[09:03] User: Good morning! Can you remind me what we discussed about the neural embedding pipeline last week?
[09:04] Assistant: Sure — last week we finalized that the embedding model will use 768-dim vectors with cosine similarity threshold of 0.82.
[09:05] User: Great. Also I'm feeling quite stressed about the deadline on Friday.
[09:06] Assistant: Understood, I'll keep responses concise to save you time.
[09:07] User: What's the current status of the data ingestion module?
[09:08] Assistant: Status: 60% complete. Blocking issue: schema mismatch on legacy CSV files from vendor X.
[09:09] User: Add to tasks: resolve schema mismatch before EOD Thursday.
[09:10] Assistant: Task added.
[09:11] User: Also note that our infrastructure team confirmed: Kubernetes cluster uses v1.29.2.
[09:12] Assistant: Noted. I'll record that as a stable infrastructure fact.
""")

# Raw interaction log 2 — uncertain facts, low-confidence items
(raw_logs_dir / "interaction_log_002.txt").write_text("""=== AI Assistant Interaction Log ===
Date: 2024-06-11
Session ID: sess-8822

[10:15] User: What was the name of the third-party analytics vendor we shortlisted?
[10:16] Assistant: I believe it might have been "DataStream Pro" but I'm not fully certain — my confidence is around 35%.
[10:17] User: And their pricing model?
[10:18] Assistant: I think it was usage-based, approximately $0.002 per query, but again I'm uncertain — confidence ~40%.
[10:19] User: Okay let's move on. The model training run from yesterday finished — final validation accuracy was 94.3%.
[10:20] Assistant: Recorded. High confidence fact.
[10:21] User: I remember we also agreed on something about data retention but I can't recall exactly.
[10:22] Assistant: I have a vague recollection of a 90-day retention window being discussed, but confidence is only 30%.
""")

# Raw project brief — complex task requiring decomposition
(raw_logs_dir / "project_brief_alpha.txt").write_text("""PROJECT BRIEF — ALPHA DEMO PREPARATION
======================================
Project Name: Alpha Demo
Due: 2024-06-21
Priority: CRITICAL

Overview:
Prepare the full AI assistant system for a live investor demo on June 21st.

Required work:
1. Finalize the memory retrieval API (endpoint: GET /memory/retrieve) with sub-200ms latency.
2. Integrate emotion-detection module into the response pipeline.
3. Conduct end-to-end load testing with 500 concurrent simulated users.
4. Prepare demo script and talking points for the CTO presentation.
5. Deploy to staging environment and run smoke tests 48 hours before demo.
6. Create fallback plan if live system fails during demo.

Assigned: Engineering team
Notes: Steps 1 and 2 are blocking for step 3. Step 5 must happen before step 6.
""")

# Semantic facts dump — needs to go into semantic knowledge base
(raw_logs_dir / "semantic_facts_dump.txt").write_text("""SEMANTIC FACTS EXTRACTED — batch 2024-06-10
============================================
fact_001: embedding_dim = 768, similarity_metric = cosine, threshold = 0.82
fact_002: kubernetes_version = 1.29.2, cluster = production
fact_003: model_validation_accuracy = 94.3%, run_date = 2024-06-10
fact_004: data_ingestion_status = in_progress, completion = 60%
fact_005: vendor_analytics_candidate = "DataStream Pro" [UNCERTAIN — confidence: 35%]
fact_006: analytics_pricing = "$0.002/query usage-based" [UNCERTAIN — confidence: 40%]
fact_007: data_retention_window = "90 days" [UNCERTAIN — confidence: 30%]
""")

print("Workspace scaffold complete.")
print(f"Files created under: {workspace}")