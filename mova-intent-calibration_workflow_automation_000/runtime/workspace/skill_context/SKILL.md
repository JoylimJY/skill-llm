---
name: mova-intent-calibration
description: Transform a raw user request into a clear, bounded, testable, and responsibility-bearing intent through structured crystallization. Use before any complex task, contract creation, or execution. Trigger when the user says "I want to", "help me think through", "define the task", or when the task scope is unclear or underdefined.
license: MIT-0
---

> **Ecosystem Skill** — Supports building and managing the MOVA ecosystem. Requires the `openclaw-mova` plugin.

# MOVA Intent Crystallization

Transform a raw user request into an explicit, bounded, testable, and responsibility-bearing intent — ready for formalization, execution, or contract creation.

This is not a form-filling exercise. This is a guided thinking process: expand the solution space, compare real alternatives, expose trade-offs, and require the user to consciously own every decision.

---

## Core Principles

1. Do not rush to fix the first plausible framing.
2. Always expand the solution space before narrowing it.
3. Present materially different options — not superficial variants of the same one.
4. Give a recommendation with full argumentation, not a short preference.
5. Show the trade-off of the recommendation.
6. Force the user to state the choice in their own words.
7. Make the user accept the cost, limits, and responsibility of the choice.
8. Separate facts, assumptions, constraints, decisions, and uncertainties.
9. If the user's intent is underdefined, do not proceed to execution.
10. The result must be explicit, bounded, testable, and owned by the user.

---

## When to trigger

Activate when the user:
- Describes something they want but the scope is unclear
- Says "I want to...", "help me...", "let me think through...", "plan this out"
- Is about to start a complex task or MOVA workflow
- Asks to formalize, define, or pre-contract a task

**Before starting**, say:

> "Let me help you crystallize this intent before we act on it. We'll go through 9 structured steps — each one expands your options, then forces a conscious choice. You own every decision. Ready?"

Wait for confirmation.

---

## Response Pattern (apply at every step)

At every step, use this structure exactly:

### 1. Observation
State briefly:
- what is already clear
- what remains unclear
- why the gap matters for this task

### 2. Option Space
Present 4–6 **materially different** options or framings. Options must differ in logic, not just wording. Make the user think.

### 3. Analysis
For each option:
- what it gives
- what it sacrifices
- when it is suitable
- when it breaks down

### 4. Recommendation
Provide a full recommendation including:
- why this is the best current choice
- why the alternatives are weaker for this task
- what trade-off is being chosen
- what responsibility the user accepts

### 5. User Fixation
Do not accept only a number. Require the user to confirm in their own words:
- what they choose
- why they choose it
- what they consciously accept or give up

Preferred formula:
> I choose X because for me Y is more important than Z.
> I understand that by choosing this I give up A and accept the risk of B.

---

## Step 0 — Problem Framing

**Goal:** Determine what kind of problem is actually being solved before choosing a solution path.

The initial request usually describes a wish, a symptom, or the first imagined solution — not the actual problem structure.

**Typical framing options:**
- A result-definition problem (we don't yet know what success looks like)
- A diagnosis problem (we don't yet know what is actually broken)
- A planning problem (we know the goal but not the path)
- A discipline/execution problem (the plan exists but is not being followed)
- A selection/filtering problem (we need to choose from known options)
- A coordination/delegation problem (clarity about who decides what)
- Custom

**User fixation:**
> I understand this task primarily as a task about ...

---

## Step 1 — Outcome

**Goal:** Convert desire into an observable result.

Distinguish between:
- artifact creation (something must exist that didn't before)
- state change (something must be different)
- behavior change (someone must act differently)
- filtering/prioritization (a set must be narrowed or ranked)
- decision preparation (a choice must be ready for approval)

**Typical outcome classes:**
- Create an artifact
- Reach a measurable state
- Change behavior
- Select or filter
- Rank or prioritize
- Prepare a decision for approval
- Custom

**User fixation:**
> I do not want merely ...
> I want specifically ...

---

## Step 2 — Reality

**Goal:** Force explicit recognition of the actual informational basis of the task.

Separate:
- known facts
- estimates
- assumptions
- unknowns
- missing but necessary inputs

**Typical reality axes:**
- Goal only
- Goal + current state
- Goal + current state + weak zones
- Goal + current state + environmental constraints
- Goal + current state + evidence/history
- Custom

**User fixation:**
> I accept that this task will be built on the following inputs ...

---

## Step 3 — Alternatives

**Goal:** Expand the solution space before fixing the core logic.

Generate 3–5 materially different strategies — not cosmetic variants of one strategy.

**Typical strategy classes:**
- Rigid structured plan
- Adaptive plan with feedback loops
- Scenario-driven approach (prepare for 2–3 futures)
- Deficit-driven approach (fix the weakest link first)
- Outcome-driven approach (start from the end state, work backward)
- Hybrid approach
- Custom

**User fixation:**
> I choose the strategy ... because for me ... matters more than ...

---

## Step 4 — Verification

**Goal:** Make the intent testable.

Present multiple verification modes and expose weak verification traps.

**Typical verification types:**
- Artifact exists (weakest — doesn't prove quality)
- Process was completed (proves effort, not result)
- Measurable behavior changed
- External review confirms adequacy
- Automatic rule-based validation
- Combined verification (recommended for important tasks)
- Custom

**User fixation:**
> I will consider this task complete if ...

---

## Step 5 — Constraints

**Goal:** Turn the intent into something realistic and executable.

Separate:
- hard constraints (cannot be violated under any circumstances)
- soft preferences (desirable but negotiable)
- hidden conflicting constraints (often the most dangerous)

**Typical constraint groups:**
- Time
- Resources
- Legal/ethical boundaries
- Cognitive load
- Emotional sustainability
- Risk tolerance
- Output format
- Scope boundaries
- Custom

**User fixation:**
> No matter what solution is chosen, the following constraints cannot be violated ...

---

## Step 6 — Decision Rights

**Goal:** Define the boundaries of agency, autonomy, and responsibility.

Separate:
- what the human must decide (cannot be delegated)
- what the system may suggest (advisory only)
- what the system may decide autonomously (within defined guardrails)
- what requires explicit confirmation before action

**Typical decision rights zones:**
- Human decides criteria, system executes
- Human approves final output only
- System performs preliminary filtering, human selects
- System adapts locally within guardrails
- System acts autonomously within a limited, pre-agreed zone
- Custom

**User fixation:**
> The human must decide ...
> The system may decide ...

---

## Step 7 — Uncertainty

**Goal:** Make assumptions and uncertainty explicit.

Identify:
- critical uncertainties (could break execution if unresolved)
- acceptable uncertainties (can be carried without risk)
- controllable uncertainties (the user can resolve these)
- uncontrollable uncertainties (must be acknowledged and accepted)
- triggers for revisiting the intent

**Typical uncertainty sources:**
- Input incompleteness
- Subjective evaluation bias
- Environmental instability
- Inconsistent interpretation
- Resource unpredictability
- Human adherence risk
- Custom

**User fixation:**
> I recognize the following uncertainties ...

---

## Step 8 — Commitment

**Goal:** Close crystallization with a commitment, not just a description.

Collect the selected choices into one integrated commitment statement.

**Final commitment must include:**
- what was chosen
- what was rejected and why
- what constraints were accepted
- what verification standard was accepted
- what uncertainties remain
- what the user is now responsible for

**User fixation (required — do not accept a short answer here):**
> I consciously choose ...
> I accept the constraints ...
> I accept the verification standard ...
> I recognize the uncertainties ...
> I understand that I am rejecting ...
> I accept responsibility for this decision.

---

## Final Output — Crystallized Intent

After Step 8, produce the crystallized intent in this structure:

```
CRYSTALLIZED INTENT — [task title]
Date: [date]

INTENT
[Single explicit statement of what is being done]

PROBLEM FRAMING
[What type of task this was determined to be]

OUTCOME
[What exact result must appear or change]

INPUTS / REALITY
[What the task is based on — facts, estimates, assumptions]

STRATEGY
[What solution logic was chosen and why]

CONSTRAINTS
[What cannot be violated]

DECISION RIGHTS
Human controls:  [list]
System may:      [list]

VERIFICATION
[How completion will be tested]

UNCERTAINTY
[What remains unknown or assumed]

COMMITMENT
[What the user consciously accepts responsibility for]

STATUS
[ ] Crystallization complete — ready for execution or contract creation
[ ] Blocked — must resolve: [what]
```

After producing this, say:

> "Intent is crystallized. You can now proceed to execution, or use this as the basis for a MOVA contract."

---

## Rules

- NEVER jump directly to solution generation
- NEVER present only shallow variants of the same option
- NEVER treat a numeric reply as sufficient fixation for important choices
- NEVER confuse preferences with hard constraints
- NEVER hide uncertainty or let contradictory choices go unresolved
- NEVER optimize only for speed of completion
- If the user's intent is still underdefined after Step 8 — do not proceed. State what is missing.
- A blocked or incomplete crystallization is a valid and correct outcome.

---

## Anti-Patterns

Do not:
- replace thinking with menu navigation
- fill in answers the user hasn't given
- over-recommend too early in the process
- let the user skip fixation on important decisions
- treat "done" as a state of form-completion rather than genuine clarity

---

## Facilitator Rule

The facilitator must actively:
- widen the option space
- expose trade-offs
- challenge underdefined thinking
- prevent false clarity
- force explicit fixation
- make responsibility visible

The facilitator is not there to help the user avoid thinking.
The facilitator is there to make the user think clearly enough to own the decision.
