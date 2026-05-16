import os
import json
import random

random.seed(42)

base = "/workspace"

# Create distractor directory structure
dirs = [
    "admin/contracts",
    "admin/hr",
    "lab/experiments/batch_2023",
    "lab/experiments/batch_2024",
    "lab/publications",
    "market_research/competitors",
    "market_research/surveys",
    "funding/grants",
    "funding/investors",
    "team_profiles",
    "legal/ip_filings",
    "references",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Distractor files - realistic but irrelevant
distractor_files = {
    "admin/contracts/lab_lease_2024.txt": """LABORATORY LEASE AGREEMENT
Tsinghua University - Building C, Room 304
Tenant: Professor Zhang Wei's Research Group
Duration: 2024-01-01 to 2026-12-31
Monthly fee: RMB 8,000
Equipment covered: Cell culture facility, biosafety cabinet
Signed: 2023-12-15""",

    "admin/hr/hiring_plan_Q1.txt": """Q1 Hiring Plan
Position 1: Senior Research Scientist (Biomedical)
Position 2: Business Development Manager
Position 3: Lab Technician x2
Budget allocated: RMB 1,200,000/year
Note: Priority hire for commercial team""",

    "admin/hr/employee_handbook_draft.txt": """DRAFT - Employee Handbook v0.3
Chapter 1: Work Hours
Chapter 2: Leave Policy
Chapter 3: IP Ownership
NOTE: All IP developed during employment belongs to the company
TODO: Legal review pending""",

    "lab/experiments/batch_2023/results_summary.csv": """experiment_id,date,scaffold_type,viability_%,notes
EXP001,2023-03-15,collagen_type_I,87.3,baseline
EXP002,2023-04-20,fibronectin,91.2,improved
EXP003,2023-06-10,hybrid_v1,94.8,best result so far
EXP004,2023-08-30,hybrid_v2,96.1,patent pending""",

    "lab/experiments/batch_2024/preliminary_data.txt": """Batch 2024 - Preliminary Results
3D cell culture scaffold technology
- Biodegradable polymer matrix: PASS
- In-vitro validation: PASS
- Animal model testing: IN PROGRESS (expected Q3 2024)
- GMP compatibility: NOT YET ASSESSED
Current TRL estimate: somewhere between lab and prototype, not yet clinical""",

    "lab/publications/paper_list.txt": """Published Papers - Prof. Chen Lihua
1. 'Novel 3D Scaffold for Hepatocyte Culture' - Nature Biomedical Engineering, 2022, IF=29.1
2. 'Biodegradable Polymer Matrix for Organ-on-Chip' - Biomaterials, 2023, IF=14.3
3. 'Scale-up Challenges in 3D Cell Culture' - Advanced Healthcare Materials, 2024 (in press)
Citation count: 847 total
H-index: 23""",

    "market_research/competitors/competitor_analysis_v2.txt": """COMPETITOR LANDSCAPE - 3D Cell Culture Market
1. Organovo (USA) - bioprinting, market cap $80M, focus: liver tissue
2. InVitria (USA) - cell culture media, $45M revenue
3. REPROCELL (Japan) - human tissue for drug testing
4. Domestic competitors: minimal, market gap identified
Market size: $2.1B global, growing 15% YoY
Key pain point: drug companies need human-relevant models to reduce animal testing
Regulatory: FDA encouraging organ-on-chip adoption (2023 FDA Modernization Act)""",

    "market_research/surveys/pharma_customer_interviews.txt": """Customer Discovery Interviews - Summary
Conducted: Oct-Nov 2023, n=12 pharma companies
Key findings:
- 9/12 companies currently using animal models, frustrated with translation rate
- 7/12 willing to pay premium for validated human 3D models
- Pain point: current vendors lack standardization and reproducibility
- Budget: $50K-200K per year per application area
- Decision maker: Head of DMPK / Preclinical Research VP
- Sales cycle estimate: 6-18 months (long procurement process)""",

    "funding/grants/nsfc_grant_2024.txt": """NSFC Grant Application - Project Summary
Project Title: Biomimetic 3D Scaffold for Drug Discovery Applications
Principal Investigator: Prof. Chen Lihua
Co-PI: Dr. Wang Fang (postdoc)
Amount requested: RMB 2,800,000
Duration: 4 years (2024-2028)
Status: APPROVED - March 2024
Note: IP generated under this grant - university ownership, licensing possible""",

    "funding/investors/vc_meeting_notes.txt": """VC Meeting Notes - Various Investors
1. Sequoia China (Dec 2023): Interested but want to see animal data first
2. Qiming Ventures (Jan 2024): Passed - too early stage
3. 5Y Capital (Feb 2024): Interested in Series A when ready, likes team
4. Matrix Partners (Mar 2024): Wants to see commercial traction first
General feedback: Technology is strong, need proof of commercial viability""",

    "team_profiles/professor_chen.txt": """Name: Chen Lihua (陈丽华)
Title: Associate Professor, Dept. of Biomedical Engineering, Tsinghua University
Age: 42
Research focus: 3D cell culture, biomaterials, organ-on-chip
Key achievement: Core inventor of hybrid scaffold technology (patent CN202310XXXX)
Industry experience: None (pure academic background)
Startup involvement: First time considering commercialization
Willingness to take CEO role: Uncertain, prefers technical leadership
Available time for startup: 30-40% (still running lab and teaching 2 courses)""",

    "team_profiles/student_zhao.txt": """Name: Zhao Mingyu (赵明宇)
Status: PhD Candidate, Year 4, Prof. Chen's lab
Age: 27
Technical expertise: Expert in scaffold fabrication, cell biology protocols
Previous experience: 6-month internship at pharmaceutical company (GSK China)
Business exposure: Participated in 3 business plan competitions, finalist in 清华挑战杯
Entrepreneurial interest: HIGH - wants to be CEO/co-founder
Availability: Flexible, willing to dedicate full time post-graduation (graduation: June 2024)
Networks: Some pharma industry contacts from internship""",

    "team_profiles/student_liu.txt": """Name: Liu Yanran (刘艳然)
Status: MBA Student (Tsinghua SEM), Year 2
Age: 29  
Background: 4 years in McKinsey healthcare practice before MBA
Technical knowledge: Limited, but strong in business strategy
Relationship to lab: No prior connection to Prof. Chen's lab
Interest: Looking for deep-tech startup opportunity
Availability: Full time after graduation (July 2024)
Skills: Business development, fundraising, strategy, pharma industry relationships""",

    "legal/ip_filings/patent_summary.txt": """IP Portfolio Summary
Patent 1: CN202310XXXX - 'Hybrid Biodegradable Scaffold Composition'
  Status: Granted (2024-01)
  Owner: Tsinghua University
  Inventors: Chen Lihua, Zhao Mingyu, Wang Fang
  Licensing: Available for exclusive license to spinout

Patent 2: CN202410XXXX - 'Manufacturing Process for 3D Cell Culture Scaffold'
  Status: Pending (filed 2024-03)
  Owner: Tsinghua University
  Inventors: Chen Lihua, Zhao Mingyu

Technology Transfer Office contact: tech_transfer@tsinghua.edu.cn
License fee structure: 2% royalty on net sales + upfront fee RMB 500K""",

    "references/framework_notes_draft.txt": """INCOMPLETE NOTES - Framework Research
- Read about different startup models from labs
- Some notes on how professors vs students lead companies
- Need to systematically evaluate which model fits us
- Found reference to x-lab framework but didn't finish reading
TODO: Complete this analysis before next team meeting""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(base, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)

# THE CORE INPUT: A messy, unstructured project brief that the agent must analyze
project_brief = """PROJECT BRIEF - CONFIDENTIAL DRAFT (NOT FOR DISTRIBUTION)
Last updated: 2024-05-10
Prepared by: Team (messy notes, needs proper analysis)

=== THE SITUATION ===
Prof. Chen Lihua has developed a breakthrough 3D cell culture scaffold technology over 8 years in her Tsinghua lab. 
The tech is genuinely novel (top journals, granted patent) but we're still at animal model testing stage - NOT ready for clinical yet.
The pharma market really needs this - we've done customer interviews and the demand is clear.

This is NOT a quick-win technology. Getting from current stage to a sellable product will take 3-5 years minimum.
We know the application area clearly: drug toxicity testing for pharma companies (organ-on-chip direction).

=== THE TEAM SITUATION ===
- Prof. Chen: wants to stay involved but not sure about being CEO. She'll definitely drive the technical direction.
  She and Zhao Mingyu have worked together for 4 years in the lab - very strong trust relationship.
- Zhao Mingyu: PhD student in the lab, graduating soon, willing to go full-time, has some pharma exposure
- Liu Yanran: MBA student, NOT from the lab, strong business background, wants to join

Professor and Zhao trust each other completely from years of lab work.
Zhao and Liu don't know each other well yet.
Prof. Chen and Zhao BOTH want to be central to the company, not just advisors.

=== THE PROBLEMS WE NEED HELP WITH ===
Problem A: We keep arguing about who should be in charge - Prof Chen thinks she should lead strategy, 
  Zhao thinks he should be CEO since he'll be full time. Liu thinks the business person should lead commercial.
  
Problem B: Our technology is great in the lab but we have NO idea how to make it into a real product. 
  The gap between our lab results and something pharma companies can actually buy feels enormous.
  
Problem C: We're not sure whether our technology should drive what product we make, or whether we 
  should start from what pharma companies want and then figure out the tech. 

=== WHAT WE NEED ===
Someone to give us a structured advisory analysis covering:
1. What team/leadership model we should adopt (with clear reasoning)
2. Specific role assignments for each team member (Prof Chen, Zhao Mingyu, Liu Yanran)  
3. Solutions to our three specific problems
4. A startup implementation roadmap we can follow
5. A checklist of success factors we need to address
"""

with open(os.path.join(base, "project_brief.txt"), 'w', encoding='utf-8') as f:
    f.write(project_brief)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files)} distractor files + 1 project brief")