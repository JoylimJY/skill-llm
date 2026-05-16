#!/usr/bin/env python3
"""
Generate the sandbox workspace for the deep-research skill evaluation.
Creates a realistic, messy workspace with pre-staged source cards and a
misconfigured/incomplete setup that the agent must fix and run.
"""

import os
import stat
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ─── Directory Structure ───────────────────────────────────────────────────────
dirs = [
    "skills/deep-research/config",
    "skills/deep-research/prompts",
    "skills/deep-research/templates",
    "skills/deep-research/scripts",
    "skills/deep-research/reports",
    "skills/deep-research/sources",
    "skills/deep-research/cache",
    "skills/deep-research/logs",
    # Distractor dirs
    "skills/web-scraper/config",
    "skills/web-scraper/scripts",
    "skills/summarizer/templates",
    "skills/summarizer/outputs",
    "archive/old-reports/2025",
    "archive/old-reports/2024",
    "data/raw",
    "data/processed",
    "notebooks",
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor Files ──────────────────────────────────────────────────────────
distractor_files = {
    "skills/web-scraper/config/scraper.yaml": "target_urls:\n  - https://example.com\ndelay: 2\n",
    "skills/web-scraper/scripts/run-scraper.sh": "#!/bin/bash\necho 'scraper not configured'\n",
    "skills/summarizer/templates/summary.md": "# Summary Template\n## Key Points\n- Point 1\n",
    "skills/summarizer/outputs/old-summary-2024.md": "# Old Summary\nThis is an outdated summary from 2024.\n",
    "archive/old-reports/2025/quantum-overview.txt": "Outdated quantum computing overview from 2025.\nDo not use for current research.\n",
    "archive/old-reports/2024/ml-survey.md": "# ML Survey 2024\nOld machine learning survey results.\n",
    "data/raw/papers-list.csv": "id,title,year\n001,Quantum Error Correction,2023\n002,Variational Quantum Eigensolver,2022\n",
    "data/processed/metrics-old.json": '{"accuracy": 0.87, "domain": "deprecated", "version": "v4.0"}\n',
    "notebooks/exploration.py": "# Scratch notebook - not part of pipeline\nimport pandas as pd\n# TODO: clean up\n",
    "tmp/debug.log": "2026-01-15 10:23:11 DEBUG: Pipeline started\n2026-01-15 10:23:45 ERROR: Config mismatch\n",
    "skills/deep-research/logs/old-run-20260101.log": "Run started: 2026-01-01\nDomain: healthcare (DEPRECATED)\nStatus: completed\n",
    "skills/deep-research/cache/stale-cache.json": '{"timestamp": "2026-01-01", "domain": "healthcare", "results": []}\n',
}
for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.write_text(content)

# ─── MISCONFIGURED research-config.yaml ───────────────────────────────────────
# Wrong domain (still set to healthcare), missing performance metrics, broken structure
bad_config = textwrap.dedent("""\
    # Research Configuration - NEEDS UPDATE
    research_domain: "healthcare"   # <-- stale, must be changed

    # key_metrics section is incomplete
    key_metrics:
      performance:
        # TODO: fill in metrics for new domain
      cost:
        - roi
        - tco

    data_sources:
      priority:
        - arxiv
        - pubmed
        - web

    output:
      max_executive_summary_lines: 50
      require_completeness_tags: true
""")
(WORKSPACE / "skills/deep-research/config/research-config.yaml").write_text(bad_config)

# ─── Prompts ───────────────────────────────────────────────────────────────────
extract_prompt = textwrap.dedent("""\
    You are a universal research extractor. Given any academic text, extract:
    1. Core claims with evidence
    2. Quantitative metrics (label completeness: high/medium/low)
    3. Methodology summary
    4. Limitations
    5. Missing data points

    Output format:
    CLAIM: <claim>
    EVIDENCE: <evidence>
    COMPLETENESS: <high|medium|low>
    MISSING: <what data is absent>
""")
(WORKSPACE / "skills/deep-research/prompts/extract-universal.txt").write_text(extract_prompt)

cluster_prompt = textwrap.dedent("""\
    Group the provided research cards by theme.
    Output: numbered clusters with card IDs.
""")
(WORKSPACE / "skills/deep-research/prompts/cluster-cards.txt").write_text(cluster_prompt)

brief_prompt = textwrap.dedent("""\
    Write a concise thematic brief from the clustered research cards.
    Maximum 200 words per theme.
""")
(WORKSPACE / "skills/deep-research/prompts/write-brief.txt").write_text(brief_prompt)

# ─── Templates ─────────────────────────────────────────────────────────────────
exec_template = textwrap.dedent("""\
    # Executive Summary: {{TOPIC}}

    **Domain:** {{DOMAIN}}
    **Date:** {{DATE}}
    **Confidence:** {{CONFIDENCE}}

    ## Core Findings (Verified)
    {{VERIFIED_FINDINGS}}

    ## Pending Verification
    {{PENDING_FINDINGS}}

    ## Recommended Actions
    - **Immediate:** {{ACTION_NOW}}
    - **After Verification:** {{ACTION_LATER}}
""")
(WORKSPACE / "skills/deep-research/templates/executive-summary.md").write_text(exec_template)

checklist_template = textwrap.dedent("""\
    # Validation Checklist: {{TOPIC}}

    ## Missing Metrics Summary
    | Metric | Source Card | Verification Path |
    |--------|-------------|-------------------|
    {{MISSING_METRICS_TABLE}}

    ## Verification Steps
    {{VERIFICATION_STEPS}}

    ## Universal Verification Methods
    - Cross-reference with primary sources
    - Contact corresponding authors
    - Search preprint servers for updates
""")
(WORKSPACE / "skills/deep-research/templates/validation-checklist.md").write_text(checklist_template)

full_report_template = textwrap.dedent("""\
    # Full Research Report: {{TOPIC}}

    ## Methodology
    {{METHODOLOGY}}

    ## Verified Conclusions
    {{VERIFIED_CONCLUSIONS}}

    ## Pending Verification
    {{PENDING_CONCLUSIONS}}

    ## Strategic Recommendations
    ### Short-term (0-3 months)
    {{SHORT_TERM}}

    ### Medium-term (3-12 months)
    {{MEDIUM_TERM}}

    ### Long-term (12+ months)
    {{LONG_TERM}}

    ## Card Index
    {{CARD_INDEX}}
""")
(WORKSPACE / "skills/deep-research/templates/full-report.md").write_text(full_report_template)

# ─── Pre-staged Source Cards ───────────────────────────────────────────────────
# These simulate what fetch-and-extract.sh would produce for quantum computing topic
cards = {
    "card-001.md": textwrap.dedent("""\
        # Card 001: Quantum Circuit Optimization via Gate Reduction
        **Source:** arXiv:2401.12345
        **Source Type:** arxiv-pdf
        **Completeness:** high

        ## Claim
        Variational gate compression reduces two-qubit gate count by 47% on NISQ hardware without fidelity loss below 0.02.

        ## Evidence
        Experiments on IBM Quantum 27-qubit system; tested on 8 benchmark circuits; fidelity measured via quantum state tomography.

        ## Metrics
        - Gate reduction: 47%
        - Fidelity loss: <0.02
        - Circuit depth reduction: 31%

        ## Missing Data
        - Energy consumption per gate not reported
        - Comparison with classical simulation costs absent

        ## Methodology
        Variational optimization using COBYLA optimizer; gradient-free approach.
    """),
    "card-002.md": textwrap.dedent("""\
        # Card 002: Cost Analysis of Quantum vs Classical HPC
        **Source:** arXiv:2402.67890
        **Source Type:** arxiv-pdf
        **Completeness:** medium

        ## Claim
        Quantum annealing achieves 23x speedup over classical branch-and-bound for portfolio optimization with >50 assets.

        ## Evidence
        D-Wave Advantage system; 100 problem instances; average over 10 runs each.

        ## Metrics
        - Speedup factor: 23x (for N>50 assets)
        - Cost per solve: ~$0.003 (quantum) vs ~$0.07 (cloud HPC)
        - Accuracy: within 0.5% of classical optimal

        ## Missing Data
        - Total cost of ownership for quantum hardware not included
        - Energy efficiency comparison absent
        - Scaling behavior beyond N=200 unknown

        ## Methodology
        QUBO formulation; hybrid quantum-classical solver pipeline.
    """),
    "card-003.md": textwrap.dedent("""\
        # Card 003: Error Mitigation ROI in Production Quantum Systems
        **Source:** PMC9876543
        **Source Type:** pmc-pdf
        **Completeness:** high

        ## Claim
        Zero-noise extrapolation reduces error rates by 60% at 2.4x computational overhead, yielding net positive ROI for circuits >200 gates.

        ## Evidence
        Production deployment at 3 financial institutions; 6-month longitudinal study; 1,200 circuit executions analyzed.

        ## Metrics
        - Error reduction: 60%
        - Computational overhead: 2.4x
        - Break-even point: >200-gate circuits
        - Annual cost saving: $2.1M per institution (average)

        ## Missing Data
        - Institution names redacted
        - Hardware vendor not disclosed

        ## Methodology
        ZNE with Richardson extrapolation; deployment on gate-based systems.
    """),
    "card-004.md": textwrap.dedent("""\
        # Card 004: Quantum Advantage Threshold for Logistics Optimization
        **Source:** PubMed:34567890
        **Source Type:** pubmed-abstract
        **Completeness:** low

        ## Claim
        [NEEDS VERIFICATION] Quantum routing algorithms may outperform classical solutions for fleet sizes >500 vehicles.

        ## Evidence
        Abstract only; claims based on simulation, not hardware deployment.

        ## Metrics
        - Fleet size threshold: >500 vehicles (unverified)
        - Claimed speedup: 12-18x (simulation only)

        ## Missing Data
        - Hardware benchmark absent
        - Real-world noise not modeled
        - Cost comparison not provided
        - Full methodology not accessible (paywalled)

        ## Methodology
        Quantum approximate optimization algorithm (QAOA); simulation only.
    """),
}
for fname, content in cards.items():
    (WORKSPACE / "skills/deep-research/sources" / fname).write_text(content)

# ─── The Core Scripts (functional stubs that the agent triggers) ────────────────

# run-research.sh: Main orchestration script
run_research = textwrap.dedent("""\
    #!/bin/bash
    # Adaptive Depth Research v6.0 - Main Runner
    set -e

    TOPIC="$1"
    DOMAIN=""
    SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

    # Parse arguments
    shift
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done

    if [ -z "$TOPIC" ]; then
        echo "ERROR: Topic required. Usage: bash run-research.sh '<topic>' --domain '<domain>'"
        exit 1
    fi

    if [ -z "$DOMAIN" ]; then
        echo "ERROR: --domain flag required."
        exit 1
    fi

    CONFIG="$SKILL_DIR/config/research-config.yaml"
    SOURCES_DIR="$SKILL_DIR/sources"
    REPORTS_DIR="$SKILL_DIR/reports"

    echo "=== Adaptive Depth Research v6.0 ==="
    echo "Topic: $TOPIC"
    echo "Domain: $DOMAIN"
    echo "Config: $CONFIG"

    # Validate config has correct domain
    CONFIG_DOMAIN=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG')); print(c.get('research_domain',''))" 2>/dev/null || echo "")
    if [ -z "$CONFIG_DOMAIN" ] || [ "$CONFIG_DOMAIN" = "healthcare" ]; then
        echo "ERROR: research-config.yaml still has stale domain '$CONFIG_DOMAIN'. Update research_domain field."
        exit 1
    fi

    # Validate key_metrics has performance entries
    PERF_COUNT=$(python3 -c "
import yaml
c = yaml.safe_load(open('$CONFIG'))
km = c.get('key_metrics', {})
perf = km.get('performance', [])
print(len(perf) if isinstance(perf, list) else 0)
" 2>/dev/null || echo "0")
    if [ "$PERF_COUNT" -lt 2 ]; then
        echo "ERROR: key_metrics.performance must have at least 2 entries in research-config.yaml"
        exit 1
    fi

    mkdir -p "$REPORTS_DIR"

    echo "--- Fetching and extracting sources ---"
    CARD_LIST=$(ls "$SOURCES_DIR"/card-*.md 2>/dev/null | sort)
    CARD_COUNT=$(echo "$CARD_LIST" | grep -c 'card-' || echo 0)
    echo "Found $CARD_COUNT source cards."

    # Build consolidated card index
    CARD_INDEX=""
    VERIFIED=""
    PENDING=""
    HIGH_COUNT=0
    MED_COUNT=0
    LOW_COUNT=0

    for card in $CARD_LIST; do
        card_id=$(basename "$card" .md)
        completeness=$(grep -i "Completeness:" "$card" | head -1 | awk '{print $NF}' | tr '[:upper:]' '[:lower:]')
        claim=$(grep -A1 "^## Claim" "$card" | tail -1 | head -c 120)
        source=$(grep "^\*\*Source:\*\*" "$card" | head -1 | sed 's/\*\*Source:\*\*\s*//')

        CARD_INDEX="$CARD_INDEX\n- [$card_id] $source — $claim"

        case "$completeness" in
            high)
                HIGH_COUNT=$((HIGH_COUNT+1))
                VERIFIED="$VERIFIED\n- [$card_id] $claim (COMPLETENESS: high)"
                ;;
            medium)
                MED_COUNT=$((MED_COUNT+1))
                VERIFIED="$VERIFIED\n- [$card_id] $claim (COMPLETENESS: medium)"
                ;;
            low)
                LOW_COUNT=$((LOW_COUNT+1))
                PENDING="$PENDING\n- [$card_id] $claim (COMPLETENESS: low — NEEDS VERIFICATION)"
                ;;
        esac
    done

    DATE=$(date +%Y-%m-%d)

    # ── Generate Executive Summary (must be ≤1 page / ≤50 lines) ──────────────
    cat > "$REPORTS_DIR/executive-summary.md" << EXECEOF
# Executive Summary: $TOPIC

**Domain:** $DOMAIN
**Date:** $DATE
**Sources Analyzed:** $CARD_COUNT cards (High: $HIGH_COUNT, Medium: $MED_COUNT, Low: $LOW_COUNT)

## Core Findings (Verified)
$(echo -e "$VERIFIED")

## Pending Verification
$(echo -e "$PENDING")

## Recommended Actions
- **Immediate:** Leverage high-confidence findings for $DOMAIN decision-making
- **After Verification:** Validate low-completeness claims before strategic commitments

## Data Completeness Summary
| Level | Count | Action |
|-------|-------|--------|
| high  | $HIGH_COUNT | Use directly |
| medium | $MED_COUNT | Use with caution |
| low   | $LOW_COUNT | Verify before use |
EXECEOF

    EXEC_LINES=$(wc -l < "$REPORTS_DIR/executive-summary.md")
    echo "Executive summary: $EXEC_LINES lines"

    # ── Generate Validation Checklist ──────────────────────────────────────────
    cat > "$REPORTS_DIR/validation-checklist.md" << CHECKEOF
# Validation Checklist: $TOPIC

**Domain:** $DOMAIN
**Date:** $DATE

## Missing Metrics Summary
| Card | Completeness | Missing Data | Verification Path |
|------|-------------|--------------|-------------------|
CHECKEOF

    for card in $CARD_LIST; do
        card_id=$(basename "$card" .md)
        completeness=$(grep -i "Completeness:" "$card" | head -1 | awk '{print $NF}')
        missing=$(grep -A3 "^## Missing Data" "$card" | grep "^-" | head -2 | tr '\n' '; ')
        echo "| $card_id | $completeness | $missing | Search arXiv/PMC for full text |" >> "$REPORTS_DIR/validation-checklist.md"
    done

    cat >> "$REPORTS_DIR/validation-checklist.md" << CHECKEOF2

## Verification Steps
1. For cards with completeness: low — retrieve full-text papers
2. For missing cost/energy data — search supplementary materials
3. Contact corresponding authors for proprietary benchmarks
4. Cross-validate metrics across independent sources

## Universal Verification Methods
- Cross-reference with primary sources
- Contact corresponding authors
- Search preprint servers for updates
CHECKEOF2

    # ── Generate Full Report ───────────────────────────────────────────────────
    cat > "$REPORTS_DIR/full-report.md" << FULLEOF
# Full Research Report: $TOPIC

**Domain:** $DOMAIN
**Date:** $DATE
**Research Skill Version:** v6.0 Universal

## Methodology
- Searched arXiv, PMC, PubMed sources
- Applied universal extraction prompt
- Completeness tags: high/medium/low assigned per card
- Sourcing validated against card index

## Verified Conclusions
$(echo -e "$VERIFIED")

## Pending Verification
$(echo -e "$PENDING")

## Strategic Recommendations

### Short-term (0-3 months)
- Apply high-confidence findings from $HIGH_COUNT verified cards
- Begin procurement evaluation based on cost data in card-002, card-003

### Medium-term (3-12 months)
- Validate pending claims (card-004) via hardware benchmarks
- Commission independent replication study for key metrics

### Long-term (12+ months)
- Reassess quantum advantage thresholds as hardware matures
- Build internal benchmarking capability for continuous evaluation

## Card Index
$(echo -e "$CARD_INDEX")

## Sourcing Audit
All conclusions traceable to source cards in sources/ directory.
FULLEOF

    echo "=== Reports generated in $REPORTS_DIR ==="
    echo "  - executive-summary.md"
    echo "  - validation-checklist.md"
    echo "  - full-report.md"
    echo "=== Research complete ==="
""")
(WORKSPACE / "skills/deep-research/scripts/run-research.sh").write_text(run_research)

# fetch-and-extract.sh
fetch_extract = textwrap.dedent("""\
    #!/bin/bash
    # Auto-routing extractor: arxiv -> PDF full text, pubmed -> abstract only
    SOURCE_URL="$1"
    SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

    if [ -z "$SOURCE_URL" ]; then
        echo "Usage: bash fetch-and-extract.sh <source_url>"
        exit 1
    fi

    if echo "$SOURCE_URL" | grep -qi "arxiv"; then
        echo "Routing to: arxiv-pdf (high confidence)"
    elif echo "$SOURCE_URL" | grep -qi "pmc"; then
        echo "Routing to: pmc-pdf (high confidence)"
    elif echo "$SOURCE_URL" | grep -qi "pubmed"; then
        echo "Routing to: pubmed-abstract (needs verification tag)"
    else
        echo "Routing to: web-scrape (directional only)"
    fi
    echo "Extraction complete. Card written to sources/"
""")
(WORKSPACE / "skills/deep-research/scripts/fetch-and-extract.sh").write_text(fetch_extract)

# extract-from-pdf.py
extract_pdf = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"PDF extraction script using pymupdf\"\"\"
    import sys
    import os

    def extract(card_id, pdf_url):
        print(f"Extracting card {card_id} from {pdf_url}")
        print("Note: In sandbox mode, using pre-staged source cards.")
        print(f"Output: sources/{card_id}.md")

    if __name__ == "__main__":
        if len(sys.argv) < 3:
            print("Usage: python3 extract-from-pdf.py <card-id> <pdf_url>")
            sys.exit(1)
        extract(sys.argv[1], sys.argv[2])
""")
(WORKSPACE / "skills/deep-research/scripts/extract-from-pdf.py").write_text(extract_pdf)

# check-sourcing.sh
check_sourcing = textwrap.dedent("""\
    #!/bin/bash
    # Validate that all claims in full-report.md are traceable to source cards
    REPORT="$1"
    SOURCES_DIR="$2"

    if [ -z "$REPORT" ] || [ -z "$SOURCES_DIR" ]; then
        echo "Usage: bash check-sourcing.sh <full-report.md> <sources/>"
        exit 1
    fi

    if [ ! -f "$REPORT" ]; then
        echo "ERROR: Report not found: $REPORT"
        exit 1
    fi

    FAIL=0
    echo "=== Sourcing Validation ==="

    # Check each card referenced in the report exists in sources
    for card_ref in $(grep -oP 'card-\\d+' "$REPORT" | sort -u); do
        card_file="$SOURCES_DIR/${card_ref}.md"
        if [ -f "$card_file" ]; then
            echo "  [OK] $card_ref -> $card_file"
        else
            echo "  [FAIL] $card_ref -> NOT FOUND in $SOURCES_DIR"
            FAIL=1
        fi
    done

    if [ "$FAIL" -eq 0 ]; then
        echo "Sourcing validation: PASSED"
        exit 0
    else
        echo "Sourcing validation: FAILED"
        exit 1
    fi
""")
(WORKSPACE / "skills/deep-research/scripts/check-sourcing.sh").write_text(check_sourcing)

# research_claw_bridge.py
bridge_py = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    Research Claw Bridge - v7.0
    Bridges arXiv, Google Scholar, PubMed, Semantic Scholar with local pipeline.
    \"\"\"
    import os
    import json
    from pathlib import Path

    class ResearchTools:
        def __init__(self, skill_dir=None):
            if skill_dir is None:
                skill_dir = Path(__file__).parent.parent
            self.skill_dir = Path(skill_dir)
            self.sources_dir = self.skill_dir / "sources"
            self.reports_dir = self.skill_dir / "reports"

        def search_papers(self, query, max_results=5):
            \"\"\"Search for papers (sandbox: returns pre-staged cards)\"\"\"
            cards = list(self.sources_dir.glob("card-*.md"))
            results = []
            for card in cards[:max_results]:
                results.append({
                    "id": card.stem,
                    "title": card.stem.replace("-", " ").title(),
                    "source": card.read_text().split("\\n")[2] if card.exists() else "",
                })
            print(f"Found {len(results)} papers for query: {query}")
            return results

        def full_research_flow(self, topic, domain=None):
            \"\"\"Complete pipeline: search + extract + report\"\"\"
            import subprocess
            script = self.skill_dir / "scripts" / "run-research.sh"
            cmd = ["bash", str(script), topic]
            if domain:
                cmd += ["--domain", domain]
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(result.stdout)
            if result.returncode != 0:
                print("STDERR:", result.stderr)
            return result.returncode == 0
""")
(WORKSPACE / "skills/deep-research/scripts/research_claw_bridge.py").write_text(bridge_py)

# ─── Make all scripts executable ───────────────────────────────────────────────
scripts = [
    "skills/deep-research/scripts/run-research.sh",
    "skills/deep-research/scripts/fetch-and-extract.sh",
    "skills/deep-research/scripts/check-sourcing.sh",
    "skills/deep-research/scripts/extract-from-pdf.py",
]
for s in scripts:
    p = WORKSPACE / s
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ─── SKILL.md (the actual skill doc the agent should read) ─────────────────────
skill_md = Path("/workspace/skills/deep-research/SKILL.md")
skill_md.write_text(textwrap.dedent("""\
    ---
    name: deep-research
    description: 深度研究技能，用于进行领域调研、文献调研、survey研究。
    ---

    # Skill: Adaptive Depth Research v6.0 Universal

    > 版本：6.0.0

    ## 🚀 触发命令

    ```bash
    bash scripts/run-research.sh "<主题>" --domain "<领域>"

    # 示例
    bash scripts/run-research.sh "transformer efficiency" --domain "machine learning"
    bash scripts/run-research.sh "telemedicine cost savings" --domain "healthcare"
    ```

    ## 📁 文件结构

    ```
    skills/deep-research/
    ├── SKILL.md
    ├── config/
    │   └── research-config.yaml      # 领域配置
    ├── prompts/
    │   ├── extract-universal.txt
    │   ├── cluster-cards.txt
    │   └── write-brief.txt
    ├── templates/
    │   ├── executive-summary.md
    │   ├── validation-checklist.md
    │   └── full-report.md
    └── scripts/
        ├── run-research.sh
        ├── fetch-and-extract.sh
        ├── extract-from-pdf.py
        └── check-sourcing.sh
    ```

    ## 🔧 配置说明

    编辑 `config/research-config.yaml`:

    ```yaml
    research_domain: "your_domain_here"

    key_metrics:
      performance:
        - accuracy
        - AUC
        - F1
      # 添加你的指标...
    ```

    ## 📊 三层输出说明

    ### 1. 执行摘要 (executive-summary.md)
    - **受众**：决策者
    - **长度**：≤1页
    - **内容**：核心结论（已验证 vs 待验证）、可直接行动、需验证后行动

    ### 2. 验证清单 (validation-checklist.md)
    - **受众**：执行者
    - **格式**：操作导向
    - **内容**：缺失指标汇总表、具体验证路径

    ### 3. 完整报告 (full-report.md)
    - **受众**：审计/存档
    - **内容**：方法论、已验证结论+证据、待验证线索、战略建议（短/中/长期）、完整卡片索引

    ## ✅ 质量门禁

    1. **数据完整度标注**：high/medium/low
    2. **缺失指标清单**：每个卡片明确列出
    3. **验证路径具体**：可操作，非模糊建议
    4. **溯源验证**：所有数据可溯源到卡片

    ## 执行流程

    ### Step 1: 修改配置
    更新 `config/research-config.yaml` 的 `research_domain` 字段为目标领域，并在 `key_metrics.performance` 下添加至少2个相关指标。

    ### Step 2: 运行研究
    ```bash
    bash scripts/run-research.sh "<主题>" --domain "<领域>"
    ```

    ### Step 3: 溯源验证
    ```bash
    bash scripts/check-sourcing.sh reports/full-report.md sources/
    ```

    三层报告自动生成在 `reports/` 目录

    ## v7.0 融合版

    ```python
    from scripts.research_claw_bridge import ResearchTools

    tools = ResearchTools()
    results = tools.full_research_flow("商保控费")
    ```
"""))

print("✅ Workspace generated successfully.")
print(f"   Skills dir: {WORKSPACE / 'skills/deep-research'}")
print(f"   Source cards: {len(list((WORKSPACE / 'skills/deep-research/sources').glob('card-*.md')))} cards")
print(f"   Distractor files: {len(distractor_files)}")