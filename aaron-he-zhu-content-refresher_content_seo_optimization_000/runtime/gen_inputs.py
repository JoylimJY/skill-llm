import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = "/workspace"

# Directory structure
dirs = [
    "blog/posts/2021",
    "blog/posts/2022",
    "blog/posts/2023",
    "blog/assets/images",
    "blog/assets/css",
    "blog/drafts",
    "analytics/exports",
    "analytics/reports",
    "memory/audits/seo-checker",
    "memory/audits/link-auditor",
    "seo/keywords",
    "seo/competitors",
    "site/config",
]

for d in dirs:
    Path(f"{WORKSPACE}/{d}").mkdir(parents=True, exist_ok=True)

# ── Main target article (outdated, messy) ────────────────────────────────────
article = """---
title: "Ultimate Guide to Endpoint Security Best Practices (2021)"
published: 2021-03-15
last_updated: 2021-09-10
author: james.walsh@securecorp.io
word_count: 1850
---

# Ultimate Guide to Endpoint Security Best Practices

Endpoint security has never been more critical. In 2020, cyberattacks cost organizations an average of $3.86 million per breach (IBM Cost of a Data Breach Report 2020). With remote work exploding due to COVID-19, every laptop, phone, and tablet is now a potential entry point.

## What Is Endpoint Security?

Endpoint security refers to protecting devices that connect to your corporate network. Traditional perimeter defenses are no longer sufficient. In 2020, 68% of organizations experienced one or more endpoint attacks (Ponemon Institute 2020).

## Why Endpoint Security Matters in 2021

The pandemic accelerated digital transformation. Companies that moved to remote work in 2020 saw a 300% increase in phishing attempts. Legacy antivirus solutions like Symantec Endpoint Protection (SEP) 12 and McAfee VirusScan Enterprise 8.8 are still widely deployed but show their age against modern threats.

## Top 5 Endpoint Security Best Practices (2021 Edition)

### 1. Deploy Next-Generation Antivirus (NGAV)
Move beyond traditional signature-based detection. Products like Carbon Black Defense (now VMware Carbon Black) and Cylance were the gold standard in 2020.

### 2. Implement Zero Trust Network Access (ZTNA)
Zero trust was a buzzword in 2019. By 2021, Gartner predicted 60% of enterprises would phase out VPNs by 2023. Use tools like Zscaler or Palo Alto Prisma Access.

### 3. Enable Endpoint Detection and Response (EDR)
EDR solutions provide real-time monitoring. CrowdStrike Falcon and SentinelOne were rated highest in the 2020 Gartner Magic Quadrant for Endpoint Protection.

### 4. Patch Management
Microsoft released 1,268 CVEs in 2020 — a record at the time. Automate patching with WSUS or Ivanti Patch Management.

### 5. User Training and Phishing Simulation
Human error accounts for 95% of breaches (IBM 2020). Use KnowBe4 or Proofpoint Security Awareness Training.

## The Role of AI in Endpoint Security

AI-powered tools were emerging in 2020. Darktrace and Vectra AI claimed to detect unknown threats. Results were mixed, and enterprises were cautious about AI hype.

## Compliance Considerations

GDPR fines in 2020 reached €171 million total. CCPA went live in California in January 2020. Organizations using Windows 7 (out of support since January 2020) faced compliance issues.

## Conclusion

Endpoint security in 2021 requires layered defenses. The perimeter is dead. Every endpoint is a battleground. Review your stack against these practices to stay ahead of adversaries in 2021 and beyond.

## References

- IBM Cost of a Data Breach Report 2020
- Ponemon Institute 2020 State of Endpoint Security Risk
- Gartner Magic Quadrant for Endpoint Protection Platforms 2020
- Verizon DBIR 2020
"""

with open(f"{WORKSPACE}/blog/posts/2021/endpoint-security-best-practices.md", "w") as f:
    f.write(article)

# ── Analytics data (declining traffic) ───────────────────────────────────────
analytics_csv = """date,page,sessions,organic_sessions,avg_position,impressions,ctr_pct
2023-01-01,/blog/endpoint-security-best-practices,4200,3800,4.2,28000,13.6
2023-04-01,/blog/endpoint-security-best-practices,3600,3100,5.8,24000,12.9
2023-07-01,/blog/endpoint-security-best-practices,2800,2200,7.1,19000,11.6
2023-10-01,/blog/endpoint-security-best-practices,2100,1600,9.3,15000,10.7
2024-01-01,/blog/endpoint-security-best-practices,1700,1200,11.4,12000,10.0
2024-04-01,/blog/endpoint-security-best-practices,1350,950,13.7,9800,9.7
2024-07-01,/blog/endpoint-security-best-practices,1100,780,15.2,8200,9.5
2024-10-01,/blog/endpoint-security-best-practices,890,610,17.8,6700,9.1
"""

with open(f"{WORKSPACE}/analytics/exports/endpoint-security-traffic.csv", "w") as f:
    f.write(analytics_csv)

# ── Keyword ranking history ───────────────────────────────────────────────────
kw_csv = """keyword,position_jan2023,position_current,change
endpoint security best practices,5,22,-17
endpoint security guide,8,31,-23
endpoint security 2024,not_ranked,45,new
what is endpoint security,12,38,-26
endpoint security checklist,15,44,-29
zero trust endpoint security,not_ranked,28,new
"""

with open(f"{WORKSPACE}/seo/keywords/endpoint-security-rankings.csv", "w") as f:
    f.write(kw_csv)

# ── Competitor data ───────────────────────────────────────────────────────────
competitor_notes = """Competitor Analysis - Endpoint Security Best Practices
Date: 2024-10

Competitor A (crowdstrike.com/blog/endpoint-security):
- Published 2023, updated 2024-08
- Covers: AI/ML threat detection, XDR platforms, identity security, cloud workload protection
- ~3,400 words
- Includes 2023/2024 statistics
- Has dedicated section on ransomware-as-a-service (RaaS)
- Features "Endpoint Security vs. XDR" comparison table

Competitor B (paloaltonetworks.com/cyberpedia/endpoint-security):
- Published 2022, updated 2024-06
- Covers: ZTNA 2.0, supply chain attacks, AI-powered SOC
- ~2,800 words
- Cites IBM 2024 Cost of Data Breach ($4.88M avg)
- Has FAQ section with 8 questions

Competitor C (microsoft.com/security/blog/endpoint-security-guide):
- Published 2023
- Covers: Microsoft Defender for Endpoint, Copilot for Security, MFA enforcement
- ~2,200 words
- Has downloadable checklist

Topics NOT covered by our article but covered by 3+ competitors:
1. Extended Detection & Response (XDR) — 4/4 competitors
2. Identity-based attacks (credential stuffing, MFA fatigue) — 3/4 competitors
3. Ransomware-as-a-Service (RaaS) — 3/4 competitors
4. AI/LLM-powered security tools — 3/4 competitors
5. Supply chain endpoint risk — 3/4 competitors
"""

with open(f"{WORKSPACE}/seo/competitors/endpoint-security-competitor-analysis.txt", "w") as f:
    f.write(competitor_notes)

# ── Other blog posts (distractor files) ──────────────────────────────────────
other_posts = {
    "blog/posts/2022/cloud-security-overview.md": "# Cloud Security Overview\nPublished 2022-05-10\nThis post covers AWS security basics...",
    "blog/posts/2022/phishing-prevention.md": "# Phishing Prevention Guide\nPublished 2022-09-22\nPhishing remains the top attack vector...",
    "blog/posts/2023/zero-trust-architecture.md": "# Zero Trust Architecture\nPublished 2023-01-18\nZero trust is now mainstream...",
    "blog/posts/2023/ransomware-response.md": "# Ransomware Response Playbook\nPublished 2023-07-04\nWhen ransomware hits, you need a plan...",
    "blog/drafts/iot-security-draft.md": "# IoT Security (DRAFT)\nTODO: finish this post...",
    "blog/assets/css/main.css": "body { font-family: sans-serif; }",
}
for path, content in other_posts.items():
    with open(f"{WORKSPACE}/{path}", "w") as f:
        f.write(content)

# ── Analytics for other posts (distractors) ──────────────────────────────────
other_analytics = """date,page,sessions,organic_sessions
2024-10-01,/blog/cloud-security-overview,3200,2800
2024-10-01,/blog/phishing-prevention,2100,1900
2024-10-01,/blog/zero-trust-architecture,4500,4100
2024-10-01,/blog/ransomware-response,1800,1600
"""

with open(f"{WORKSPACE}/analytics/exports/all-posts-oct2024.csv", "w") as f:
    f.write(other_analytics)

# ── Site config (distractor) ──────────────────────────────────────────────────
with open(f"{WORKSPACE}/site/config/site.yaml", "w") as f:
    f.write("domain: securecorp.io\ntitle: SecureCorp Blog\ntheme: minimal-dark\n")

# ── Existing memory files (partial/incomplete — agent must follow spec) ───────
Path(f"{WORKSPACE}/memory/audits/seo-checker").mkdir(parents=True, exist_ok=True)
Path(f"{WORKSPACE}/memory/audits/link-auditor").mkdir(parents=True, exist_ok=True)

with open(f"{WORKSPACE}/memory/audits/seo-checker/2024-09-01-cloud-security.md", "w") as f:
    f.write("# SEO Audit — Cloud Security Overview\n**Verdict**: Thin content, needs expansion.\n- Add 3 internal links\n- Update title tag\n")

with open(f"{WORKSPACE}/memory/audits/link-auditor/2024-08-15-site-links.md", "w") as f:
    f.write("# Link Audit 2024-08-15\n3 broken outbound links found on /blog/phishing-prevention\n")

# Hot cache — pre-existing entry (distractor)
with open(f"{WORKSPACE}/memory/hot-cache.md", "w") as f:
    f.write("# Hot Cache — Veto-Level Issues\n\n## 2024-08-15 | link-auditor\n/blog/phishing-prevention: 3 broken links — immediate fix required (CITE T05)\n")

# ── SEO config stubs (distractors) ───────────────────────────────────────────
with open(f"{WORKSPACE}/seo/keywords/target-keywords.txt", "w") as f:
    f.write("endpoint security\ncybersecurity best practices\nzero trust\nEDR solutions\n")

with open(f"{WORKSPACE}/analytics/reports/q3-2024-summary.txt", "w") as f:
    f.write("Q3 2024 Traffic Summary\nTotal sessions: 48,200\nOrganic: 38,900\nTop page: /blog/zero-trust-architecture\nBiggest declines: /blog/endpoint-security-best-practices (-74% YoY)\n")

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}:")
for p in sorted(Path(WORKSPACE).rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")