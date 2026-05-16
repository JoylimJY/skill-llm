import os
import random

random.seed(42)

workspace = "/workspace"

# ── directory structure ──────────────────────────────────────────────
dirs = [
    "rules",
    "course_materials",
    "course_materials/past_exams",
    "course_materials/lecture_slides",
    "course_materials/assignments",
    "notes_drafts",
    "notes_drafts/scratch",
    "references",
    "references/textbooks",
    "tools",
    "tools/scripts",
    "exports",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files (at least 10) ──────────────────────────────────

# 1. Old partial notes (wrong format, no traceability)
with open(os.path.join(workspace, "notes_drafts/scratch/old_notes.md"), "w") as f:
    f.write("""# Old DS Notes
- Binary trees have nodes
- Hash tables use buckets
- Dijkstra finds shortest path
(incomplete, no examples)
""")

# 2. A red-herring 'study_guide.txt' with bad formatting
with open(os.path.join(workspace, "notes_drafts/study_guide_v0.txt"), "w") as f:
    f.write("""STUDY GUIDE DRAFT
================
Trees: important
Hashing: important
Graphs: very important
DP: memorize stuff
[Not usable - just placeholders]
""")

# 3. Past exam PDF placeholder (text file pretending to be a PDF)
with open(os.path.join(workspace, "course_materials/past_exams/midterm_2023.txt"), "w") as f:
    f.write("""MIDTERM 2023 - CS302 Data Structures
Q1: Explain AVL rotations (15 pts)
Q2: Implement a hash function (20 pts)
Q3: Trace Dijkstra on a graph (25 pts)
[Answers not provided]
""")

# 4. Assignment stubs
with open(os.path.join(workspace, "course_materials/assignments/hw3_graphs.py"), "w") as f:
    f.write("""# HW3: Graph Algorithms
# TODO: Implement BFS and DFS
def bfs(graph, start):
    pass  # student fills in

def dfs(graph, start):
    pass  # student fills in
""")

# 5. Lecture slide placeholder
with open(os.path.join(workspace, "course_materials/lecture_slides/lec08_dp_slides.txt"), "w") as f:
    f.write("""Lecture 8: Dynamic Programming
Slide 1: Overview
Slide 2: Fibonacci example (naive)
Slide 3: Memoization
Slide 4: Tabulation
[Slides not in PDF format - use topic outline instead]
""")

# 6. A confusing 'quick_ref.md' with wrong format (prose style - the anti-pattern)
with open(os.path.join(workspace, "notes_drafts/scratch/quick_ref_bad.md"), "w") as f:
    f.write("""# Quick Reference (BAD EXAMPLE)
## Hash Tables
Hash tables are data structures that use a hash function to map keys to array positions.
The load factor determines when to resize. Collision resolution can be done via chaining
or open addressing. The average time complexity for insert, delete, and search is O(1).

## Binary Trees
A binary tree is a tree where each node has at most two children called left and right.
Binary search trees maintain the BST property: left < root < right for all nodes.
""")

# 7. References bibliography
with open(os.path.join(workspace, "references/textbooks/reading_list.txt"), "w") as f:
    f.write("""Required Textbooks:
- CLRS: Introduction to Algorithms (Cormen et al.)
- Sedgewick: Algorithms, 4th Edition
- Skiena: The Algorithm Design Manual

Online Resources:
- https://visualgo.net (algorithm visualizations)
- https://leetcode.com (practice problems)
""")

# 8. Tools/scripts stub
with open(os.path.join(workspace, "tools/scripts/convert_notes.sh"), "w") as f:
    f.write("""#!/bin/bash
# Placeholder conversion script
echo "Note conversion not yet implemented"
""")

# 9. Course info file
with open(os.path.join(workspace, "course_materials/course_info.txt"), "w") as f:
    f.write("""CS302: Data Structures and Algorithms
Semester: Fall 2024
Instructor: Prof. Martinez
Office Hours: Mon/Wed 2-4pm
Final Exam: December 15, 2024 9:00 AM
Exam covers: ALL topics from weeks 1-14
""")

# 10. Incomplete synthesis attempt
with open(os.path.join(workspace, "notes_drafts/synthesis_attempt.md"), "w") as f:
    f.write("""# Synthesis Attempt (INCOMPLETE)
## Trees
- BST, AVL, Red-Black (not finished)
## Hash Tables
- (TODO)
## Graphs
- (TODO)
## DP
- (TODO)
[This was abandoned - needs full rework]
""")

# 11. Git-like log distractor
with open(os.path.join(workspace, "exports/conversion_log.txt"), "w") as f:
    f.write("""Export log:
2024-11-01: attempted pandoc conversion - failed (no source file)
2024-11-15: study-notes.md not found
2024-12-01: export aborted
""")

# ── RULE FILES (the skill references these as already existing) ──────

# rules/phase-intake.md
with open(os.path.join(workspace, "rules/phase-intake.md"), "w") as f:
    f.write("""# Phase 0: Intake Workflow

## Purpose
Gather all necessary information in a single exchange before proceeding to processing.

## Required Information to Collect (Single Exchange)
1. **Input type**: PDFs, topic list, or course name
2. **Study tier**: 
   - "Quick Review" — summary only, no appendices
   - "Deep Dive" — full notes, no appendices  
   - "Exam Ready" — full notes + Quick Reference + Exam Q&A appendices
3. **Priority topics**: Any concepts the user wants extra depth on
4. **Output format**: Markdown only, or also PDF export

## Tier Rules
- "Exam Ready" tier: MUST produce study-notes.md, quick-reference.md, AND exam-qa.md
- "Deep Dive" tier: MUST produce study-notes.md only
- "Quick Review" tier: MUST produce study-notes.md (abbreviated)

## Intake Output
Summarize confirmed parameters:
```
Intake confirmed:
- Input: [type]
- Tier: [tier]
- Priority topics: [list or "none"]
- Output: [formats]
```
Then proceed immediately to the appropriate phase.

## Single Exchange Constraint
Do NOT ask follow-up questions. Make reasonable assumptions for anything not stated.
Default tier: "Exam Ready" if user mentions exam, final, midterm, or quiz preparation.
Default priority topics: none, unless explicitly stated.
""")

# rules/phase-extract.md
with open(os.path.join(workspace, "rules/phase-extract.md"), "w") as f:
    f.write("""# Phase 1: Extract

## Purpose
Extract all content from PDF files using the /pdf skill.

## Output
For each PDF: `lecture-XX-extract.md`

## Format
- Page-aligned extraction: note the page number for every major concept
- Dense and compact — no padding, no meta-commentary
- Every concept: name, page number, brief definition

## Skipping Phase 1
If input is a topic list (not PDFs), skip directly to Phase 2.
""")

# rules/phase-synthesize.md
with open(os.path.join(workspace, "rules/phase-synthesize.md"), "w") as f:
    f.write("""# Phase 2: Synthesize

## Purpose
Build a unified knowledge map from extracted lecture content or topic list.

## Output: course-synthesis.md

## Structure
- Group related concepts across sources
- Identify prerequisites and dependencies
- Note section numbers (topic list) or page/lecture numbers (PDFs)
- Flag gaps and contradictions

## Traceability Requirement
EVERY concept must be tagged with its source location:
- Topic list: [Section X.Y]
- PDF: [Lecture N, p.Z]

## Output Format
```
# Course Synthesis: [Course Name]

## Concept Cluster: [Name]
### [Concept]
- Source: [Section/Lecture ref]
- Definition: ...
- Dependencies: ...
- Related: ...
```
""")

# rules/phase-expand.md
with open(os.path.join(workspace, "rules/phase-expand.md"), "w") as f:
    f.write("""# Phase 3: Expand

## Purpose
Enrich course content with external knowledge or fill curriculum gaps.

## Output: course-expansion.md

## Two Modes

### Mode A: With web access
- Search for authoritative sources
- Cite real URLs, paper titles, authors

### Mode B: Without web access (DEFAULT in isolated environments)
- Every claim NOT directly from the course material MUST be tagged: `[Standard curriculum knowledge]`
- NO invented URLs, paper titles, or author names
- Draw on well-established CS curriculum knowledge only
- Mark everything added beyond the source material

## Expansion Scope
- Worked examples beyond what the source provides
- Common implementation patterns
- Connections to industry practice
- Historical context (if well-established)
""")

# rules/phase-study.md
with open(os.path.join(workspace, "rules/phase-study.md"), "w") as f:
    f.write("""# Phase 4: Study Materials

## Output Files
- `study-notes.md` — always produced
- `quick-reference.md` — Exam Ready tier only
- `exam-qa.md` — Exam Ready tier only

## study-notes.md Structure

### Header
```
# Study Notes: [Course Name]
**Tier:** [tier]
**Generated:** [date]
**Priority Topics:** [list]
```

### Per-Concept Block (MANDATORY for every non-trivial concept)
```
## [Concept Name]
**Source:** [Section X.Y or Lecture N p.Z]

### What it is
[Definition — instructor's phrasing first, then your own]

### Intuition
[Why it exists, what problem it solves]

### Formal Treatment
[LaTeX formulas in $...$ or $$...$$, or code blocks]

### Worked Example
[Concrete, step-by-step — MANDATORY, never omit]

### Connections
**Requires:** [prerequisites]
**Enables:** [what this unlocks]

### Common Misconceptions
[At least one misconception with correction]
```

### Priority Topic Treatment
Priority topics receive ALL of the above PLUS:
- Extended worked examples (at least 2)
- Deeper formal treatment
- Additional edge cases
- Must appear in quick-reference.md AND exam-qa.md

## Step 6a: quick-reference.md (Exam Ready only)

### Format Rules (STRICT)
- Title: `# Quick Reference: [Course Name]`
- One section per major topic cluster
- **ONE LINE PER ENTRY MAXIMUM** — no prose, no multi-line explanations
- Format: `**[Term]**: [ultra-brief definition or formula]`
- Priority topics get a `★` prefix: `★ **[Term]**: ...`
- All priority topics MUST appear here

### Example
```
# Quick Reference: CS302 Data Structures

## Trees
**BST Property**: left < node < right, enables O(log n) search
★ **AVL Rotation**: rebalancing op; 4 types: LL, RR, LR, RL

## Hash Tables
**Load Factor**: n/m; resize when > 0.75 typically
```

## Step 6b: exam-qa.md (Exam Ready only)

### Format Rules (STRICT)
- Title: `# Exam Q&A: [Course Name]`
- Minimum 3 questions per major topic
- Each question: multiple choice, short answer, or worked problem
- **Every answer MUST cite source location**: `[Source: Section X.Y]` or `[Source: Lecture N]`
- Priority topics: minimum 5 questions each, marked with `★`
- Format:
```
## [Topic]

**Q1: [Question text]**
> **A:** [Answer]  
> [Source: Section X.Y]

★ **Q2: [Priority topic question]**
> **A:** [Answer]  
> [Source: Section X.Y]
```
""")

# rules/templates.md
with open(os.path.join(workspace, "rules/templates.md"), "w") as f:
    f.write("""# Format-Agnostic Writing Rules

## Markdown Standards
- Use ATX headers (# ## ###), not Setext
- Fenced code blocks with language tag: ```python, ```java, etc.
- LaTeX inline: $formula$, block: $$formula$$
- Bold for terms: **term**
- Tables: GFM pipe tables

## Density Rules
- No padding phrases ("As we can see...", "It is worth noting...")
- No repeated meta-commentary between sections
- Intermediate files (extracts, synthesis): maximum density
- Study notes: density balanced with readability

## Structure
- Every file starts with a YAML-like header block
- Sections separated by horizontal rules (---) at major boundaries only
""")

# rules/pdf-export.md
with open(os.path.join(workspace, "rules/pdf-export.md"), "w") as f:
    f.write("""# PDF Export Configuration

## Tool: pandoc

## Base Command
```bash
pandoc input.md -o output.pdf --pdf-engine=xelatex
```

## Font Configuration
- Default body font: --variable mainfont="DejaVu Serif"
- Monospace: --variable monofont="DejaVu Sans Mono"
- Math: --variable mathfont="STIX Two Math"

## CJK Handling
If content contains Chinese/Japanese/Korean characters:
- Add: --variable CJKmainfont="Noto Serif CJK SC"
- Add: -V lang=zh or -V lang=ja as appropriate

## Full Command (with math support)
```bash
pandoc input.md -o output.pdf \\
  --pdf-engine=xelatex \\
  --variable mainfont="DejaVu Serif" \\
  --variable monofont="DejaVu Sans Mono" \\
  -V geometry:margin=1in \\
  --toc
```
""")

# rules/subject-coverage.md
with open(os.path.join(workspace, "rules/subject-coverage.md"), "w") as f:
    f.write("""# Subject Coverage and Gap Analysis

## Live Search Strategy (when web access available)
1. Search for "[course topic] university syllabus"
2. Cross-reference with top 3 CS textbooks for the area
3. Identify topics present in curriculum but not in provided materials

## Offline Gap Analysis (no web access)
1. Compare provided topics against standard CS curriculum
2. Flag missing prerequisites
3. Note standard topics typically adjacent to covered material
4. Mark all inferences as [Standard curriculum knowledge]

## Coverage Tiers
- Core: Must be in study-notes.md
- Supporting: Should be mentioned with brief explanation  
- Adjacent: Flag as "see also" with [Standard curriculum knowledge] tag
""")

# rules/changelog.md
with open(os.path.join(workspace, "rules/changelog.md"), "w") as f:
    f.write("""# Changelog

## v2.0.0
- Added Exam Ready tier with quick-reference.md and exam-qa.md outputs
- Mandatory worked examples for every non-trivial concept
- [Standard curriculum knowledge] tagging for offline expansion
- Priority topic deeper treatment + appendix inclusion
- Single-exchange intake constraint

## v1.5.0
- Added PDF export via pandoc
- CJK font support

## v1.0.0
- Initial release: basic study notes generation
""")

# ── THE MAIN INPUT: topic outline ────────────────────────────────────
with open(os.path.join(workspace, "topic_outline.txt"), "w") as f:
    f.write("""CS302: Data Structures and Algorithms — Final Exam Topic Outline
================================================================

Section 1: Trees
  1.1 Binary Trees and Binary Search Trees
      - BST property, traversals (inorder, preorder, postorder)
      - Search, insert, delete operations
      - Time complexity analysis

  1.2 AVL Trees (Self-Balancing BST)
      - Balance factor, height property
      - Rotations: LL, RR, LR, RL cases
      - Insertion and rebalancing procedure

  1.3 Red-Black Trees
      - Properties (coloring rules)
      - Comparison with AVL trees
      - Use in std::map / TreeMap

Section 2: Hash Tables
  2.1 Hash Functions
      - Division method, multiplication method
      - Properties of good hash functions

  2.2 Collision Resolution
      - Chaining (separate chaining)
      - Open addressing: linear probing, quadratic probing, double hashing

  2.3 Load Factor and Resizing
      - Load factor α = n/m
      - Amortized analysis of resizing
      - Expected time complexity

Section 3: Graph Algorithms
  3.1 Graph Representations
      - Adjacency matrix vs adjacency list
      - Space and time trade-offs

  3.2 Traversals
      - BFS: queue-based, level-order, shortest path in unweighted graph
      - DFS: stack/recursion, discovery/finish times

  3.3 Shortest Path Algorithms
      - Dijkstra's Algorithm (PRIORITY TOPIC)
      - Bellman-Ford: handles negative edges
      - Floyd-Warshall: all-pairs shortest path

  3.4 Minimum Spanning Trees
      - Kruskal's Algorithm: union-find
      - Prim's Algorithm: greedy, priority queue

Section 4: Dynamic Programming
  4.1 DP Fundamentals (PRIORITY TOPIC)
      - Optimal substructure, overlapping subproblems
      - Memoization (top-down) vs tabulation (bottom-up)
      - Identifying DP problems

  4.2 Classic DP Problems
      - Fibonacci (baseline example)
      - 0/1 Knapsack Problem
      - Longest Common Subsequence (LCS)
      - Matrix Chain Multiplication

  4.3 DP on Sequences and Strings
      - Edit distance (Levenshtein)
      - Coin change problem
      - Rod cutting problem
""")

# ── Intake parameters file (simulates what the user communicated) ────
with open(os.path.join(workspace, "intake_params.txt"), "w") as f:
    f.write("""User request summary (for agent reference):
- Input: topic_outline.txt (topic list format, NOT PDFs)
- Study tier: Exam Ready (user is preparing for final exam)
- Priority topics: Dijkstra's Algorithm, Dynamic Programming Fundamentals
- Output: Markdown files
- Course: CS302 Data Structures and Algorithms
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("/workspace"):
    for fn in files:
        path = os.path.join(root, fn)
        print(f"  {path}")