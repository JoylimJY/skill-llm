import os
import stat

WORKSPACE = "/workspace"

# ── directory structure ────────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "drafts",
    "drafts/old",
    "drafts/archive",
    "resources/liturgical",
    "resources/sacraments",
    "resources/morality",
    "rcia/sessions",
    "rcia/handouts",
    "admin/logs",
    "admin/reports",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "drafts/old/baptism_notes.txt": (
        "Baptism notes - rough draft\n"
        "- matter: water\n"
        "- form: Trinitarian formula\n"
        "TODO: add CCC refs\n"
    ),
    "drafts/archive/eucharist_v1.txt": (
        "Eucharist draft v1 (deprecated)\n"
        "Short answer: The Eucharist is the body and blood of Christ.\n"
        "Missing: citations\n"
    ),
    "resources/liturgical/calendar_notes.md": (
        "# Liturgical Calendar\n"
        "Advent, Christmas, Ordinary Time, Lent, Easter\n"
        "See General Norms for the Liturgical Year\n"
    ),
    "resources/sacraments/seven_sacraments_list.txt": (
        "1. Baptism\n2. Confirmation\n3. Eucharist\n"
        "4. Penance\n5. Anointing of the Sick\n6. Holy Orders\n7. Matrimony\n"
    ),
    "resources/morality/conscience_notes.txt": (
        "Conscience: CCC 1776-1802\n"
        "Must be formed according to right reason and divine law.\n"
    ),
    "rcia/sessions/session01_outline.txt": (
        "Session 1: Who is God?\nObjectives: Introduce Trinity, Creation\nDuration: 90 min\n"
    ),
    "rcia/sessions/session02_outline.txt": (
        "Session 2: Scripture & Tradition\nObjectives: Dual sources of Revelation\nDuration: 90 min\n"
    ),
    "rcia/handouts/glossary.txt": (
        "Dogma: Divinely revealed truth, defined by the Church\n"
        "Doctrine: Official Church teaching\n"
        "Discipline: Church law/practice, changeable\n"
        "Prudential Judgment: Application of principles to specific cases\n"
    ),
    "admin/logs/session_attendance.csv": (
        "session,date,attendees\n"
        "1,2024-09-15,12\n"
        "2,2024-09-22,11\n"
        "3,2024-09-29,13\n"
    ),
    "admin/reports/q3_summary.txt": (
        "Q3 RCIA Summary\nTotal sessions: 8\nAvg attendance: 11.5\nTopics covered: Trinity, Sacraments, Scripture\n"
    ),
    "drafts/confirmation_draft.txt": (
        "Confirmation topic - INCOMPLETE\nNeeds: short answer, church teaching, citations, next step\n"
    ),
    "resources/morality/capital_sins.txt": (
        "The Seven Capital Sins (CCC 1866):\n"
        "Pride, Avarice, Envy, Wrath, Gluttony, Lust, Sloth\n"
    ),
}

for rel_path, content in distractors.items():
    fpath = os.path.join(WORKSPACE, rel_path)
    with open(fpath, "w") as f:
        f.write(content)

# ── CCC topic map reference file ─────────────────────────────────────────────
ccc_topic_map = """\
# CCC Topic Map

## purgatory
- CCC 1030: All who die in God's grace, but still imperfectly purified, are assured of eternal salvation; but after death they undergo purification.
- CCC 1031: The Church gives the name Purgatory to this final purification of the elect, which is entirely different from the punishment of the damned.
- CCC 1032: This teaching is also based on the practice of prayer for the dead, already mentioned in Sacred Scripture: "Therefore [Judas Maccabeus] made atonement for the dead, that they might be delivered from their sin."
- CCC 1472: The doctrine of purgatory demonstrates that even after death there is still a possibility of purification. [Note: distinguish DOGMA (existence of purgatory, defined at Lyons II, Florence, Trent) from DOCTRINE (nature/duration of purification) and DISCIPLINE (indulgences as practice).]

## eucharist
- CCC 1322: The holy Eucharist completes Christian initiation.
- CCC 1323: "The Eucharist is the source and summit of the Christian life."
- CCC 1374: The mode of Christ's presence under the Eucharistic species is unique.
- CCC 1376: Transubstantiation: the whole substance of the bread is converted into the substance of Christ's Body.

## baptism
- CCC 1213: Holy Baptism is the basis of the whole Christian life.
- CCC 1215: Baptism is called the sacrament of regeneration through water in the word.
- CCC 1250: Born with a fallen human nature and tainted by original sin, children also have need of the new birth in Baptism.

## prayer
- CCC 2558: "The mystery of faith." From this mystery springs the prayer of the Church.
- CCC 2590: God tirelessly calls each person to prayer.
- CCC 2607: When Jesus prays he is already teaching us how to pray.

## conscience
- CCC 1776: Deep within his conscience man discovers a law which he has not laid upon himself but which he must obey.
- CCC 1783: Conscience must be informed and moral judgment enlightened.
- CCC 1800: A human being must always obey the certain judgment of his conscience.
"""

with open(os.path.join(WORKSPACE, "references/ccc-topic-map.md"), "w") as f:
    f.write(ccc_topic_map)

# ── prayers reference file ────────────────────────────────────────────────────
prayers_md = """\
# Prayer Snippets

## hail mary
Hail Mary, full of grace, the Lord is with thee;
blessed art thou among women,
and blessed is the fruit of thy womb, Jesus.
Holy Mary, Mother of God,
pray for us sinners, now and at the hour of our death. Amen.

## our father
Our Father, who art in heaven, hallowed be thy name;
thy kingdom come, thy will be done, on earth as it is in heaven.
Give us this day our daily bread;
and forgive us our trespasses, as we forgive those who trespass against us;
and lead us not into temptation, but deliver us from evil. Amen.

## eternal rest
Eternal rest grant unto them, O Lord,
and let perpetual light shine upon them.
May the souls of the faithful departed,
through the mercy of God, rest in peace. Amen.

## memorare
Remember, O most gracious Virgin Mary,
that never was it known that anyone who fled to thy protection,
implored thy help, or sought thy intercession was left unaided.
Inspired with this confidence, I fly unto thee, O Virgin of virgins, my Mother.
To thee do I come; before thee I stand, sinful and sorrowful. Amen.
"""

with open(os.path.join(WORKSPACE, "references/prayers.md"), "w") as f:
    f.write(prayers_md)

# ── style reference file ──────────────────────────────────────────────────────
style_md = """\
# Tone & Style Guide

- Neutral, respectful, precise theological language
- Avoid sensationalism or apologetics-as-combat
- When citing CCC, use format: CCC XXXX
- Distinguish: dogma (defined, irreformable) / doctrine (official teaching) / discipline (changeable practice) / prudential judgment (application)
- Beginner-friendly explanations for RCIA context
- Always include a practical pastoral next step
"""

with open(os.path.join(WORKSPACE, "references/style.md"), "w") as f:
    f.write(style_md)

# ── scripts ───────────────────────────────────────────────────────────────────
ccc_sh = r"""#!/bin/bash
# Usage: ./scripts/ccc.sh "<topic>"
TOPIC="${1,,}"
MAP="$(dirname "$0")/../references/ccc-topic-map.md"
if [ ! -f "$MAP" ]; then
    echo "ERROR: ccc-topic-map.md not found" >&2
    exit 1
fi

# Find the section for the topic
python3 - "$TOPIC" "$MAP" <<'PYEOF'
import sys, re

topic = sys.argv[1].strip().lower()
map_file = sys.argv[2]

with open(map_file) as f:
    content = f.read()

# Find section
pattern = rf"## {re.escape(topic)}\n((?:- .*\n)*)"
match = re.search(pattern, content)
if match:
    print(f"CCC references for topic: {topic}")
    print(match.group(1).strip())
else:
    print(f"No CCC entries found for topic: {topic}")
    print("Try: purgatory, eucharist, baptism, prayer, conscience")
PYEOF
"""

prayer_sh = r"""#!/bin/bash
# Usage: ./scripts/prayer.sh "<prayer name>"
PRAYER="${1,,}"
PRAYERS="$(dirname "$0")/../references/prayers.md"
if [ ! -f "$PRAYERS" ]; then
    echo "ERROR: prayers.md not found" >&2
    exit 1
fi

python3 - "$PRAYER" "$PRAYERS" <<'PYEOF'
import sys, re

prayer = sys.argv[1].strip().lower()
prayers_file = sys.argv[2]

with open(prayers_file) as f:
    content = f.read()

pattern = rf"## {re.escape(prayer)}\n((?:(?!##).+\n)*)"
match = re.search(pattern, content, re.MULTILINE)
if match:
    print(f"Prayer: {prayer}")
    print(match.group(1).strip())
else:
    print(f"No prayer found for: {prayer}")
    print("Available: hail mary, our father, eternal rest, memorare")
PYEOF
"""

status_sh = r"""#!/bin/bash
echo "Catholic Grounding Pack - Status"
echo "================================="
echo "CCC Topic Map: $(wc -l < "$(dirname "$0")/../references/ccc-topic-map.md") lines"
echo "Prayers file:  $(wc -l < "$(dirname "$0")/../references/prayers.md") lines"
echo "Style guide:   $(wc -l < "$(dirname "$0")/../references/style.md") lines"
echo ""
echo "Available topics (ccc.sh): purgatory, eucharist, baptism, prayer, conscience"
echo "Available prayers (prayer.sh): hail mary, our father, eternal rest, memorare"
"""

scripts = {
    "scripts/ccc.sh": ccc_sh,
    "scripts/prayer.sh": prayer_sh,
    "scripts/status.sh": status_sh,
}

for rel_path, content in scripts.items():
    fpath = os.path.join(WORKSPACE, rel_path)
    with open(fpath, "w") as f:
        f.write(content)
    os.chmod(fpath, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# ── task brief ────────────────────────────────────────────────────────────────
task_brief = """\
RCIA Program - Knowledge Base Entry Request
============================================

Topic assigned to you: PURGATORY
Intended audience: RCIA candidates (beginners)
Output file required: purgatory_answer.md

Please prepare a complete knowledge-base entry for our RCIA digital library.
The entry must be drawn from our local reference system and follow the program's
standard format. Make sure to include relevant prayer content and all CCC citations
obtained from the reference tools. The entry should be suitable for self-study by
new Catholics exploring the faith.

Note: The topic of purgatory involves multiple levels of Church teaching authority.
The entry should help learners understand what is definitively defined versus what
remains open theological discussion.
"""

with open(os.path.join(WORKSPACE, "task_brief.txt"), "w") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print(f"Structure written to: {WORKSPACE}")