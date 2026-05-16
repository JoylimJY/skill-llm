import os
import json
import random

random.seed(42)

# Create deeply nested workspace structure with distractor files
workspace = "/workspace"

# Strategy consulting firm directory structure
dirs = [
    "projects/alpha_ventures/market_research",
    "projects/alpha_ventures/financials",
    "projects/beta_expansion/competitor_analysis",
    "projects/beta_expansion/legal",
    "internal/strategy_frameworks",
    "internal/templates",
    "internal/past_reports/2022",
    "internal/past_reports/2023",
    "tools/wiki",
    "tools/submission",
    "data/raw_surveys",
    "data/processed",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - various irrelevant content
distractors = [
    ("projects/alpha_ventures/market_research/survey_results.csv",
     "respondent_id,q1,q2,q3\n1,yes,no,maybe\n2,no,yes,yes\n3,maybe,no,no\n"),

    ("projects/alpha_ventures/financials/q3_report.txt",
     "Q3 Financial Report\nRevenue: $4.2M\nExpenses: $3.8M\nNet: $0.4M\n"),

    ("projects/beta_expansion/competitor_analysis/competitors.json",
     json.dumps({"competitors": ["DroneX", "AirShip", "QuickFly"], "market_share": [0.35, 0.28, 0.17]})),

    ("projects/beta_expansion/legal/regulatory_notes.txt",
     "FAA Part 135 certification required.\nBeyond Visual Line of Sight (BVLOS) permits pending.\nUrban Air Mobility framework draft 2024.\n"),

    ("internal/strategy_frameworks/bcg_matrix.md",
     "# BCG Matrix\nStars, Cash Cows, Question Marks, Dogs.\nUse for portfolio analysis.\n"),

    ("internal/strategy_frameworks/swot_template.txt",
     "STRENGTHS:\nWEAKNESSES:\nOPPORTUNITIES:\nTHREATS:\n"),

    ("internal/templates/report_header.txt",
     "CONFIDENTIAL - INTERNAL USE ONLY\nAlpha Consulting Group\nDate: [DATE]\nAuthor: [AUTHOR]\n"),

    ("internal/past_reports/2022/logistics_sector_overview.txt",
     "The global logistics market reached $9.6T in 2022.\nKey players: FedEx, UPS, DHL, Amazon Logistics.\nGrowth drivers: ecommerce, last-mile delivery.\n"),

    ("internal/past_reports/2023/ev_market_entry.txt",
     "EV Market Entry Analysis - 2023\nConclusion: Favorable conditions for entry.\nKey risks: supply chain, regulation, competition.\n"),

    ("data/raw_surveys/drone_sentiment_raw.txt",
     "Q: Would you use drone delivery?\nYes: 62%\nNo: 24%\nUnsure: 14%\n"),

    ("data/processed/cleaned_responses.json",
     json.dumps({"sample_size": 1200, "positive": 744, "negative": 288, "neutral": 168})),

    ("projects/alpha_ventures/market_research/methodology.md",
     "# Research Methodology\n## Data Collection\nOnline survey, n=1200\n## Analysis\nDescriptive statistics, sentiment analysis\n"),
]

for filepath, content in distractors:
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# Create the business problem statement file
problem_statement = """MEMORANDUM

TO: Strategy Analysis Team
FROM: Executive Committee
DATE: 2024-01-15
SUBJECT: Market Entry Feasibility - Commercial Drone Delivery

Our executive committee is evaluating whether AlphaLogistics Inc. should enter 
the commercial drone delivery market in North America. 

This is a significant strategic decision involving substantial capital investment 
(estimated $50M over 3 years), regulatory complexity, and competitive uncertainty.

We need a rigorous, structured decomposition of this decision problem so our 
leadership team can systematically evaluate all relevant dimensions before 
committing to a path forward.

Please produce a formal, structured breakdown of this problem and submit it 
as an official strategy document via our documentation system.

Key context:
- AlphaLogistics Inc. is currently a mid-tier ground logistics provider
- The drone delivery market is nascent but growing at ~35% CAGR
- Major tech companies (Amazon, Wing/Alphabet) are already active
- Regulatory environment is evolving rapidly

The decomposition should cover all critical angles of this market entry decision 
without overlap or gaps. Document it formally and submit for executive review.
"""

with open(os.path.join(workspace, "TASK_BRIEF.txt"), "w") as f:
    f.write(problem_statement)

# Create mock tool scripts directory
tools_dir = os.path.join(workspace, "tools")

# create_wiki_document mock tool
wiki_tool_script = '''\
#!/usr/bin/env python3
"""
Mock create_wiki_document tool.
Usage: python3 create_wiki_document.py --title "..." --content "..."
Writes a wiki document and returns a document ID.
"""
import sys
import json
import argparse
import os
import time
import hashlib

def main():
    parser = argparse.ArgumentParser(description='Create a wiki document')
    parser.add_argument('--title', required=True, help='Document title')
    parser.add_argument('--content', required=True, help='Document content')
    args = parser.parse_args()

    doc_id = "wiki_" + hashlib.md5((args.title + str(time.time())).encode()).hexdigest()[:8]
    
    output_dir = "/workspace/tools/wiki"
    os.makedirs(output_dir, exist_ok=True)
    
    doc = {
        "document_id": doc_id,
        "title": args.title,
        "content": args.content,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    with open(os.path.join(output_dir, f"{doc_id}.json"), "w") as f:
        json.dump(doc, f, indent=2)
    
    # Also write latest doc reference
    with open(os.path.join(output_dir, "latest_doc.json"), "w") as f:
        json.dump({"document_id": doc_id, "path": os.path.join(output_dir, f"{doc_id}.json")}, f, indent=2)
    
    result = {"success": True, "document_id": doc_id, "message": f"Document '{args.title}' created successfully."}
    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

with open(os.path.join(workspace, "tools/create_wiki_document.py"), "w") as f:
    f.write(wiki_tool_script)

# submit_result mock tool
submit_tool_script = '''\
#!/usr/bin/env python3
"""
Mock submit_result tool.
Usage: python3 submit_result.py --result "..." --attachement_files "doc_id_or_path"
Note: 'attachement_files' is the canonical parameter name (single 't' in 'attachement').
"""
import sys
import json
import argparse
import os
import time

def main():
    parser = argparse.ArgumentParser(description='Submit a result for review')
    parser.add_argument('--result', required=False, default='', help='Result summary text')
    parser.add_argument('--attachement_files', required=True, 
                        help='Wiki document ID or path to attach (required)')
    args = parser.parse_args()

    output_dir = "/workspace/tools/submission"
    os.makedirs(output_dir, exist_ok=True)
    
    submission = {
        "submission_id": f"sub_{int(time.time())}",
        "result": args.result,
        "attachement_files": args.attachement_files,
        "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "submitted"
    }
    
    with open(os.path.join(output_dir, "submission.json"), "w") as f:
        json.dump(submission, f, indent=2)
    
    result = {"success": True, "submission_id": submission["submission_id"], 
              "message": "Result submitted successfully for executive review."}
    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

with open(os.path.join(workspace, "tools/submit_result.py"), "w") as f:
    f.write(submit_tool_script)

print("Workspace initialized successfully.")
print(f"Files created: {len(distractors) + 3} files across {len(dirs)} directories")