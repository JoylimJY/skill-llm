import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Distractor directory structure (10+ files) ---
dirs = [
    "editorial/raw_dumps",
    "editorial/processed",
    "editorial/reports/weekly",
    "editorial/reports/monthly",
    "infra/configs",
    "infra/logs",
    "pipelines/legacy",
    "pipelines/staging",
    "analytics/word_stats",
    "analytics/sentiment",
    "scratch",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "editorial/raw_dumps/dump_2024_01.txt": "User generated content. lots of noise!!   spaces  and -- punctuation\n\nAnother line with CAPS and   extra   spaces.",
    "editorial/raw_dumps/dump_2024_02.txt": "  More messy text. stopwords like the and a should be ignored??  \n\nRepeated word word word.",
    "editorial/processed/cleaned_sample.txt": "already cleaned text ready for analysis",
    "editorial/reports/weekly/report_wk1.json": json.dumps({"week": 1, "articles": 42, "avg_words": 312}),
    "editorial/reports/weekly/report_wk2.json": json.dumps({"week": 2, "articles": 55, "avg_words": 287}),
    "editorial/reports/monthly/summary_jan.json": json.dumps({"month": "Jan", "total": 180}),
    "infra/configs/pipeline.yaml": "version: 2\nsteps:\n  - clean\n  - tokenize\n  - count\n",
    "infra/logs/run_2024_01_15.log": "[INFO] Pipeline started\n[ERROR] text-clean failed on null input\n[INFO] Done",
    "infra/logs/run_2024_01_16.log": "[INFO] All steps succeeded\n[INFO] 3 tools called",
    "pipelines/legacy/old_normalizer.js": "// DEPRECATED - do not use\nfunction normalize(t) { return t.toLowerCase().trim(); }\nmodule.exports = { normalize };",
    "pipelines/staging/draft_counter.py": "# stub - needs replacement\nimport re\nwords = re.findall(r'\\w+', input())\nprint(len(words))",
    "analytics/word_stats/placeholder.txt": "word frequency stats go here",
    "analytics/sentiment/model_config.json": json.dumps({"model": "vader", "threshold": 0.5}),
    "scratch/notes.txt": "Need a tool that: 1) cleans text, 2) counts words, 3) returns top-N words by frequency. Should be composable.",
    "scratch/ideas.md": "- Look for text-clean in the registry\n- Look for word count / tokenizer tools\n- Chain them together\n- Submit to core category",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- The main task brief (business context, no technical hints) ---
brief = {
    "project": "ContentLens Word Pipeline",
    "request": (
        "We need a reusable pipeline component called 'text-word-freq' that takes messy raw text "
        "and returns the top-N most frequent meaningful words. "
        "It must be registered in our internal tool registry under the 'core' category. "
        "The tool should leverage any existing normalisation and utility tools already available "
        "in the ecosystem rather than reimplementing everything from scratch."
    ),
    "input_example": {"text": "  Hello world! Hello   WORLD.  foo bar foo.", "top_n": 3},
    "expected_output_shape": {"ok": True, "words": [["hello", 2], ["world", 2], ["foo", 2]]},
    "registry_category": "core",
    "tool_name": "text-word-freq",
}

with open(os.path.join(workspace, "task_brief.json"), "w") as f:
    json.dump(brief, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created: {len(distractors) + 1}")