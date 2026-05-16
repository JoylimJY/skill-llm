import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create distractor directory structure ---
dirs = [
    "vendor_docs/SAP",
    "vendor_docs/Oracle",
    "vendor_docs/Infor",
    "internal_reports/Q1",
    "internal_reports/Q2",
    "internal_reports/Q3",
    "it_assessments",
    "finance/budget",
    "finance/forecasts",
    "operations/current_wms",
    "operations/pain_points",
    "meetings/notes",
    "memory",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
# 1. SAP vendor brochure
(workspace / "vendor_docs/SAP/sap_ewm_overview.txt").write_text(
    """SAP Extended Warehouse Management (SAP EWM) Overview
=====================================================
Version: 9.4 / S/4HANA
License Model: Perpetual + Annual Maintenance (22% of license cost)
Typical Implementation: 14-18 months
Base License Cost (mid-size): $480,000 - $620,000
Annual Maintenance: ~$105,600 - $136,400

Key Features:
- Real-time inventory tracking
- Labor management system (LMS)
- Yard management
- Integration: Native SAP ERP, third-party via iDocs/BAPI
- Supported languages: 32
- Mobile: SAP Fiori-based apps

Reference Customers (Logistics):
- DHL Supply Chain (APAC)
- Kuehne+Nagel Germany
- Rhenus Group

Weaknesses noted by analyst Gartner 2023:
- High TCO for SMB
- Implementation complexity
- Requires certified SAP consultants (limited pool)
""", encoding="utf-8"
)

# 2. Oracle WMS brochure
(workspace / "vendor_docs/Oracle/oracle_wms_cloud.txt").write_text(
    """Oracle Warehouse Management Cloud
===================================
Version: 23D (Latest)
License Model: SaaS - per user/month + transaction fees
Pricing: $180 - $340/user/month (volume discounts available)
Estimated Annual Cost (50 users): $108,000 - $204,000
Implementation: 6-10 months (Cloud)

Key Features:
- Cloud-native, multi-tenant
- AI-powered slotting optimization
- Advanced labor management
- Integration: REST APIs, Oracle ERP native, third-party middleware
- Mobile: iOS/Android native apps

Reference Customers:
- XPO Logistics
- Americold

Weaknesses:
- Ongoing SaaS cost accumulates over years
- Data sovereignty concerns for Chinese operations
- Customization limited by SaaS model
""", encoding="utf-8"
)

# 3. Infor vendor doc
(workspace / "vendor_docs/Infor/infor_wms_specs.txt").write_text(
    """Infor WMS
=========
License: Perpetual or Cloud subscription
On-premise cost (mid-size): $220,000 - $350,000
Cloud: $85/user/month
Implementation: 8-12 months

Features:
- 3D Visual Warehouse
- Slotting and task interleaving
- RF-directed workflows
- Integration: Infor ION, REST, EDI
""", encoding="utf-8"
)

# 4. Internal requirement doc (intentionally incomplete/messy)
(workspace / "internal_reports/Q1/wms_requirements_draft_v2.txt").write_text(
    """WMS Requirements - DRAFT v2 (incomplete - needs finance review)
================================================================
Author: Operations Team
Date: 2024-03-15
Status: DRAFT - NOT FINAL

FUNCTIONAL REQUIREMENTS:
[x] Real-time inventory visibility
[x] Barcode + RFID support
[x] Multi-warehouse support (we have 3 DCs: Shanghai, Guangzhou, Chengdu)
[?] Labor management (nice-to-have? ask HR)
[x] Returns processing (critical for our e-commerce clients)
[ ] AI-based demand forecasting (future phase, not now)
[x] ERP integration (currently on SAP ECC 6.0 - upgrade to S/4HANA planned 2025)
[x] Mobile support for floor staff (~120 handheld devices)

NON-FUNCTIONAL:
- Uptime: 99.9% SLA required
- Response time: <2 sec for picking transactions
- Data residency: China (regulatory requirement for client data)

BUDGET: TBD - finance meeting on Apr 3rd
NOTE: IT says our current WMS (HighJump 7.1) end-of-life in Dec 2024
NOTE: Do NOT include AI forecasting in scope for this decision
""", encoding="utf-8"
)

# 5. Pain points summary
(workspace / "operations/pain_points/current_system_issues.txt").write_text(
    """Current WMS Pain Points (HighJump 7.1)
======================================
Compiled by: Ops Manager Li Wei
Last updated: 2024-02-28

1. System crashes during peak hours (11am-2pm, 7pm-10pm) - avg 2.3 incidents/week
2. No real-time sync with SAP ECC - batch jobs run every 2 hours, causing stock discrepancies
3. Mobile app broken since Android 12 update - staff using paper backups
4. No support for RFID (all barcode only) - losing contract bids
5. Reporting module requires IT involvement for every custom report
6. End-of-support: Dec 31, 2024 - vendor confirmed no patches after this date
7. Zero API capability - all integrations are file-based FTP

IMPACT:
- Estimated 3.2% inventory shrinkage due to stock discrepancy
- 0.8% order accuracy rate below target (99.2% vs 99.5% target  <- NOTE: this needs re-checking, might be wrong)
- Client SLA breach penalty: ¥2.3M in 2023
""", encoding="utf-8"
)

# 6. Finance budget note (conflicting numbers)
(workspace / "finance/budget/wms_budget_note_v1.txt").write_text(
    """WMS Replacement Budget - Preliminary
=====================================
Approved cap (preliminary): ¥4,500,000 total project cost
This includes: license + implementation + training + 1 year support

Note from CFO (Apr 3 meeting): 
- We can stretch to ¥5,200,000 if ROI payback < 3 years
- Prefer SaaS to minimize capex (finance policy change 2024)
- BUT: data sovereignty concern from legal team may override SaaS preference

Exchange rate used for USD conversion: 1 USD = 7.2 CNY
""", encoding="utf-8"
)

# 7. Finance forecast (distractor)
(workspace / "finance/forecasts/logistics_revenue_2024.txt").write_text(
    """Logistics Division Revenue Forecast 2024
=========================================
Q1 Actual: ¥87.3M
Q2 Forecast: ¥91.5M
Q3 Forecast: ¥96.2M
Q4 Forecast: ¥103.8M (peak season)
YTD Target: ¥378.8M

WMS downtime impact on revenue (estimated): 
- Each hour of peak downtime = ¥1.2M revenue at risk
""", encoding="utf-8"
)

# 8. IT assessment
(workspace / "it_assessments/infrastructure_compatibility.txt").write_text(
    """IT Infrastructure Compatibility Assessment
==========================================
Author: IT Architecture Team
Date: 2024-04-10

Current State:
- ERP: SAP ECC 6.0 (upgrade to S/4HANA planned Q3 2025)
- Network: Fiber backbone, 1Gbps inter-DC links
- Servers: On-premise VMware cluster (Shanghai DC is primary)
- Cloud policy: Hybrid allowed, but customer data must stay on-premise or in China sovereign cloud

WMS Integration Assessment:
- SAP EWM: Native integration with ECC + S/4HANA. RECOMMENDED by IT.
  Risk: Timeline overlap with S/4HANA upgrade project.
- Oracle WMS Cloud: REST API integration tested in POC. Works but requires 
  middleware layer. Data residency: Oracle China region available (Chengdu).
  Risk: SaaS cost grows with transaction volume.
- Infor WMS: EDI/file-based only for ECC. Would need upgrade for REST.
  NOT RECOMMENDED by IT for our architecture.

Recommendation: SAP EWM or Oracle WMS Cloud shortlisted.
Infor eliminated from consideration.
""", encoding="utf-8"
)

# 9. Meeting notes (distractor)
(workspace / "meetings/notes/wms_steering_committee_2024-04-15.txt").write_text(
    """WMS Steering Committee Meeting Notes
=====================================
Date: April 15, 2024
Attendees: CEO, CFO, COO, IT Director, Operations Manager

Decisions:
1. Deadline for WMS selection: June 30, 2024
2. Go-live target: October 31, 2024 (before peak season)
3. Shortlist confirmed: SAP EWM vs Oracle WMS Cloud
4. Infor eliminated (IT assessment)
5. Request for Proposal (RFP) to be sent to SAP and Oracle by May 1

Open Issues:
- Need formal ROI analysis
- Data sovereignty legal opinion pending
- S/4HANA upgrade timeline conflict with SAP EWM (IT to resolve)
""", encoding="utf-8"
)

# 10. Operations current WMS config (distractor)
(workspace / "operations/current_wms/highjump_config_export.txt").write_text(
    """HighJump WMS 7.1 Configuration Export
=====================================
[SYSTEM]
version=7.1.4.2209
license_type=perpetual
license_expiry=2024-12-31
support_expiry=2024-12-31

[WAREHOUSES]
DC_001=Shanghai_Pudong; zones=12; locations=8420; staff=87
DC_002=Guangzhou_Nansha; zones=8; locations=5200; staff=54
DC_003=Chengdu_Longquanyi; zones=6; locations=3800; staff=41

[INTEGRATIONS]
erp_type=SAP_ECC_60
sync_method=FTP_BATCH
sync_interval=120min
rfid_enabled=false
mobile_platform=Android_7_ONLY
""", encoding="utf-8"
)

# 11. Q3 report distractor
(workspace / "internal_reports/Q3/q3_operations_kpi.txt").write_text(
    """Q3 2024 Operations KPI Report
==============================
Order Accuracy: 99.21% (Target: 99.5%) - BELOW TARGET
On-Time Dispatch: 97.8% (Target: 98.5%) - BELOW TARGET
Inventory Accuracy: 96.8% (Target: 99%) - SIGNIFICANTLY BELOW TARGET
WMS Uptime: 94.2% (Target: 99.9%) - CRITICAL

Root cause analysis attributes 71% of KPI misses to WMS limitations.
""", encoding="utf-8"
)

# 12. Partial ROI analysis (messy, incomplete)
(workspace / "finance/budget/roi_analysis_draft.txt").write_text(
    """WMS ROI Analysis - INCOMPLETE DRAFT
=====================================
NOTE: Numbers below are ESTIMATES only, pending vendor quotes

Scenario A: SAP EWM (On-Premise)
- Year 0 capex: ~¥4,500,000 (license + impl, using ¥480k USD * 7.2 + ¥100k impl)
  CORRECTION NEEDED: IT estimates impl cost at ¥1,800,000 not ¥100k
  REVISED Year 0: ~¥5,256,000 (may exceed budget cap - needs CFO approval)
- Annual maintenance: ~¥950,000/year
- Expected savings: ¥3,200,000/year (SLA penalties + shrinkage reduction)
- Payback: ~2.2 years on savings alone

Scenario B: Oracle WMS Cloud (SaaS)
- Year 0 cost: ~¥800,000 (implementation only)
- Annual subscription: 50 users * ¥1,800/month * 12 = ¥1,080,000/year
  NOTE: Transaction fees not yet calculated
- Expected savings: Same as above ¥3,200,000/year
- Payback: ~0.7 years (Year 0 only) then net positive
- 5-year TCO: ~¥6,200,000 vs SAP EWM ~¥9,500,000

*** DATA SOVEREIGNTY: Legal opinion not yet received ***
*** If Oracle China region approved, Oracle wins on TCO ***
*** If rejected, SAP EWM is only viable option ***
""", encoding="utf-8"
)

# 13. Empty memory directory placeholder (agent should write here)
(workspace / "memory" / ".gitkeep").write_text("", encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")