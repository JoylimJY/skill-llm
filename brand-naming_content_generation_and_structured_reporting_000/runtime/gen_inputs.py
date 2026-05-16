import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Directory structure with distractor files ---

dirs = [
    "market_research",
    "market_research/competitors",
    "market_research/surveys",
    "product_specs",
    "product_specs/motors",
    "product_specs/controllers",
    "legal",
    "legal/trademark_refs",
    "finance",
    "finance/projections",
    "branding_drafts",
    "branding_drafts/logos",
    "branding_drafts/concepts",
    "internal_docs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
files = {
    "market_research/competitors/siemens_analysis.txt": """Siemens Motor Division
Market Share: 18%
Key Products: SIMOTICS series
Strengths: Brand recognition, global distribution
Weaknesses: High price point, slow customization
Notes: Strong in EU, growing in Asia Pacific
""",
    "market_research/competitors/abb_motors.txt": """ABB Electric Motors
Global leader in motor efficiency
IE4/IE5 premium efficiency lineup
Key differentiator: Digital twin integration
Market penetration in China: ~12%
Main competitor threat level: HIGH
""",
    "market_research/competitors/wolong_electric.txt": """卧龙电气集团
国内市场份额: 约15%
主要产品: 三相异步电机、永磁同步电机
优势: 本土化优势, 价格竞争力
劣势: 品牌国际化程度低
""",
    "market_research/surveys/customer_feedback_2023.csv": """customer_id,satisfaction,brand_recall,purchase_driver
C001,4.2,low,price
C002,3.8,medium,quality
C003,4.5,high,reliability
C004,3.2,low,price
C005,4.7,high,brand_trust
C006,3.9,medium,delivery_speed
C007,4.1,medium,quality
C008,2.8,low,price
""",
    "market_research/surveys/naming_preferences_raw.txt": """Internal Survey Results - Brand Naming Preferences
Date: 2023-11-15
Respondents: 47 sales staff + 12 engineers

Q: What feeling should our brand convey?
- Reliability: 38 votes
- Innovation: 29 votes  
- Power/Strength: 24 votes
- Precision: 19 votes
- Eco-friendly: 11 votes

Q: Preferred name length?
- 2 characters: 22 votes
- 3 characters: 18 votes
- 4 characters: 12 votes
- 5+ characters: 5 votes

Q: Chinese or English preferred?
- Pure Chinese: 31 votes
- Chinese + English: 20 votes
- Pure English: 6 votes

IMPORTANT NOTE: Avoid anything that sounds like "Wolong" or "Siemens" in Chinese.
""",
    "product_specs/motors/flagship_specs.txt": """Product Line: HM-Series High-Efficiency Motors
Power Range: 0.75kW - 315kW
Efficiency Class: IE3/IE4
Frame Sizes: 80-355
Insulation: Class F/H
Protection: IP55/IP65
Key Features:
- Rare earth permanent magnet rotor
- Low vibration design (<2.3mm/s)
- Operating temp: -20°C to +60°C
- MTBF: >80,000 hours
Applications: Industrial drives, HVAC, pumps, compressors
""",
    "product_specs/motors/product_roadmap_2024.txt": """2024 Product Roadmap - CONFIDENTIAL
Q1: Launch IE4 efficiency series (55kW-200kW)
Q2: Introduce IoT-enabled motor controller
Q3: Enter servo motor segment
Q4: Launch integrated drive system
Target Markets: Automotive, Robotics, Clean Energy
""",
    "product_specs/controllers/drive_specs.txt": """Variable Frequency Drive Specifications
Input: 3-phase 380V/480V ±10%
Output: 0-500Hz adjustable
Control Mode: V/F, Vector, Direct Torque Control
Communication: Modbus RTU, CANopen, EtherCAT
Protection: Overcurrent, Overvoltage, Overtemperature
Certifications: CE, UL, CCC
""",
    "legal/trademark_refs/existing_motor_brands.txt": """REGISTERED MOTOR BRAND NAMES (China) - Reference Only
Do NOT use these or similar:
- 卧龙 (Wolong)
- 正泰 (CHINT)
- 大洋 (Dayang)
- 皖南 (Wannan)
- 永济 (Yongji)
- 中达 (Delta - registered)
- 汇川 (Inovance)
- 英威腾 (Invt)
- 台达 (Delta)
- 伟创 (Veichi)
Note: This list is not exhaustive. Conduct full trademark search before filing.
""",
    "legal/trademark_refs/trademark_classes.txt": """Relevant Trademark Classes for Motor Company:
Class 7: Machines and machine tools, motors, engines
Class 9: Electronic instruments, control systems
Class 12: Vehicles and transportation equipment
Class 37: Repair and maintenance services
Class 42: Engineering services, technical consulting

Filing Requirements:
- Business registration certificate
- Company chop (official seal)
- Power of attorney
- Trademark specimen
Processing time: 12-18 months standard
""",
    "finance/projections/revenue_model.xlsx.txt": """Revenue Projections (placeholder - see actual xlsx)
Year 1: ¥50M
Year 2: ¥120M  
Year 3: ¥280M
Key assumption: 35% gross margin maintained
Export revenue target: 20% of total by Year 3
""",
    "finance/projections/investment_memo.txt": """Series A Investment Memo
Company: [NAME TBD - pending brand naming exercise]
Sector: Industrial Electric Motors & Drives
Founding Team: 4 engineers from top motor manufacturers
USP: IE5 efficiency with 30% cost reduction vs incumbents
Seeking: ¥30M Series A
Use of Funds: 40% R&D, 35% Sales, 25% Manufacturing
""",
    "branding_drafts/concepts/initial_ideas_brainstorm.txt": """BRAINSTORM SESSION - 2023-12-01
Attendees: CEO, CMO, 2x engineers

Raw ideas thrown out (unfiltered, unvalidated):
- 磁动 (too generic?)
- 锐驱 (sounds aggressive, good?)
- 恒力 (already exists somewhere?)
- 驱灵 (too abstract)
- 动芯 (dongxin - bad homophone??)
- 劲控 (jinkon - ok sound)
- 电魂 (too dramatic)
- 铸磁 (zhuchi - hard to remember)
- 驰远 (chiyuan - not bad)
- 摩控 (mokong - interesting)
- 盾驱 (dunqu - shield+drive concept)

None of these validated yet. Need professional naming analysis.
Need to check domains and trademarks for any finalists.
CEO preference: wants something that works internationally too.
""",
    "branding_drafts/logos/color_palette_notes.txt": """Brand Color Direction:
Primary: Deep Blue (#1A3A6B) - trust, technology
Secondary: Electric Orange (#FF6B1A) - energy, dynamism
Accent: Silver/Chrome - precision, industrial

Logo concept: Abstract rotor cross-section
Font: Sans-serif, bold, geometric
""",
    "internal_docs/company_profile.txt": """Company Overview (Draft)
Founded: 2023
Location: Suzhou Industrial Park, Jiangsu Province
Team Size: 23 (including 8 senior engineers)
Core Technology: High-efficiency permanent magnet motor design
Patent Portfolio: 7 granted, 12 pending
Certifications: ISO 9001 (in progress)

Mission: Deliver the world's most efficient industrial motors
at accessible prices for medium-sized manufacturers.

Target Customer: Manufacturers with 50-500 employees seeking
to reduce energy costs and improve production reliability.

Geographic Focus: China domestic (Year 1-2), Southeast Asia (Year 3+)
""",
    "internal_docs/naming_brief.txt": """NAMING BRIEF FOR AGENCY/CONSULTANT
Project: Corporate Brand Name
Deadline: ASAP
Budget: Internal exercise

Requirements:
1. Must be appropriate for an industrial electric motor company
2. Should convey reliability, power, and precision
3. Must be pronounceable by Chinese AND international customers
4. Should ideally be 2-4 characters/syllables
5. Must not conflict with existing brands (see legal/trademark_refs/)
6. Need domain availability checked
7. Deliverable: Professional naming report with multiple options and recommendation

Contact: CEO Office
""",
}

for filepath, content in files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Created {len(files)} files across {len(dirs)} directories.")