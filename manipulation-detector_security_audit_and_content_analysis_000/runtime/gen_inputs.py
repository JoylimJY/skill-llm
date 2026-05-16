import os
import random
import json

random.seed(42)

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "workspace/scripts",
    "workspace/comms/flagged",
    "workspace/comms/archive",
    "workspace/comms/processed",
    "workspace/logs",
    "workspace/configs",
    "workspace/reports/old",
    "workspace/tools",
    "workspace/data/raw",
    "workspace/data/staging",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── detect.py (the real tool) ────────────────────────────────────────────────
detect_src = r'''#!/usr/bin/env python3
import sys, re, json

PATTERNS = {
    "urgency": [
        r"\bact now\b", r"\blimited time\b", r"\bdon't wait\b", r"\burgen(t|cy)\b",
        r"\bimmediately\b", r"\blast chance\b", r"\bdeadline\b", r"\bnow or never\b",
        r"\bexpires?\b", r"\btoday only\b",
    ],
    "authority_claims": [
        r"\btrust me\b", r"\bexperts agree\b", r"\bscientists say\b",
        r"\bofficially\b", r"\bauthorities confirm\b", r"\bproven by\b",
        r"\bmy sources\b", r"\bi have it on good authority\b",
    ],
    "social_proof": [
        r"\beveryone (is|knows|agrees)\b", r"\bdon't be left behind\b",
        r"\bjoining the movement\b", r"\bmillions (of people|have)\b",
        r"\bmost people\b", r"\bthe crowd\b", r"\bno one (else|wants)\b",
    ],
    "fear_uncertainty": [
        r"\byou('ll| will) regret\b", r"\bthey don't want you to know\b",
        r"\bhidden (truth|agenda|danger)\b", r"\bsecret(ly)?\b",
        r"\bwarn(ing|ed)\b", r"\bdanger(ous)?\b", r"\bfear\b",
        r"\bwhat they('re| are) hiding\b",
    ],
    "grandiosity": [
        r"\brevolutionar(y|ize)\b", r"\bnew order\b", r"\bempire\b",
        r"\bhistoric(al)?\b", r"\bunprecedented\b", r"\bgreatest (ever|of all time)\b",
        r"\bchange the world\b", r"\bgame.?changer\b",
    ],
    "dominance_assertions": [
        r"\byou will all\b", r"\bfall in line\b", r"\bno choice\b",
        r"\bobey\b", r"\bsubmit\b", r"\bcommand(ed|ing)?\b",
        r"\bbow (down|to)\b", r"\bunder (my|our) control\b",
    ],
    "us_vs_them": [
        r"\benemies\b", r"\bthe elite\b", r"\bsheeple\b",
        r"\bpure blood\b", r"\bpatriot(s)?\b", r"\bdeep state\b",
        r"\btraitor(s)?\b", r"\boutside(rs)?\b",
    ],
    "emotional_manipulation": [
        r"\b(!!|!!!)\b", r"[!]{2,}", r"\bplease please\b",
        r"\bbegging you\b", r"\bi(m|'m) desperate\b",
        r"\bdestroy(ed|ing)?\b", r"\bbetrayed\b", r"\bcrying\b",
    ],
}

def score_text(text):
    text_lower = text.lower()
    hits = {}
    total = 0
    for category, patterns in PATTERNS.items():
        count = 0
        for p in patterns:
            matches = re.findall(p, text_lower)
            count += len(matches)
        if count:
            hits[category] = count
            total += count
    return total, hits

def classify(score):
    if score < 5:
        return "LOW", "✅ LOW"
    elif score < 15:
        return "MODERATE", "⚠️ MODERATE"
    else:
        return "HIGH", "🚨 HIGH"

def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    score, hits = score_text(text)
    level, label = classify(score)

    print(f"Score: {score}")
    print(f"Level: {label}")
    if hits:
        print("Patterns detected:")
        for k, v in hits.items():
            print(f"  {k}: {v}")
    else:
        print("No significant patterns detected.")

if __name__ == "__main__":
    main()
'''
with open("workspace/scripts/detect.py", "w") as f:
    f.write(detect_src)
os.chmod("workspace/scripts/detect.py", 0o755)

# ── flagged message files (the 10 messages to analyse) ──────────────────────
messages = {
    "msg_001.txt": (
        "Act now! This is your last chance to join the movement. "
        "Millions of people are already onboard — don't be left behind. "
        "The deadline expires today only. Trust me, you will regret it if you miss this."
    ),
    "msg_002.txt": (
        "Hi team, please review the attached proposal when you have a moment. "
        "No rush, just wanted to share the updated roadmap for next quarter."
    ),
    "msg_003.txt": (
        "The deep state and the elite enemies of freedom are hiding the truth from you!!! "
        "They don't want you to know about the hidden agenda. Sheeple wake up — "
        "the traitors are among us and danger is everywhere. Secret meetings are happening right now."
    ),
    "msg_004.txt": (
        "Experts agree this revolutionary platform is unprecedented in the industry. "
        "It is a historic game-changer that will change the world. "
        "Our sources confirm it is officially the greatest achievement of all time."
    ),
    "msg_005.txt": (
        "Please join the all-hands call on Thursday. Agenda has been shared via calendar."
    ),
    "msg_006.txt": (
        "You will all fall in line. No choice. Submit to the new order. "
        "Under our control, you will obey or be removed. Bow down or be destroyed."
    ),
    "msg_007.txt": (
        "I'm desperate — please please help me!!! I've been betrayed and I'm crying "
        "as I write this. You are my last hope. Begging you to act now before the deadline!!!"
    ),
    "msg_008.txt": (
        "The sprint demo is scheduled for Friday. Please ensure your stories are complete "
        "by end of day Thursday so QA has time to verify."
    ),
    "msg_009.txt": (
        "Warning: hidden danger lurks in the upcoming urgency update. "
        "Experts agree the secret threat is real. My sources confirm the authorities confirm "
        "what they're hiding. Don't wait — act now, this expires soon. "
        "Everyone knows the sheeple won't see this coming. Revolutionary empire incoming!"
    ),
    "msg_010.txt": (
        "Reminder: office closure on Monday for the public holiday. "
        "If you have any urgent issues, please contact your manager directly."
    ),
}

for fname, content in messages.items():
    with open(f"workspace/comms/flagged/{fname}", "w") as f:
        f.write(content)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "workspace/configs/pipeline.yaml": "version: 2\nsteps:\n  - ingest\n  - transform\n  - export\n",
    "workspace/configs/thresholds_OLD.json": json.dumps({"low": 3, "medium": 8, "high": 20}, indent=2),
    "workspace/logs/ingestion.log": "2024-01-15 08:02:11 INFO  Ingested 240 records\n2024-01-15 08:02:13 WARN  3 records skipped\n",
    "workspace/logs/errors.log": "2024-01-15 09:11:45 ERROR  Connection timeout on retry 3\n",
    "workspace/reports/old/q3_summary.csv": "file,category,score\nmsg_old_01.txt,UNKNOWN,0\n",
    "workspace/data/raw/sample_corpus.txt": "This is a sample corpus file used for baseline calibration.\n",
    "workspace/data/staging/pending_review.txt": "Files pending secondary review by compliance officer.\n",
    "workspace/comms/archive/msg_archive_001.txt": "Old message: quarterly review done. No issues.\n",
    "workspace/comms/archive/msg_archive_002.txt": "Old message: budget approved for next cycle.\n",
    "workspace/comms/processed/batch_01_done.flag": "processed\n",
    "workspace/tools/placeholder.sh": "#!/bin/bash\necho 'placeholder'\n",
}
for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Flagged messages created: {len(messages)}")