#!/usr/bin/env python3
import os
import json

WORKSPACE = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "references",
    "assets",
    "scripts",
    "sessions",
    "sessions/cambridge4",
    "sessions/cambridge5",
    "sessions/cambridge17",
    "vocab",
    "notes/drafts",
    "notes/archive",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "notes/drafts/scratch.txt": "random notes about grammar",
    "notes/archive/old_review.txt": "old C4T1P1 review content",
    "vocab/custom_list.csv": "word,meaning\nacquire,获得\nperceive,感知\n",
    "logs/session_log.txt": "2024-01-10 session started\n2024-01-11 session ended\n",
    "sessions/cambridge4/c4t3_raw.txt": "Cambridge 4 Test 3 raw data\nP1:13correct P2:12correct",
    "sessions/cambridge5/c5t2_notes.txt": "Quick notes from C5T2: struggled with P3",
    "scripts/helper.py": "# placeholder helper\ndef noop(): pass\n",
    "assets/old_template_v1.html": "<html><body>old template</body></html>",
    "references/grammar_notes.md": "# Grammar Notes\n- Subject verb agreement\n- Tense consistency\n",
    "logs/errors.log": "[ERROR] session not found\n[WARN] vocab list incomplete\n",
    "notes/drafts/todo.md": "- review passage 3\n- update vocab list\n- check timing\n",
}
for path, content in distractors.items():
    with open(os.path.join(WORKSPACE, path), "w", encoding="utf-8") as f:
        f.write(content)

# ── references/score-band-table.md ───────────────────────────────────────────
# Official IELTS Academic Reading score-to-band conversion
# Key design: raw score 30 maps to band 7.0, raw score 29 maps to 6.5-7.0 boundary range
score_band_table = """\
# IELTS Academic Reading Score-to-Band Conversion Table

This table maps raw scores (0–40) to IELTS band scores for **Academic Reading only**.

> **Boundary rule**: If a raw score appears in the "Boundary" column, display the band as a range (e.g., `6.5-7.0`).

| Raw Score | Band  | Boundary? |
|-----------|-------|-----------|
| 40        | 9.0   | No        |
| 39        | 9.0   | No        |
| 38        | 8.5   | No        |
| 37        | 8.5   | No        |
| 36        | 8.0   | No        |
| 35        | 8.0   | No        |
| 34        | 7.5   | No        |
| 33        | 7.5   | No        |
| 32        | 7.0   | No        |
| 31        | 7.0   | No        |
| 30        | 7.0   | No        |
| 29        | 6.5   | Yes → display as 6.5-7.0 |
| 28        | 6.5   | No        |
| 27        | 6.5   | No        |
| 26        | 6.0   | Yes → display as 6.0-6.5 |
| 25        | 6.0   | No        |
| 24        | 6.0   | No        |
| 23        | 5.5   | Yes → display as 5.5-6.0 |
| 22        | 5.5   | No        |
| 21        | 5.5   | No        |
| 20        | 5.5   | No        |
| 19        | 5.5   | No        |
| 18        | 5.0   | Yes → display as 5.0-5.5 |
| 17        | 5.0   | No        |
| 16        | 5.0   | No        |
| 15        | 4.5   | Yes → display as 4.5-5.0 |
| 14        | 4.5   | No        |
| 13        | 4.5   | No        |
| 12        | 4.0   | Yes → display as 4.0-4.5 |
| 11        | 4.0   | No        |
| 10        | 4.0   | No        |
| 9         | 3.5   | Yes → display as 3.5-4.0 |
| 8         | 3.5   | No        |
| 7         | 3.0   | Yes → display as 3.0-3.5 |
| 6         | 3.0   | No        |
| 5         | 2.5   | Yes → display as 2.5-3.0 |
| 4         | 2.5   | No        |
| 3         | 2.0   | Yes → display as 2.0-2.5 |
| 2         | 2.0   | No        |
| 1         | 1.0   | No        |
| 0         | 1.0   | No        |

> Always use this table for Academic Reading. Do NOT use General Training conversion.
"""
with open(os.path.join(WORKSPACE, "references/score-band-table.md"), "w", encoding="utf-8") as f:
    f.write(score_band_table)

# ── references/error-taxonomy.md ─────────────────────────────────────────────
error_taxonomy = """\
# IELTS Reading Error Taxonomy

## Type A: Synonym/Paraphrase Miss
**Definition**: The student failed to recognize that a passage word and a question word are synonyms or paraphrases.
**Example**: Passage says "alleviate", question says "reduce".
**Marker**: [A-Synonym]

## Type B: Scope Error
**Definition**: The student selected an answer that is "roughly related" but adds information not present in the passage, or is too broad/narrow.
**Example**: Passage discusses one company; student chooses option about "all companies in the industry".
**Marker**: [B-Scope]

## Type C: Over-inference
**Definition**: The student inferred a conclusion the author did not explicitly state.
**Example**: Passage says "X may improve Y"; student concludes "X definitely improves Y".
**Marker**: [C-Inference]

## Type D: NOT GIVEN / FALSE Confusion
**Definition**: Student chose FALSE when the topic is simply not discussed (should be NOT GIVEN), or vice versa.
**Three-Step Method must be applied**: (1) Is the topic mentioned? (2) Does the passage agree or contradict? (3) Can you point to the exact sentence?
**Marker**: [D-NGvsFALSE]

## Type E: Word Limit Violation
**Definition**: Student's fill-in answer exceeded the stated word limit, or repeated words already in the question stem.
**Marker**: [E-WordLimit]

## Type F: Concessive Clause Misread
**Definition**: Student misread "however far..." or similar concessive constructions as causal/affirmative statements.
**Marker**: [F-Concessive]

## Type G: Distraction by True-but-Irrelevant Detail
**Definition**: Answer contains true information from passage but does not actually answer the specific question asked.
**Marker**: [G-Irrelevant]
"""
with open(os.path.join(WORKSPACE, "references/error-taxonomy.md"), "w", encoding="utf-8") as f:
    f.write(error_taxonomy)

# ── references/538-keywords-guide.md ─────────────────────────────────────────
keywords_guide = """\
# 538 IELTS Core Keywords Guide

## Frequency Rating System

| Rating | Category | Criteria |
|--------|----------|----------|
| ⭐⭐⭐ | Category 1 | Top 54 keywords — appear in ~90% of IELTS reading tests as question anchors |
| ⭐⭐  | Category 2 | 171 keywords — appear in ~60% of tests |
| ⭐    | Category 3 | 300+ keywords — lower frequency but still IELTS-relevant |
| —     | Not listed | Not in 538 list; cross-reference COCA 5000 for general academic frequency |

## Category 1 — Top 54 Keywords (⭐⭐⭐)

accelerate, acquire, adapt, affect, allocate, approach, assess, assume, attribute, benefit,
challenge, characteristic, circumstance, compensate, complex, concept, consequence,
construct, contribute, convert, create, demonstrate, develop, dimension, emerge, enable,
establish, evaluate, evidence, expand, facilitate, generate, identify, illustrate, implement,
indicate, innovative, integrate, involve, maintain, occur, perceive, perform, predict, process,
promote, prove, recognise, reduce, replace, require, respond, significant, specific, transfer

## Category 2 — 171 Keywords (⭐⭐)

abandon, accompany, accumulate, acknowledge, advocate, ambiguous, analyze, anticipate,
apparent, assert, bias, capacity, circumstantial, clarify, classify, cognitive, collaborate,
commence, commit, communicate, compare, compatible, compensate, compile, comprehensive,
confirm, conflict, contemporary, context, contradict, coordinate, correlate, criterion,
debate, decline, define, deliberate, deny, deplete, derive, detect, diverse, document,
dominate, eliminate, emphasize, encounter, ensure, environment, exclude, exhaust, exploit,
expose, external, facilitate, fluctuate, formulate, foundation, fundamental, generate,
global, gradual, hypothesis, imply, impose, inadequate, incorporate, inevitable, infer,
inherent, initiative, innovate, insight, interpret, investigate, justify, limitation, monitor,
motivate, mutual, neglect, objective, obtain, oppose, optimise, outcome, overcome, paradigm,
parameter, participate, phenomenon, portion, potential, precede, predominate, prohibit,
proportion, propose, pursue, quantify, rational, reinforce, reject, relevant, rely, resolve,
restrict, retain, reveal, revise, role, sequence, simulate, strategy, structure, subsequent,
sustain, synthesize, target, transform, transmit, valid, vary, verify, vulnerable, widespread

## Category 3 — 300+ Keywords (⭐)

abstract, access, accurate, adapt, adjacent, aggregate, allocate, alter, analogy, annual,
anthropology, apparent, application, arbitrary, archive, array, assembly, authority, aware,
bilateral, boundary, bracket, capacity, capture, catalog, cautious, coherent, coincide,
collective, compatible, complement, compile, concede, concise, confine, constant, construct,
consult, correlate, cycle, deduce, defer, depict, designate, detect, deviate, diagnose,
differentiate, digital, directive, discrete, distinguish, distribute, domain, duration,
dynamic, economy, edition, eliminate, empirical, encounter, encompass, enforce, enhance,
equilibrium, equivalent, estimate, eventual, evolve, exchange, exhibit, explicit, extract,
facilitate, finite, flexible, fluctuate, format, formulate, frequency, function, fundamental,
generate, hierarchy, implicit, induce, inherent, initiate, input, integrate, intervene,
isolate, mechanism, mediate, minimal, modify, negate, neutral, norm, notion, objective,
obscure, obtain, output, parallel, perceive, periodic, perspective, physical, policy,
principal, procedure, project, protocol, random, range, ratio, react, regulate, reinforce,
reject, relative, relocate, remove, represent, resource, restrict, reverse, revise, role,
scope, sector, select, shift, simulate, specify, stable, static, substitute, supplement,
survey, suspend, symbolic, technique, temporal, theoretical, trace, transmit, uniform,
unique, utilize, vary, virtual, visual, volume, widespread
"""
with open(os.path.join(WORKSPACE, "references/538-keywords-guide.md"), "w", encoding="utf-8") as f:
    f.write(keywords_guide)

# ── references/review-style-guide.md ─────────────────────────────────────────
style_guide = """\
# Review Style Guide

## Language
- Primary language: Chinese for explanations and annotations
- Keep English terms (e.g., TRUE/FALSE/NOT GIVEN, IELTS, Cambridge) in English
- Use 雅思 for IELTS in Chinese contexts

## Tone
- Blunt and direct — do not soften criticism of mistakes
- Action-oriented — every note must suggest what to do differently
- No fluff — avoid phrases like "good job" or "you're improving"

## Section Order (mandatory)
1. 📌 Score summary & alert box
2. ❌ Per-question error breakdown
3. 🔄 Synonym accumulation table
4. 📝 Vocabulary table
5. 💡 Recurring mistake tracker
6. 📊 Test scorecard (when full test data available)

## Synonym Table Column Order
Passage Expression | Question Expression | Chinese Meaning | Question Number

## Vocabulary Table Column Order
Word | Phonetic | Definition | Frequency Rating | Cambridge Appearance

## Recurring Mistake Tracker Format
List each pattern as: [Error Type Code] Description — Example from this passage

## Time Format
- Per-passage: MM:SS
- Total with breakdown: MM:SS+MM:SS+MM:SS=MM:SS
- Use 24-hour arithmetic (no AM/PM)
"""
with open(os.path.join(WORKSPACE, "references/review-style-guide.md"), "w", encoding="utf-8") as f:
    f.write(style_guide)

# ── assets/review-template.html ──────────────────────────────────────────────
review_template = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IELTS Reading Review</title>
<style>
  /* ── Base ── */
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    font-size: 15px; line-height: 1.7;
    color: #1a1a1a; background: #f8f8f8;
    padding: 40px 20px; max-width: 860px; margin: 0 auto;
  }
  h1 { font-size: 1.6em; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 24px; }
  h2 { font-size: 1.2em; color: #2c3e50; margin: 28px 0 12px; padding: 6px 12px;
       background: #eaf2fb; border-left: 4px solid #3498db; }
  h3 { font-size: 1em; color: #555; margin: 16px 0 6px; }

  /* ── Alert box ── */
  .alert-box {
    background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px;
    padding: 14px 18px; margin: 16px 0;
  }
  .alert-box .score-line { font-size: 1.3em; font-weight: bold; color: #e67e22; }
  .alert-box .core-problem { margin-top: 8px; color: #7d6608; }

  /* ── Error block ── */
  .error-block {
    background: #fff; border: 1px solid #e0e0e0; border-radius: 6px;
    padding: 14px 18px; margin: 12px 0;
  }
  .error-block .q-header { font-weight: bold; color: #c0392b; margin-bottom: 8px; }
  .error-block .source-sentence { background: #f9f9f9; border-left: 3px solid #ccc;
    padding: 8px 12px; margin: 8px 0; font-style: italic; color: #444; }
  .error-block .keyword-map { color: #27ae60; }
  .error-block .error-type { display: inline-block; background: #e74c3c; color: white;
    border-radius: 3px; padding: 1px 7px; font-size: 0.85em; margin: 4px 0; }
  .error-block .lesson { background: #eafaf1; border-left: 3px solid #27ae60;
    padding: 8px 12px; margin: 8px 0; }

  /* ── Tables ── */
  table { width: 100%; border-collapse: collapse; margin: 12px 0; }
  th { background: #2c3e50; color: white; padding: 8px 12px; text-align: left; }
  td { padding: 7px 12px; border-bottom: 1px solid #e0e0e0; }
  tr:nth-child(even) td { background: #f5f5f5; }

  /* ── Scorecard ── */
  .scorecard {
    background: #fff; border: 2px solid #3498db; border-radius: 8px;
    padding: 16px; margin: 16px 0; overflow-x: auto;
  }
  .scorecard table th { background: #3498db; }
  .progress-table table th { background: #27ae60; }
  .progress-analysis {
    background: #eaf8f1; border-left: 4px solid #27ae60;
    padding: 14px 18px; margin: 14px 0; border-radius: 0 6px 6px 0;
  }

  /* ── Feedback nudge ── */
  .feedback-nudge {
    margin-top: 40px; padding: 12px 18px;
    background: #fef9e7; border: 1px dashed #f1c40f; border-radius: 6px;
    color: #7d6608; font-size: 0.9em;
  }
</style>
</head>
<body>

<!-- SECTION 1: Score Summary -->
<section id="score-summary">
  <h2>📌 本次成绩概览</h2>
  <!-- Insert alert-box here -->
</section>

<!-- SECTION 2: Error Breakdown -->
<section id="error-breakdown">
  <h2>❌ 错题逐题分析</h2>
  <!-- Insert error-block elements here -->
</section>

<!-- SECTION 3: Synonym Table -->
<section id="synonym-table">
  <h2>🔄 同义词积累表</h2>
  <table>
    <thead>
      <tr>
        <th>原文表达</th>
        <th>题目表达</th>
        <th>中文释义</th>
        <th>题号</th>
      </tr>
    </thead>
    <tbody>
      <!-- Insert rows here -->
    </tbody>
  </table>
</section>

<!-- SECTION 4: Vocabulary Table -->
<section id="vocab-table">
  <h2>📝 词汇积累表</h2>
  <table>
    <thead>
      <tr>
        <th>单词</th>
        <th>音标</th>
        <th>释义</th>
        <th>频率等级</th>
        <th>剑桥出现记录</th>
      </tr>
    </thead>
    <tbody>
      <!-- Insert rows here -->
    </tbody>
  </table>
</section>

<!-- SECTION 5: Recurring Mistake Tracker -->
<section id="recurring-mistakes">
  <h2>💡 错误模式追踪</h2>
  <!-- Insert patterns here -->
</section>

<!-- SECTION 6: Scorecard (full test) -->
<section id="scorecard">
  <h2>📊 成绩单</h2>
  <!-- Insert scorecard and progress table here -->
</section>

<!-- Feedback Nudge -->
<div class="feedback-nudge">
  💡 如果这次复盘对你有帮助，可以去 <a href="https://github.com/dengjiawei1226/ielts-reading-review">GitHub 仓库</a> 点个 ⭐ Star，让更多雅思考生发现这个工具！
</div>

</body>
</html>
"""
with open(os.path.join(WORKSPACE, "assets/review-template.html"), "w", encoding="utf-8") as f:
    f.write(review_template)

# ── scripts/generate-pdf.js ───────────────────────────────────────────────────
generate_pdf_js = """\
// generate-pdf.js — PDF export via puppeteer-core
// Usage: node generate-pdf.js <input.html> <output.pdf>
const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

(async () => {
  const [,, inputHtml, outputPdf] = process.argv;
  if (!inputHtml || !outputPdf) {
    console.error('Usage: node generate-pdf.js <input.html> <output.pdf>');
    process.exit(1);
  }
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/chromium',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  const absolutePath = path.resolve(inputHtml);
  await page.goto('file://' + absolutePath, { waitUntil: 'networkidle0' });
  await page.pdf({
    path: outputPdf,
    format: 'A4',
    margin: { top: '2cm', bottom: '2cm', left: '2cm', right: '2cm' },
    displayHeaderFooter: false,
  });
  await browser.close();
  console.log('PDF saved to', outputPdf);
})();
"""
with open(os.path.join(WORKSPACE, "scripts/generate-pdf.js"), "w", encoding="utf-8") as f:
    f.write(generate_pdf_js)

# ── sessions/progress_history.json ────────────────────────────────────────────
# 5 prior test results for the cumulative progress table
progress_history = {
  "tests": [
    {
      "test_id": "剑4 T3",
      "p1": 7, "p2": 6, "p3": 3,
      "total": 16,
      "time_p1": "34:40", "time_p2": "42:53", "time_p3": "47:55",
      "total_time": "125:28",
      "band": "5.0",
      "date": "2024-10-05"
    },
    {
      "test_id": "剑4 T4",
      "p1": 7, "p2": 7, "p3": 5,
      "total": 19,
      "time_p1": "33:43", "time_p2": "30:59", "time_p3": "33:50",
      "total_time": "98:32",
      "band": "5.5",
      "date": "2024-10-12"
    },
    {
      "test_id": "剑5 T2",
      "p1": 8, "p2": 9, "p3": 2,
      "total": 19,
      "time_p1": "35:52", "time_p2": "36:23", "time_p3": "53:32",
      "total_time": "125:47",
      "band": "5.5",
      "date": "2024-10-19"
    },
    {
      "test_id": "剑5 T3",
      "p1": 11, "p2": 9, "p3": 6,
      "total": 26,
      "time_p1": "32:40", "time_p2": "39:34", "time_p3": "34:32",
      "total_time": "106:46",
      "band": "6.0-6.5",
      "date": "2024-10-26"
    },
    {
      "test_id": "剑5 T4",
      "p1": 11, "p2": 11, "p3": 7,
      "total": 29,
      "time_p1": "34:10", "time_p2": "35:32", "time_p3": "51:13",
      "total_time": "120:55",
      "band": "6.5-7.0",
      "date": "2024-11-02"
    }
  ]
}
with open(os.path.join(WORKSPACE, "sessions/progress_history.json"), "w", encoding="utf-8") as f:
    json.dump(progress_history, f, ensure_ascii=False, indent=2)

# ── The actual task input: Cambridge 17 Test 2 Passage 3 ─────────────────────
# Raw messy input that the agent will receive via the prompt
task_input = """\
# Cambridge 17 Test 2 Passage 3 — Task Input
## Source: Cambridge IELTS 17 Academic, Test 2, Passage 3
## Topic: The Psychology of Innovation

## Passage Excerpt (relevant sentences only)

[Q27-context] Despite the enormous appeal of innovation in theory, psychological research 
consistently shows that people have a "status quo bias" — a preference for things as they 
are. Organisations are no different: most claim to embrace change yet systematically 
undervalue novel ideas when encountered in practice.

[Q28-context] A study by Mueller et al. found that when people feel uncertain, they 
associate creativity with impracticality. The more uncertain a person felt, the more 
negatively they evaluated creative ideas — even when explicitly instructed to evaluate them 
positively.

[Q29-context] However far from reality the perfect innovative solution may seem, research 
demonstrates that organisations which tolerate ambiguity are significantly more likely to 
produce breakthrough products than those with rigid structures.

[Q30-context] Organisations that successfully innovate tend to create what psychologists 
call "psychological safety" — an environment in which individuals can propose ideas without 
fear of humiliation or reprimand. This safety is not simply "being nice"; it requires 
deliberate structural choices.

[Q31-context] The evidence suggests that intrinsic motivation — doing something because it 
is inherently interesting or satisfying — is more conducive to creative output than extrinsic 
rewards such as bonuses. Extrinsic rewards can, paradoxically, reduce creative performance 
by narrowing focus.

[Q32-context] Contrary to popular belief, solitary brainstorming consistently outperforms 
group brainstorming in generating a greater quantity and variety of ideas, largely because 
group settings introduce social pressures that inhibit expression.

[Q33-context] Most innovative breakthroughs are not the result of random inspiration but 
rather the product of extensive domain knowledge combined with the capacity to make unusual 
cross-domain connections.

## Questions & Answers

Questions 27–33: TRUE / FALSE / NOT GIVEN

Q27. Most organisations prefer existing practices to new ones.
Correct: TRUE    User's answer: TRUE    ✓ CORRECT

Q28. Mueller's study participants were not told to assess ideas positively.
Correct: FALSE   User's answer: NOT GIVEN    ✗ WRONG

Q29. Organisations that can accept uncertainty are more likely to innovate.
Correct: TRUE    User's answer: TRUE    ✓ CORRECT

Q30. Psychological safety depends entirely on managers being kind to employees.
Correct: FALSE   User's answer: FALSE   ✓ CORRECT (HARD — note synonym map)

Q31. Offering financial incentives always improves creative output.
Correct: FALSE   User's answer: NOT GIVEN   ✗ WRONG

Q32. Working alone generates more ideas than working in a group.
Correct: TRUE    User's answer: FALSE   ✗ WRONG

Q33. Creative breakthroughs require both specialised knowledge and broad thinking.
Correct: TRUE    User's answer: TRUE    ✓ CORRECT

## Passage Scores
P1: 13/14   P2: 10/12   P3: 10/14 (this passage — 3 wrong from Q27-33 range)

Wait — let me recount. Passage 3 actually had 14 questions total (Q27-40). 
The 3 wrong ones are Q28, Q31, Q32 as listed above. Final P3 score = 11/14.

## Timing
P1: 28:15, P2: 31:44, P3: 38:03

## Test: Cambridge 17 Test 2 (剑17 T2)
Full test total: P1(13) + P2(10) + P3(11) = 34/40

## Key Vocabulary from passage (agent must look up in 538 guide)
- innovate / innovative
- systematic / systematically  
- ambiguity
- intrinsic
- conducive
- paradoxically / paradox
- domain

## User reflection
Q32 really got me — I thought "consistently outperforms" meant it was too extreme to be TRUE. 
Q31 I thought the passage said rewards CAN reduce performance but didn't say "always" so I 
thought it was NOT GIVEN. Q28 — I just missed this one completely.
"""
with open(os.path.join(WORKSPACE, "sessions/cambridge17/c17t2p3_raw_input.txt"), "w", encoding="utf-8") as f:
    f.write(task_input)

print("Workspace initialized successfully.")
print(f"Key files created:")
print(f"  - references/score-band-table.md  (raw score 34 -> band 7.5, no boundary)")
print(f"  - references/538-keywords-guide.md")
print(f"  - references/error-taxonomy.md")
print(f"  - assets/review-template.html")
print(f"  - sessions/progress_history.json  (5 prior tests)")
print(f"  - sessions/cambridge17/c17t2p3_raw_input.txt  (task input)")