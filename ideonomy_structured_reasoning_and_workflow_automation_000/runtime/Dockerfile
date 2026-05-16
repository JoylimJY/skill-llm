FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN printf '%s\n' \
    '#!/usr/bin/env python3' \
    'import sys' \
    'import json' \
    'import argparse' \
    '' \
    'LENSES = {' \
    '    "CAUSES": "causal_analysis",' \
    '    "ANALOGIES": "analogical_reasoning",' \
    '    "CONSTRAINTS": "constraint_mapping",' \
    '    "STAKEHOLDERS": "stakeholder_analysis",' \
    '    "TRADEOFFS": "tradeoff_analysis",' \
    '    "RISKS": "risk_assessment",' \
    '    "OPPORTUNITIES": "opportunity_identification",' \
    '    "SYSTEMS": "systems_thinking",' \
    '    "FIRST_PRINCIPLES": "first_principles",' \
    '    "SCENARIOS": "scenario_planning",' \
    '    "ASSUMPTIONS": "assumption_challenge",' \
    '    "METRICS": "metrics_definition",' \
    '}' \
    '' \
    'STYLES = {' \
    '    "diagnostic": ["CAUSES", "ANALOGIES", "SYSTEMS", "ASSUMPTIONS"],' \
    '    "strategic": ["TRADEOFFS", "SCENARIOS", "STAKEHOLDERS", "RISKS"],' \
    '    "exploratory": ["OPPORTUNITIES", "ANALOGIES", "FIRST_PRINCIPLES", "CONSTRAINTS"],' \
    '}' \
    '' \
    'def generate_lens_output(lens, problem, concise=False):' \
    '    base = {' \
    '        "lens": lens,' \
    '        "type": LENSES.get(lens, "general_analysis"),' \
    '        "problem_excerpt": problem[:80] + "..." if len(problem) > 80 else problem,' \
    '        "insights": [' \
    '            f"Primary insight via {lens} lens applied to the stated problem.",' \
    '            f"Secondary consideration: systemic patterns revealed through {lens}.",' \
    '            f"Actionable signal: investigate {lens.lower()}-related factors further."' \
    '        ],' \
    '        "confidence": "medium-high",' \
    '    }' \
    '    if not concise:' \
    '        base["detailed_reasoning"] = (' \
    '            f"Applying {lens} reasoning: The problem exhibits characteristics best "' \
    '            f"understood through {LENSES.get(lens, '"'"'general'"'"')} frameworks. "' \
    '            f"Key signals include ambiguity in root cause attribution and multi-variable interactions."' \
    '        )' \
    '        base["recommended_actions"] = [' \
    '            f"Map {lens.lower()} dependencies explicitly.",' \
    '            f"Validate {lens.lower()} assumptions with stakeholders.",' \
    '            f"Prioritize {lens.lower()} factors in next analysis cycle.",' \
    '        ]' \
    '    return base' \
    '' \
    'def main():' \
    '    parser = argparse.ArgumentParser(prog="ideonomy", description="Ideonomy reasoning engine")' \
    '    subparsers = parser.add_subparsers(dest="command")' \
    '' \
    '    analyze_parser = subparsers.add_parser("analyze", help="Analyze a problem")' \
    '    analyze_parser.add_argument("--problem", required=False, default="", help="Problem statement")' \
    '    analyze_parser.add_argument("--style", default="diagnostic", help="Reasoning style")' \
    '    analyze_parser.add_argument("--lenses", default=None, help="Comma-separated lens names")' \
    '    analyze_parser.add_argument("--concise", action="store_true", help="Concise output")' \
    '    analyze_parser.add_argument("--limit", type=int, default=None, help="Max number of lenses")' \
    '' \
    '    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ("--help", "-h")):' \
    '        parser.print_help()' \
    '        sys.exit(0)' \
    '' \
    '    args = parser.parse_args()' \
    '' \
    '    if args.command == "analyze":' \
    '        problem = args.problem' \
    '        style = args.style if args.style in STYLES else "diagnostic"' \
    '' \
    '        if args.lenses:' \
    '            selected_lenses = [l.strip().upper() for l in args.lenses.split(",")]' \
    '        else:' \
    '            selected_lenses = STYLES[style]' \
    '' \
    '        if args.limit:' \
    '            selected_lenses = selected_lenses[:args.limit]' \
    '' \
    '        result = {' \
    '            "style": style,' \
    '            "problem": problem,' \
    '            "concise": args.concise,' \
    '            "lenses_applied": selected_lenses,' \
    '            "analysis": [generate_lens_output(l, problem, args.concise) for l in selected_lenses],' \
    '            "engine_version": "1.0.0",' \
    '        }' \
    '        print(json.dumps(result, indent=2))' \
    '    else:' \
    '        parser.print_help()' \
    '        sys.exit(1)' \
    '' \
    'if __name__ == "__main__":' \
    '    main()' \
    > /usr/local/bin/ideonomy

RUN chmod +x /usr/local/bin/ideonomy

WORKDIR /workspace