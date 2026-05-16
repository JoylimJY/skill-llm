import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "platform/ingestion/raw",
    "platform/ingestion/processed",
    "platform/review/pending",
    "platform/review/flagged",
    "platform/review/approved",
    "platform/metadata/authors",
    "platform/metadata/journals",
    "platform/config/pipelines",
    "platform/logs/2024-01",
    "platform/logs/2024-02",
    "platform/archive/2023",
    "platform/archive/2022",
    "tools/validators",
    "tools/parsers",
    "reports/monthly",
    "reports/weekly",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ---- Distractor files ----
distractors = {
    "platform/config/pipelines/pipeline_config.yaml": "version: 2\nsteps:\n  - ingest\n  - validate\n  - analyze\n  - report\n",
    "platform/config/pipelines/thresholds.json": json.dumps({"plagiarism_threshold": 0.85, "similarity_cutoff": 0.6}),
    "platform/metadata/authors/author_index.csv": "author_id,name,affiliation\n1,Dr. Smith,MIT\n2,Prof. Lee,Stanford\n3,Jane Doe,Oxford\n",
    "platform/metadata/journals/journal_list.txt": "Nature\nScience\nCell\nLancet\nPLoS ONE\n",
    "platform/ingestion/raw/batch_manifest.json": json.dumps({"batch_id": "b2024-03", "count": 5, "status": "pending"}),
    "platform/review/flagged/flag_log.txt": "2024-01-10: submission_003 flagged for review\n2024-01-11: submission_007 escalated\n",
    "platform/review/approved/approval_log.txt": "2024-02-01: submission_001 approved\n2024-02-03: submission_002 approved\n",
    "platform/logs/2024-01/ingest.log": "INFO: 10 articles ingested\nWARN: 2 articles had missing abstracts\nINFO: Pipeline complete\n",
    "platform/logs/2024-02/ingest.log": "INFO: 8 articles ingested\nINFO: Pipeline complete\n",
    "tools/validators/schema_validator.py": "# Validates submission JSON schema\ndef validate(data):\n    required = ['id', 'title', 'body']\n    return all(k in data for k in required)\n",
    "tools/parsers/text_cleaner.py": "# Cleans raw text\nimport re\ndef clean(text):\n    return re.sub(r'\\s+', ' ', text).strip()\n",
    "platform/archive/2023/summary_2023.json": json.dumps({"total": 120, "flagged": 14, "approved": 106}),
    "platform/archive/2022/summary_2022.json": json.dumps({"total": 98, "flagged": 9, "approved": 89}),
    "reports/monthly/template.txt": "Monthly Report Template\n========================\nBatch ID: {{batch_id}}\nTotal: {{total}}\nFlagged: {{flagged}}\n",
    "reports/weekly/placeholder.txt": "No weekly reports generated yet.\n",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ---- The actual submissions to analyze ----
# Each submission is a text file. The agent must analyze all of them and produce analysis_report.json

submissions = {
    "submission_A.txt": (
        "The landscape of modern artificial intelligence is both multifaceted and nuanced. "
        "It's important to note that a holistic approach is required when navigating the realm of "
        "deep learning systems. Researchers must delve into the comprehensive frameworks that "
        "underpin these models.\n"
        "1. Data preprocessing steps\n"
        "2. Model architecture selection\n"
        "3. Hyperparameter tuning protocols\n"
        "The field continues to evolve rapidly."
    ),
    "submission_B.txt": (
        "As an AI language model, I don't have personal opinions on this matter. "
        "I apologize for any confusion in my previous response. Certainly, the methodology "
        "you described is valid. Furthermore, it is worth noting that the experimental setup "
        "aligns with established protocols. Moreover, the results are consistent with the literature.\n"
        "- Data was collected over six months\n"
        "- Analysis was performed using standard tools\n"
        "- Results were peer-reviewed\n"
        "In conclusion, the study demonstrates significant findings."
    ),
    "submission_C.txt": (
        "The experiment used a simple random sample of 200 participants. "
        "Each participant completed a survey. "
        "Data was entered into a spreadsheet. "
        "Results were calculated manually. "
        "The findings suggest a positive correlation."
    ),
    "submission_D.txt": (
        "To summarize the key contributions of this paper: first, we introduce a novel "
        "optimization algorithm. In summary, the tapestry of related work reveals gaps "
        "that our approach addresses. Navigate the challenges of distributed systems "
        "requires careful consideration. Keep in mind that these results are preliminary."
    ),
    "submission_E.txt": (
        "Absolutely! The proposed framework is designed to handle edge cases. "
        "I don't have personal experience with this hardware, but the literature suggests "
        "it performs well. Furthermore, the theoretical guarantees are sound. "
        "Moreover, empirical validation confirms these claims. "
        "Certainly, further work is warranted. I apologize for the brevity of this section.\n"
        "1. Setup the environment\n"
        "2. Run the baseline\n"
        "3. Compare results\n"
        "The approach is scalable."
    ),
}

submissions_dir = os.path.join(WORKSPACE, "platform/ingestion/raw/submissions")
os.makedirs(submissions_dir, exist_ok=True)

for filename, content in submissions.items():
    with open(os.path.join(submissions_dir, filename), "w") as f:
        f.write(content)

# Also write a skill reference file for the agent to use
skill_path = os.path.join(WORKSPACE, "SKILL.md")
skill_content = '''---
id: gpt-analyzer
version: 1.0.0
name: GPT Analyzer
description: GPT-specific pattern detection with model fingerprinting and version identification
author: NeoClaw Team
category: detection
tags:
  - ai-detection
  - gpt
  - pattern-matching
  - model-fingerprinting
dependencies: []
---

# GPT Analyzer

Specialized detection for GPT-generated content with model-specific pattern recognition.

## Implementation

```javascript
/**
 * Analyze text for GPT-specific patterns and fingerprints
 * @param {string} text - Text to analyze
 * @param {object} options - Configuration options
 * @returns {object} Analysis result with model identification
 */
async function analyzeGPTContent(text, options = {}) {
  const {
    detectVersion = true,
    checkWatermarks = true,
    minConfidence = 0.7
  } = options;

  const normalizedText = text.toLowerCase();
  const wordCount = text.split(/\\s+/).length;

  // GPT-specific phrases (stronger indicators)
  const gptPhrases = {
    \'gpt-4\': [
      \'delve into\', \'landscape of\', \'realm of\', \'it\\\'s important to note\',
      \'multifaceted\', \'nuanced\', \'comprehensive\', \'holistic approach\'
    ],
    \'gpt-3.5\': [
      \'as an ai language model\', \'i don\\\'t have personal\', \'i apologize for\',
      \'certainly\', \'absolutely\', \'furthermore\', \'moreover\'
    ],
    \'common\': [
      \'it\\\'s worth noting\', \'keep in mind\', \'in conclusion\',
      \'to summarize\', \'in summary\', \'navigate the\', \'tapestry of\'
    ]
  };

  // Model fingerprinting
  let gpt4Score = 0;
  let gpt35Score = 0;
  let commonScore = 0;
  const foundPhrases = [];

  // Check GPT-4 specific patterns
  for (const phrase of gptPhrases[\'gpt-4\']) {
    if (normalizedText.includes(phrase)) {
      gpt4Score += 0.2;
      foundPhrases.push({ phrase, model: \'gpt-4\' });
    }
  }

  // Check GPT-3.5 specific patterns
  for (const phrase of gptPhrases[\'gpt-3.5\']) {
    if (normalizedText.includes(phrase)) {
      gpt35Score += 0.2;
      foundPhrases.push({ phrase, model: \'gpt-3.5\' });
    }
  }

  // Check common GPT patterns
  for (const phrase of gptPhrases[\'common\']) {
    if (normalizedText.includes(phrase)) {
      commonScore += 0.1;
      foundPhrases.push({ phrase, model: \'common\' });
    }
  }

  // Structure analysis
  const hasNumberedLists = (text.match(/\\n\\d+\\./g) || []).length >= 3;
  const hasBulletPoints = (text.match(/\\n[•\\-\\*]/g) || []).length >= 3;
  const structureScore = (hasNumberedLists || hasBulletPoints) ? 0.15 : 0;

  // Sentence uniformity
  const sentences = text.split(/[.!?]+/).filter(s => s.trim());
  const avgLength = sentences.reduce((sum, s) => sum + s.length, 0) / sentences.length;
  const variance = sentences.reduce((sum, s) => sum + Math.pow(s.length - avgLength, 2), 0) / sentences.length;
  const uniformityScore = variance < 500 ? 0.1 : 0;

  // Calculate confidence
  const totalScore = gpt4Score + gpt35Score + commonScore + structureScore + uniformityScore;
  const confidence = Math.min(totalScore, 1.0);

  // Determine model
  let detectedModel = \'unknown\';
  if (gpt4Score > gpt35Score && gpt4Score > 0) {
    detectedModel = \'gpt-4\';
  } else if (gpt35Score > gpt4Score && gpt35Score > 0) {
    detectedModel = \'gpt-3.5\';
  } else if (commonScore > 0) {
    detectedModel = \'gpt-family\';
  }

  const isGPT = confidence >= minConfidence;

  return {
    isGPT,
    confidence: Math.round(confidence * 100),
    detectedModel: isGPT ? detectedModel : \'not-gpt\',
    scores: {
      gpt4: Math.round(gpt4Score * 100) / 100,
      gpt35: Math.round(gpt35Score * 100) / 100,
      common: Math.round(commonScore * 100) / 100,
      structure: Math.round(structureScore * 100) / 100,
      uniformity: Math.round(uniformityScore * 100) / 100
    },
    indicators: {
      foundPhrases: foundPhrases.length,
      hasStructure: hasNumberedLists || hasBulletPoints,
      avgSentenceLength: Math.round(avgLength),
      sentenceVariance: Math.round(variance)
    },
    recommendation: confidence >= 0.85 ? \'Very likely GPT\' :
                     confidence >= 0.70 ? \'Likely GPT\' :
                     confidence >= 0.50 ? \'Possibly GPT\' :
                     \'Unlikely GPT or human-written\'
  };
}

// Export for OpenClaw
module.exports = {
  analyzeGPTContent
};
```

## Usage

```javascript
const result = await skills.gptAnalyzer.analyzeGPTContent(text);

if (result.isGPT) {
  console.log(`GPT detected: ${result.detectedModel} (${result.confidence}% confidence)`);
}
```

## Configuration

```json
{
  "detectVersion": true,
  "minConfidence": 0.7
}
```
'''

with open(skill_path, "w") as f:
    f.write(skill_content)

print("Workspace initialized successfully.")
print(f"Submissions written to: {submissions_dir}")