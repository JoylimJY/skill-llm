import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── directory structure (distractor files) ──────────────────────────────────
dirs = [
    "project/data/raw",
    "project/data/processed",
    "project/analysis/scripts",
    "project/analysis/outputs",
    "project/manuscript/figures",
    "project/manuscript/tables",
    "project/literature/pdfs",
    "project/literature/notes",
    "project/admin/irb",
    "project/admin/correspondence",
    "references/examples",
    "references",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# distractor files
distractor_files = {
    "project/data/raw/participants_raw.csv": (
        "id,age,gender,condition,trail_making_score,stroop_score,sleep_hours\n"
        "1,19,F,control,42,88,8.1\n"
        "2,22,M,deprived,61,72,3.9\n"
        "3,34,F,deprived,58,69,4.2\n"
        "4,45,M,control,40,91,7.8\n"
        "103,21,F,deprived,77,61,3.5\n"
    ),
    "project/data/processed/summary_stats.txt": (
        "Trail Making Test (TMT-B): deprived M=61.3 (SD=9.1), control M=40.8 (SD=7.4), t(98)=12.4, p<0.001\n"
        "Stroop Interference: deprived M=71.2 (SD=11.3), control M=89.7 (SD=8.6), t(98)=9.8, p<0.001\n"
        "Gender subgroup (female, deprived vs control): TMT-B p=0.41 (ns)\n"
        "Age interaction: F(1,96)=5.62, p=0.020, eta^2=0.055\n"
    ),
    "project/analysis/scripts/anova.py": (
        "# Two-way ANOVA for sleep x age interaction\nimport scipy.stats\n# placeholder\n"
    ),
    "project/analysis/scripts/descriptives.py": (
        "# Compute means and SDs per condition\n# placeholder\n"
    ),
    "project/analysis/outputs/anova_results.json": (
        '{"interaction_F": 5.62, "interaction_p": 0.020, "eta_sq": 0.055}\n'
    ),
    "project/manuscript/figures/fig1_tmt_boxplot.png.placeholder": "binary placeholder\n",
    "project/manuscript/tables/table1_demographics.csv": (
        "variable,deprived,control\nN,50,50\nMean Age,24.3,23.9\nFemale %,54,52\n"
    ),
    "project/literature/notes/harrison2000_notes.txt": (
        "Harrison & Horne (2000): 36h TSD impairs prefrontal tasks.\n"
        "Effect sizes moderate; younger adults more resilient in some measures.\n"
    ),
    "project/literature/notes/lim2010_notes.txt": (
        "Lim & Dinges (2010): meta-analysis of 70 studies; sustained attention most impaired.\n"
        "Age-moderated effects not examined systematically.\n"
    ),
    "project/literature/notes/wimmer2012_notes.txt": (
        "Wimmer et al. (2012): gender differences in sleep deprivation response - females show \n"
        "attenuated cognitive decline on some measures. Mechanism unclear.\n"
    ),
    "project/admin/irb/approval_notice.txt": (
        "IRB approval #2021-0482. Exempt category 2. Renewal due 2024-01.\n"
    ),
    "project/admin/correspondence/reviewer_comments.txt": (
        "Reviewer 2: Discussion lacks engagement with the null finding in the female subgroup.\n"
        "Reviewer 1: Limitations section needs more specificity about generalizability.\n"
    ),
    "references/examples/placeholder.txt": (
        "Sample outputs directory - see skill documentation for examples.\n"
    ),
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """---
name: discussion-section-architect
description: Structures and writes discussion sections for academic papers and research reports. Use when writing a discussion section, interpreting research results, connecting findings to existing literature, addressing study limitations, synthesizing conclusions, or drafting any part of an academic discussion. Helps researchers organize arguments, contextualize data, and produce clear, publication-ready discussion prose.
allowed-tools: "Read Write Bash Edit"
license: MIT
metadata:
  skill-author: AIPOCH
  version: "1.0"
---

# Discussion Section Architect

## Quick Start

1. Provide your **research question**, **key results**, and any **prior literature** you want to reference.
2. Choose a structure (see workflows below).
3. Generate a draft discussion section with clearly organized subsections.
4. Run the **Draft → Revise loop** (see below).

---

## Core Capabilities

### 1. Interpret and Contextualize Results

- State whether results support or contradict the original hypothesis.
- Explain unexpected findings with reasoned interpretations.
- Quantify effect sizes or patterns when relevant.

**Example prompt input:**
```
Results: Group A showed a 23% reduction in symptom severity (p=0.003) vs. control.
Hypothesis: Intervention would reduce symptom severity.
Task: Interpret this result for the discussion section.
```

**Example output excerpt:**
```
The 23% reduction in symptom severity (p=0.003) supports the primary hypothesis.
This effect size is clinically meaningful and consistent with the mechanistic
rationale proposed in the introduction...
```

---

### 2. Connect Findings to Existing Literature

- Identify studies that corroborate the findings.
- Highlight where results diverge from prior literature and offer explanations.
- Use hedged academic language appropriate to the field.

**Example:**
```
Finding: Effect was stronger in older participants.
Literature: Smith et al. (2019) found age-moderated responses in a similar cohort.
Task: Connect finding to literature.
```

**Output:**
```
The age-moderated effect aligns with Smith et al. (2019), who reported attenuated
responses in younger adults. One possible explanation is differential receptor
sensitivity across age groups, as suggested by...
```

---

### 3. Address Limitations

Draft a limitations subsection that is honest but does not undermine the contribution:

```
Limitation: [Describe constraint]
Impact: [How it affects interpretation]
Mitigation / Future direction: [How it could be addressed]
```

---

### 4. Synthesize Conclusions

Generate a closing paragraph that:

- Restates the core finding in plain language.
- States the theoretical or practical contribution.
- Ends with a forward-looking statement about implications or next steps.

---

## Recommended Discussion Structure

```
1. Opening: Restate the research question and summarize the key finding (2–3 sentences).
2. Interpretation: Explain what the results mean mechanistically or theoretically.
3. Comparison to Literature: Agree/contrast with prior studies; explain divergences.
4. Implications: Theoretical contributions and/or practical applications.
5. Limitations: Honest scope boundaries with future directions.
6. Conclusion: Synthesis and forward-looking close.
```

---

## Draft → Revise Loop

Use this iterative workflow after generating an initial draft:

**Step 1 — Draft**: Generate the full discussion section using the structure above.

**Step 2 — Check**: Review against the checklist:
- [ ] Each finding from the Results section is explicitly addressed.
- [ ] Claims are supported by citations or logical reasoning — not stated as facts.
- [ ] Unexpected or null results are acknowledged and interpreted.
- [ ] Limitations are stated without dismissing the study's contribution.
- [ ] No new data or results are introduced in the discussion.
- [ ] Hedged language used appropriately (e.g., "suggests," "indicates," "may reflect").
- [ ] Conclusion ties back to the original research question.

**Step 3 — Revise**: For each failed checklist item, revise only the affected paragraph(s).

**Step 4 — Re-check**: Re-run the checklist on revised paragraphs to confirm resolution before finalizing.

---

## References

- `references/guide.md` - Detailed documentation
- `references/examples/` - Sample inputs and outputs

---

**Skill ID**: 950 | **Version**: 1.0 | **License**: MIT
"""

(workspace / "SKILL.md").write_text(skill_md)

# ── MAIN INPUT FILE the agent must read and process ──────────────────────────
research_brief = """# Research Brief: Sleep Deprivation & Cognitive Flexibility Study

## Research Question
Does acute partial sleep deprivation (≤5 hours/night for 3 consecutive nights)
impair cognitive flexibility in university students aged 18–50, and does this
effect vary by age or gender?

## Hypotheses
- H1: Sleep-deprived students will perform worse on cognitive flexibility tasks
  (Trail Making Test B, Stroop task) than rested controls.
- H2: The effect will be uniform across age groups and genders.

## Key Results
1. Sleep-deprived participants scored significantly higher (worse) on TMT-B
   compared to controls: M=61.3 (SD=9.1) vs. M=40.8 (SD=7.4), t(98)=12.4, p<0.001.
2. Stroop interference scores were significantly lower in the deprived group:
   M=71.2 (SD=11.3) vs. M=89.7 (SD=8.6), t(98)=9.8, p<0.001. (Higher score = better inhibitory control.)
3. A significant sleep-deprivation × age interaction was found: F(1,96)=5.62,
   p=0.020, eta²=0.055, indicating that older participants (30–50) showed
   larger cognitive deficits than younger participants (18–29).
4. NULL FINDING: No significant effect was found for the gender subgroup analysis
   (female deprived vs. female control on TMT-B, p=0.41).

## Prior Literature to Reference
- Harrison & Horne (2000): Demonstrated that 36-hour total sleep deprivation
  severely impairs prefrontal-dependent tasks; effects were more pronounced in
  older adult samples.
- Lim & Dinges (2010): Meta-analysis (70 studies) showed sustained attention is
  most consistently impaired; noted that age-moderated effects require further study.
- Wimmer et al. (2012): Reported that females may show attenuated cognitive
  decline under sleep deprivation on certain tasks, though the mechanism is unclear.

## Study Limitations (raw notes from PI)
- Sample restricted to university students — may not generalize to working adults.
- Self-reported sleep duration (actigraphy not used in all participants).
- Cross-sectional design; no within-subject tracking of cognitive change.

## Your Task
Write the full discussion section for the manuscript. Save it as discussion_section.md
in the project/manuscript/ directory.
"""

(workspace / "project/manuscript/research_brief.md").write_text(research_brief)

# ── references/guide.md ──────────────────────────────────────────────────────
guide_md = """# Discussion Section Architect — Detailed Guide

## Section-by-Section Guidance

### Opening
- 2–3 sentences max.
- Restate the research question (do not copy verbatim from the introduction).
- Name the single most important finding.

### Interpretation
- Work through each result systematically.
- Use hedged language: "suggests," "may indicate," "is consistent with."
- Do not introduce new data here.

### Comparison to Literature
- For each key finding, cite at least one prior study.
- When results diverge from prior work, provide a theoretical explanation.

### Implications
- Distinguish theoretical from practical contributions.
- Avoid overclaiming.

### Limitations
**Required format per limitation:**
```
Limitation: [one-sentence description]
Impact: [how this constrains interpretation]
Mitigation / Future direction: [what could address this]
```

### Conclusion
- 1 paragraph, 4–6 sentences.
- Restate the research question in plain language.
- State the primary contribution.
- End with a forward-looking sentence.
"""

(workspace / "references/guide.md").write_text(guide_md)

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")