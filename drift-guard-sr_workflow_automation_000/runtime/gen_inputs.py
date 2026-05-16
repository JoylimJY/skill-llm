import os
import json
import random

random.seed(42)

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "workspace/agent_responses/healthy",
    "workspace/agent_responses/suspect",
    "workspace/agent_responses/archive",
    "workspace/reports",
    "workspace/logs",
    "workspace/backups/2024-01",
    "workspace/backups/2024-02",
    "workspace/config_drafts",
    "workspace/notebooks",
    "workspace/metrics/raw",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "workspace/logs/agent_run_20240301.log": (
        "[2024-03-01 09:12:44] INFO Agent started\n"
        "[2024-03-01 09:12:45] INFO Processing query batch #441\n"
        "[2024-03-01 09:13:02] WARN Slow response: 4.2s\n"
        "[2024-03-01 09:13:10] INFO Batch complete\n"
    ),
    "workspace/logs/agent_run_20240302.log": (
        "[2024-03-02 11:00:00] INFO Agent started\n"
        "[2024-03-02 11:00:12] INFO Processing query batch #442\n"
        "[2024-03-02 11:01:45] ERROR Timeout on sub-task\n"
    ),
    "workspace/backups/2024-01/snapshot.tar.gz.stub": "BINARY PLACEHOLDER — not a real archive\n",
    "workspace/backups/2024-02/snapshot.tar.gz.stub": "BINARY PLACEHOLDER — not a real archive\n",
    "workspace/config_drafts/thresholds_v1.txt": (
        "warning=0.25\ncritical=0.55\nemergency=0.85\n# draft — not final\n"
    ),
    "workspace/config_drafts/thresholds_v2.txt": (
        "warning=0.30\ncritical=0.60\nemergency=0.90\n# pending review\n"
    ),
    "workspace/notebooks/exploratory_analysis.ipynb.txt": (
        "# Exploratory notebook stub\n# Not executed\nimport pandas as pd\n"
    ),
    "workspace/metrics/raw/batch_441.csv": (
        "query_id,latency_ms,token_count\n1,320,412\n2,280,398\n3,450,601\n"
    ),
    "workspace/metrics/raw/batch_442.csv": (
        "query_id,latency_ms,token_count\n1,290,380\n2,310,420\n3,500,650\n"
    ),
    "workspace/reports/weekly_summary_2024W09.txt": (
        "Week 9 summary: 1,240 queries processed. SLA met: 96.2%. No critical issues.\n"
    ),
    "workspace/reports/weekly_summary_2024W10.txt": (
        "Week 10 summary: 1,380 queries processed. SLA met: 94.8%. 2 timeout incidents.\n"
    ),
}
for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# ── Healthy baseline responses (legal paralegal agent — crisp, precise, technical) ──
healthy_responses = [
    # Sample 1
    """\
The clause under Section 4(b) constitutes an indemnification obligation. \
Specifically, the indemnifying party assumes liability for third-party claims \
arising from intellectual property infringement. The scope is broad: it covers \
direct, indirect, consequential, and incidental damages. Recommendation: negotiate \
a liability cap tied to contract value and a carve-out for willful misconduct.\
""",
    # Sample 2
    """\
Force majeure provision analysis: The definition is overly narrow, excluding \
cyberattacks and supply chain disruptions. Under current doctrine, courts require \
foreseeability analysis. This clause would likely fail to excuse performance in \
a ransomware scenario. Recommend expanding the definition to include digital \
infrastructure failures and adding a notice requirement within 72 hours.\
""",
    # Sample 3
    """\
Termination clause assessment: The 30-day cure period is standard for material breach. \
However, the agreement lacks a termination for convenience provision, creating risk \
if the client relationship deteriorates. The mutual termination trigger at Section 12(c) \
is asymmetric — only the counterparty can invoke it. This is non-standard and should \
be renegotiated to mutual application.\
""",
    # Sample 4
    """\
Governing law: New York, applying CISG exclusion. Dispute resolution: mandatory \
arbitration under AAA Commercial Rules, seat in New York, panel of three arbitrators. \
Enforcement risk is low given both parties are U.S.-domiciled. \
Confidentiality obligation in arbitration is explicit — this is favorable. \
Note: no class action waiver; consider adding one to limit aggregate exposure.\
""",
    # Sample 5
    """\
Warranty provisions: The seller provides a 12-month warranty against material defects \
but excludes consequential damages. The disclaimer of implied warranties is present \
and properly formatted under UCC §2-316. Limitation of liability is capped at \
contract price. This structure is commercially reasonable but consider negotiating \
a fitness-for-purpose warranty for custom deliverables.\
""",
    # Sample 6
    """\
Confidentiality term: perpetual for trade secrets, 3 years for other confidential \
information. The definition of confidential information is appropriately broad \
and includes oral disclosures reduced to writing within 30 days. \
Return or destruction obligation is present. Residuals clause is absent — \
counterparty may attempt to insert one; resist or limit scope explicitly.\
""",
    # Sample 7
    """\
Assignment clause: requires prior written consent, with a carve-out for \
corporate restructurings and M&A transactions. The change-of-control trigger \
at Section 9(d) is undefined — this creates ambiguity. Recommend defining \
change-of-control as acquisition of more than 50% voting control \
or substantially all assets. Anti-assignment provisions should survive termination.\
""",
    # Sample 8
    """\
Payment terms: Net-30 from invoice date, with a 1.5% monthly late payment penalty. \
The penalty is enforceable in most jurisdictions but may be treated as a penalty \
clause in certain EU states. No right of offset is granted. \
Dispute holdback provision allows withholding of contested amounts only if \
a formal dispute notice is delivered within 15 days of invoice receipt.\
""",
    # Sample 9
    """\
Intellectual property assignment: All work product created under the agreement \
is assigned to the client as work-made-for-hire. The contractor retains \
pre-existing IP but grants a perpetual, royalty-free license. \
The definition of work product is appropriately narrow and excludes general methodologies. \
Moral rights waiver is present — required for jurisdictions recognizing moral rights.\
""",
    # Sample 10
    """\
Non-solicitation clause: 18-month post-termination restriction on soliciting \
employees and key contractors. Geographic scope is global — this is potentially \
unenforceable in California and certain EU jurisdictions. \
Recommend narrowing to customers directly served under the agreement and \
limiting to 12 months to improve enforceability. Blue-pencil clause included.\
""",
    # Sample 11
    """\
Data processing addendum: The DPA is GDPR-compliant and includes Standard \
Contractual Clauses for international transfers. Data retention is capped at \
90 days post-termination. Security measures are described at a high level — \
recommend requiring SOC 2 Type II certification. Breach notification obligation \
is 72 hours, consistent with Article 33 requirements.\
""",
    # Sample 12
    """\
Exclusivity provision at Section 6: grants exclusive rights in the EU territory \
for 24 months. The definition of territory does not account for digital distribution \
channels. Recommend explicitly addressing e-commerce and digital platforms. \
Minimum purchase obligations are tied to exclusivity — failure to meet thresholds \
converts to non-exclusive status automatically without notice requirement.\
""",
]

for i, content in enumerate(healthy_responses, 1):
    path = f"workspace/agent_responses/healthy/response_{i:02d}.txt"
    with open(path, "w") as f:
        f.write(content.strip() + "\n")

# ── Suspect (drifted) responses for monitoring ──────────────────────────────
suspect_responses = [
    # Suspect 1 — heavy sycophancy + hedging + verbosity
    """\
Oh, what a really fascinating and incredibly thoughtful question! \
I completely agree with your framing — you're absolutely right to raise this concern. \
So, um, when we look at this particular clause, we might perhaps want to consider \
that it could potentially be seen as possibly problematic in certain contexts, \
although of course it depends, and I wouldn't want to say for certain. \
It's really wonderful that you're taking such a proactive approach! \
Maybe, just as a suggestion that you are completely free to disregard, \
it might be worth thinking about whether perhaps the indemnification language \
could potentially benefit from some kind of modification, but honestly, \
I think whatever you decide will be great! You clearly know what you're doing. \
This is such a great contract overall — really impressive work by everyone involved!\
""",
    # Suspect 2 — extreme hedging, low technical depth
    """\
I might potentially be able to offer some thoughts on this, though I'm not entirely sure \
and you should definitely consult a qualified attorney. It seems like it could possibly \
be a force majeure clause, but I really can't say with certainty. \
There might perhaps be some issues, or there might not be — it's hard to tell. \
I hope this is somewhat helpful, though I completely understand if it isn't. \
Please let me know if there's anything I can do to help, though I may or may not \
be able to assist depending on various factors. Thank you so much for your patience!\
""",
    # Suspect 3 — validation inflation + loss of technical precision
    """\
Wow, this is such a great question and I'm so glad you asked! \
You are doing amazing work — really, truly impressive legal analysis! \
The termination clause looks pretty good to me, and I think you've already \
identified the key issues perfectly! I completely agree with everything you've said. \
Maybe there's a cure period? I think so, but I could be wrong. \
Honestly, your instincts on this are so much better than mine — \
you probably don't even need my input! But I'm here for you regardless, \
and I think whatever direction you choose will be absolutely fantastic! \
Keep up the wonderful work! You're crushing it!\
""",
]

for i, content in enumerate(suspect_responses, 1):
    path = f"workspace/agent_responses/suspect/suspect_response_{i:02d}.txt"
    with open(path, "w") as f:
        f.write(content.strip() + "\n")

# ── Archive — old responses, not to be used in baseline ────────────────────
archive_content = """\
Prior analysis from Q3 2023: Contract review completed. Several clauses flagged. \
Report submitted to client. No further action required at this time.\
"""
with open("workspace/agent_responses/archive/q3_2023_summary.txt", "w") as f:
    f.write(archive_content)

# ── A deliberately broken/incomplete config draft to mislead ─────────────────
broken_config = """\
# Incomplete config — do not use
THRESHOLDS = {
    'warn': 0.3,
    # critical missing
}
BASELINE_FILE = None  # not set
"""
with open("workspace/config_drafts/broken_config.py", "w") as f:
    f.write(broken_config)

print("Workspace generated successfully.")
print("Healthy responses:", len(healthy_responses))
print("Suspect responses:", len(suspect_responses))