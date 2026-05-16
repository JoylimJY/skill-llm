#!/bin/bash
set -e

mkdir -p /workspace/scripts
mkdir -p /workspace/comms/flagged

if [ ! -f /workspace/scripts/detect.py ]; then
    cat > /workspace/scripts/detect.py << 'PYEOF'
#!/usr/bin/env python3
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
PYEOF
fi

chmod +x /workspace/scripts/detect.py

echo "Setup complete. detect.py is executable."
echo "Flagged messages in /workspace/comms/flagged/:"
ls /workspace/comms/flagged/