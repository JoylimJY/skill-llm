import sys
import json
import re
from pathlib import Path
from datetime import date

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    def check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ──────────────────────────────────────────────────────────────────────────
    # BLOCK 1: remediation_plan.json
    # ──────────────────────────────────────────────────────────────────────────
    plan_files = list(workspace.rglob("remediation_plan.json"))
    if not plan_files:
        total_score += check(
            "remediation_plan.json exists",
            False,
            "File 'remediation_plan.json' not found anywhere in workspace."
        )
        plan = None
    else:
        plan_path = plan_files[0]
        try:
            plan = json.loads(plan_path.read_text())
            total_score += check("remediation_plan.json exists", True, f"Found at {plan_path}")
        except Exception as e:
            total_score += check("remediation_plan.json exists", False, f"JSON parse error: {e}")
            plan = None

    if plan is not None:
        plan_text = json.dumps(plan).lower()

        # Check 1: 70% threshold mentioned
        has_70 = bool(re.search(r'70\s*%|70\s*percent|0\.7\b|at.{0,20}70', plan_text))
        total_score += check(
            "Plan references 70% condensation trigger",
            has_70,
            "Plan must mention the 70% context threshold as the trigger for condensation." if not has_70 else f"Found 70% reference.",
            weight=1.5
        )

        # Check 2: Masking before summarization (ordering)
        mask_pos = plan_text.find("mask")
        summ_pos = plan_text.find("summar")
        if mask_pos == -1:
            mask_first = False
            mask_detail = "No mention of masking in remediation plan."
        elif summ_pos == -1:
            mask_first = True  # masking present, no summarization = correct preference
            mask_detail = "Masking mentioned; no conflicting summarization ordering issue."
        else:
            mask_first = mask_pos < summ_pos
            mask_detail = f"Masking appears at position {mask_pos}, summarization at {summ_pos}. {'Correct order.' if mask_first else 'WRONG: summarization listed before masking.'}"
        total_score += check(
            "Masking recommended before summarization",
            mask_first,
            mask_detail,
            weight=2.0
        )

        # Check 3: No re-summarization of already-condensed turns
        no_resummarize = bool(
            re.search(r'never.{0,40}re.?summar|re.?summar.{0,40}never|switch.{0,40}context|spawn.{0,40}sub.?agent|already.{0,40}condens', plan_text)
        )
        total_score += check(
            "Plan identifies re-summarization trap and prescribes switch/spawn",
            no_resummarize,
            "Plan must identify that turn 12 is already a condensed summary and prescribe context switch or sub-agent spawn instead of re-summarization." if not no_resummarize else "Correctly addresses the re-summarization trap.",
            weight=2.0
        )

        # Check 4: Tool outputs identified as primary context growth source
        tool_output_flagged = bool(
            re.search(r'tool.{0,30}output|84\s*%|lowest.{0,20}value|highest.{0,20}growth|raw.{0,20}output', plan_text)
        )
        total_score += check(
            "Plan identifies tool outputs as primary growth / low-value tokens",
            tool_output_flagged,
            "Plan should cite that tool outputs are the primary driver of context growth and lowest-value tokens." if not tool_output_flagged else "Tool output characterization found.",
            weight=1.5
        )

        # Check 5: Issues ordered by urgency / priority
        has_priority = bool(
            re.search(r'priorit|urgent|critical|order|first|p1|p2|high|medium|low', plan_text)
        )
        total_score += check(
            "Plan has priority ordering of issues",
            has_priority,
            "Remediation items should be ordered by priority/urgency." if not has_priority else "Priority ordering present.",
            weight=0.5
        )

        # Check 6: Quadratic cost mentioned
        has_cost_model = bool(
            re.search(r'quadrat|linear|cost.{0,30}scal|scal.{0,30}cost|2x|halv', plan_text)
        )
        total_score += check(
            "Plan references cost scaling model (quadratic→linear)",
            has_cost_model,
            "Plan should mention that unmanaged context causes quadratic cost scaling; condensation converts it to linear." if not has_cost_model else "Cost model reference found.",
            weight=1.0
        )

        # Check 7: Turn 9 specifically called out as missed condensation trigger
        turn9_flagged = bool(
            re.search(r'turn.{0,10}9|74.{0,10}%|74\s*percent', plan_text)
        )
        total_score += check(
            "Plan identifies missed condensation trigger at turn 9 (74%)",
            turn9_flagged,
            "Turn 9 crossed 74% context (past the 70% threshold) without triggering condensation — this must be flagged." if not turn9_flagged else "Turn 9 / 74% threshold violation identified.",
            weight=1.5
        )

    # ──────────────────────────────────────────────────────────────────────────
    # BLOCK 2: corrected_architecture.json
    # ──────────────────────────────────────────────────────────────────────────
    arch_files = list(workspace.rglob("corrected_architecture.json"))
    if not arch_files:
        total_score += check("corrected_architecture.json exists", False, "File not found.")
        arch = None
    else:
        arch_path = arch_files[0]
        try:
            arch = json.loads(arch_path.read_text())
            total_score += check("corrected_architecture.json exists", True, f"Found at {arch_path}")
        except Exception as e:
            total_score += check("corrected_architecture.json exists", False, f"Parse error: {e}")
            arch = None

    if arch is not None:
        arch_text = json.dumps(arch).lower()

        # Check: condensation_trigger_pct must be 70 (not 90 as in draft)
        trigger_correct = False
        try:
            trigger_val = arch.get("condensation_trigger_pct", arch.get("condensation_trigger", None))
            if trigger_val is not None:
                trigger_correct = (int(str(trigger_val).replace("%","").strip()) == 70)
            else:
                # Maybe embedded in text
                trigger_correct = bool(re.search(r'"70"|\b70\b', arch_text))
        except:
            trigger_correct = False
        total_score += check(
            "Corrected architecture: condensation trigger set to 70%",
            trigger_correct,
            f"Draft had 90%; correct value is 70%. Found: {arch.get('condensation_trigger_pct', 'not found')}",
            weight=2.0
        )

        # Check: condensation_order must be mask first, summarize second
        cond_order = arch.get("condensation_order", [])
        if isinstance(cond_order, list) and len(cond_order) >= 1:
            first_item = str(cond_order[0]).lower()
            order_correct = "mask" in first_item
        else:
            order_correct = bool(re.search(r'mask.{0,50}summar', arch_text))
        total_score += check(
            "Corrected architecture: condensation order is mask-first",
            order_correct,
            f"Masking must come before summarization. condensation_order first item: {cond_order[0] if isinstance(cond_order, list) and cond_order else 'not found'}",
            weight=2.0
        )

        # Check: re_summarize_allowed must be False/false/never
        re_summ = arch.get("re_summarize_allowed", None)
        re_summ_correct = (re_summ is False) or (str(re_summ).lower() in ["false", "never", "no", "0"])
        total_score += check(
            "Corrected architecture: re_summarize_allowed = false",
            re_summ_correct,
            f"Draft had True; correct is False. Found: {re_summ}",
            weight=2.0
        )

        # Check: critical_info_placement must be start/end, not middle
        placement = str(arch.get("critical_info_placement", "")).lower()
        placement_correct = any(w in placement for w in ["start", "end", "beginning", "first", "last", "top", "bottom"])
        placement_wrong = "middle" in placement
        total_score += check(
            "Corrected architecture: critical_info_placement at start or end (not middle)",
            placement_correct and not placement_wrong,
            f"Draft had 'middle'; correct is 'start or end'. Found: '{arch.get('critical_info_placement', 'not found')}'",
            weight=1.5
        )

        # Check: sub_agent_context must be fresh/clean, not inherit
        sub_ctx = str(arch.get("sub_agent_context", "")).lower()
        sub_correct = any(w in sub_ctx for w in ["fresh", "clean", "isolated", "independent", "new", "own"])
        sub_wrong = "inherit" in sub_ctx
        total_score += check(
            "Corrected architecture: sub_agent_context is fresh/clean (not inherited)",
            sub_correct and not sub_wrong,
            f"Draft had 'inherit_parent'; correct is fresh/clean context. Found: '{arch.get('sub_agent_context', 'not found')}'",
            weight=1.5
        )

        # Check: context_strategy must be typed blocks, not monolithic
        strategy = str(arch.get("context_strategy", "")).lower()
        strategy_correct = any(w in strategy for w in ["typed", "block", "structured", "labeled", "separated"])
        strategy_wrong = "monolith" in strategy
        total_score += check(
            "Corrected architecture: context_strategy is typed/blocked (not monolithic)",
            strategy_correct and not strategy_wrong,
            f"Draft had 'monolithic'; correct is typed blocks. Found: '{arch.get('context_strategy', 'not found')}'",
            weight=1.5
        )

        # Check: cost_scaling corrected to quadratic (without intervention)
        cost_scaling = str(arch.get("cost_scaling", "")).lower()
        cost_correct = any(w in cost_scaling for w in ["quadrat", "linear_with_condense", "linear_after", "quadratic_without", "periodic_condense"])
        total_score += check(
            "Corrected architecture: cost_scaling reflects quadratic→linear model",
            cost_correct,
            f"Draft had 'linear_assumed'; correct reflects quadratic without intervention, linear with condensation. Found: '{arch.get('cost_scaling', 'not found')}'",
            weight=1.0
        )

    # ──────────────────────────────────────────────────────────────────────────
    # BLOCK 3: memory/YYYY-MM-DD.md breadcrumb
    # ──────────────────────────────────────────────────────────────────────────
    memory_dir = workspace / "memory"
    today = date.today().strftime("%Y-%m-%d")

    # Find any markdown file in memory/ with a date-like name
    md_files = list(memory_dir.glob("*.md")) if memory_dir.exists() else []
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\.md$')
    dated_md = [f for f in md_files if date_pattern.match(f.name)]

    if not dated_md:
        total_score += check(
            "memory/YYYY-MM-DD.md breadcrumb exists",
            False,
            f"No date-named markdown file found in memory/. Files present: {[f.name for f in md_files]}",
            weight=2.0
        )
        breadcrumb_text = ""
    else:
        breadcrumb_path = dated_md[0]
        try:
            breadcrumb_text = breadcrumb_path.read_text()
            total_score += check(
                "memory/YYYY-MM-DD.md breadcrumb exists",
                True,
                f"Found: {breadcrumb_path.name}",
                weight=2.0
            )
        except Exception as e:
            total_score += check(
                "memory/YYYY-MM-DD.md breadcrumb exists",
                False,
                f"Error reading file: {e}",
                weight=2.0
            )
            breadcrumb_text = ""

    if breadcrumb_text:
        bt = breadcrumb_text.lower()

        # Must describe what was done
        has_what_done = bool(re.search(r'audit|session|analy|complet|did|accomplish|review', bt))
        total_score += check(
            "Breadcrumb: documents what was done",
            has_what_done,
            "Breadcrumb must describe the work completed (audit, session analysis, etc.)" if not has_what_done else "What-was-done section present.",
            weight=1.0
        )

        # Must describe what's next
        has_whats_next = bool(re.search(r'next|follow.?up|todo|action|recommend|step', bt))
        total_score += check(
            "Breadcrumb: documents what's next",
            has_whats_next,
            "Breadcrumb must include next steps or follow-up actions." if not has_whats_next else "What's-next section present.",
            weight=1.0
        )

        # Must reference file locations
        has_file_refs = bool(re.search(r'\.json|\.md|memory\/|agent_session|remediation|corrected|file|path', bt))
        total_score += check(
            "Breadcrumb: references file locations",
            has_file_refs,
            "Breadcrumb must mention where output files are located." if not has_file_refs else "File location references found.",
            weight=1.0
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Final scoring
    # ──────────────────────────────────────────────────────────────────────────
    max_score = (
        1.0 +  # plan exists
        1.5 + 2.0 + 2.0 + 1.5 + 0.5 + 1.0 + 1.5 +  # plan checks
        1.0 +  # arch exists
        2.0 + 2.0 + 2.0 + 1.5 + 1.5 + 1.5 + 1.0 +  # arch checks
        2.0 +  # breadcrumb exists
        1.0 + 1.0 + 1.0  # breadcrumb content
    )

    normalized = round(min(total_score / max_score, 1.0), 4)
    passed = normalized >= 0.65

    return {
        "passed": passed,
        "score": normalized,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))