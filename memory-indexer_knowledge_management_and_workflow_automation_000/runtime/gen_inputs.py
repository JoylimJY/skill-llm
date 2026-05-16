import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Create deeply nested distractor structure simulating a research lab project
dirs = [
    "lab_projects/protein_folding/data",
    "lab_projects/protein_folding/results",
    "lab_projects/nlp_research/datasets",
    "lab_projects/nlp_research/models",
    "lab_projects/nlp_research/experiments",
    "lab_projects/cv_team/annotations",
    "lab_projects/cv_team/checkpoints",
    "admin/budgets/2024",
    "admin/budgets/2025",
    "admin/meeting_minutes",
    "admin/hr_records",
    "tools/scripts",
    "tools/config",
    "archive/2023",
    "archive/2022/q1",
    "archive/2022/q2",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "lab_projects/protein_folding/data/sequences.csv": "id,sequence\n1,MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPQTIGGGIGQSRLTMLLLQLPHIGQVQAGVWPAAVRESVPSLL\n",
    "lab_projects/protein_folding/results/summary_2024.txt": "Experiment Results Q4 2024\nProtein stability: 87.3%\nFolding accuracy: 0.92 RMSD\n",
    "lab_projects/nlp_research/datasets/corpus_stats.json": json.dumps({"total_docs": 15000, "languages": ["zh", "en"], "avg_length": 312}),
    "lab_projects/nlp_research/models/model_config.yaml": "model: bert-base\nhidden_size: 768\nnum_layers: 12\nvocab_size: 21128\n",
    "lab_projects/nlp_research/experiments/exp_001.log": "Epoch 1/10: loss=2.341\nEpoch 2/10: loss=1.892\nEpoch 3/10: loss=1.543\n",
    "lab_projects/nlp_research/experiments/exp_002.log": "Epoch 1/5: loss=1.234\nEpoch 2/5: loss=0.987\n",
    "lab_projects/cv_team/annotations/label_schema.json": json.dumps({"classes": ["cat", "dog", "bird"], "version": "2.1"}),
    "lab_projects/cv_team/checkpoints/best_model.txt": "checkpoint: epoch_45\nval_accuracy: 0.9312\n",
    "admin/budgets/2024/q4_budget.csv": "category,amount\nequipment,50000\nsalaries,120000\nconsumables,8000\n",
    "admin/budgets/2025/q1_forecast.txt": "Projected spend Q1 2025: $45,000\n",
    "admin/meeting_minutes/2024_12_15.txt": "Attendees: Prof. Zhang, Dr. Li, Dr. Wang\nTopic: End of year review\nDecision: Continue protein folding project\n",
    "admin/hr_records/headcount.txt": "Current headcount: 23\nPhD students: 8\nPostdocs: 5\nEngineers: 10\n",
    "tools/scripts/backup.sh": "#!/bin/bash\ntar -czf backup_$(date +%Y%m%d).tar.gz /workspace/lab_projects\n",
    "tools/config/environment.yml": "name: research\nchannels:\n  - conda-forge\ndependencies:\n  - python=3.11\n  - pytorch\n",
    "archive/2023/old_results.tar.gz.txt": "This file was archived. Original size: 2.3GB\n",
    "archive/2022/q1/notes.txt": "Q1 2022 research notes placeholder\n",
    "archive/2022/q2/notes.txt": "Q2 2022 research notes placeholder\n",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content, encoding="utf-8")

# The core task definition file - tells the agent WHAT to do in business terms
task_brief = """# Research Knowledge Cataloging Task

## Context
The lab research team needs to organize key research insights into the knowledge management system.

## Notes to Catalog
The following research notes must be added to the knowledge index:

1. "今天完成了蛋白质折叠实验，使用AlphaFold模型预测结构，准确率达到92%，这是一个重大突破"
2. "NLP团队完成了中文语料库标注，共15000篇文档，支持多语言处理，包括中文和英文"
3. "深度学习模型训练完成，使用BERT架构，在蛋白质序列分析任务上表现优异，损失函数收敛"
4. "实验室采购了新的GPU服务器，用于深度学习训练，将大幅提升模型训练速度和效率"
5. "团队发现蛋白质折叠与基因表达之间存在强相关性，需要进一步研究深度学习方法验证"
6. "NLP模型成功应用于医疗文本分析，识别出关键医学实体，准确率超过95%，效果显著"

## Important Flagging
After adding all notes, the following notes must be flagged as HIGH PRIORITY (starred):
- The note about AlphaFold protein structure prediction breakthrough
- The note about NLP model application to medical text analysis

## Verification Required
After completing the above steps:
1. Perform a strict multi-topic search for notes that mention BOTH "蛋白质" AND "深度学习" - save the search results to a file named `search_results.txt` in /workspace
2. Run the association discovery feature and save its output to a file named `related_output.txt` in /workspace
3. Run the status check and save its output to a file named `status_output.txt` in /workspace
"""

(workspace / "task_brief.txt").write_text(task_brief, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")