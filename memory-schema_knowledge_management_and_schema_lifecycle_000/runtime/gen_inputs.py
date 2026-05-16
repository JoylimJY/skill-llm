import os
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# --- Create directory structure ---
dirs = [
    "memory/people",
    "memory/projects",
    "memory/meetings",
    "memory/decisions",
    "memory/labs",
    "schema",
    "memory/archive/2023",
    "memory/archive/2024",
    "memory/templates",
    "logs",
    "exports",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Helper to write files ---
def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(textwrap.dedent(content).strip() + "\n")

# --- DISTRACTOR FILES ---

write("memory/projects/quantum-sim.md", """
---
title: Quantum Simulation Project
type: Project
status: active
tags: [quantum, physics, simulation]
---
# Quantum Simulation Project

## Observations
- [status] active
- [domain] quantum physics
- [funding] NSF Grant #2024-QP-001
""")

write("memory/projects/ml-genomics.md", """
---
title: ML Genomics Pipeline
type: Project
status: active
tags: [machine learning, genomics]
---
# ML Genomics Pipeline

## Observations
- [status] active
- [domain] bioinformatics
""")

write("memory/meetings/2024-03-15-kickoff.md", """
---
title: 2024-03-15 Kickoff
type: Meeting
date: 2024-03-15
---
# 2024-03-15 Kickoff

## Observations
- [topic] Project kickoff for quantum-sim
- [date] 2024-03-15
""")

write("memory/meetings/2024-04-02-review.md", """
---
title: 2024-04-02 Review
type: Meeting
date: 2024-04-02
---
# 2024-04-02 Review

## Observations
- [topic] Mid-semester review
- [date] 2024-04-02
""")

write("memory/decisions/arch-decision-001.md", """
---
title: Architecture Decision 001
type: Decision
date: 2024-02-10
---
# Architecture Decision 001

## Observations
- [decision] Use PostgreSQL for primary data store
- [rationale] Proven reliability and strong JSONB support
""")

write("memory/labs/plasma-physics-lab.md", """
---
title: Plasma Physics Lab
type: Lab
director: Dr. Elena Vasquez
---
# Plasma Physics Lab

## Observations
- [department] Physics
- [location] Building C, Room 401
""")

write("memory/archive/2023/old-notes.md", """
---
title: Old Notes 2023
type: Note
---
# Old Notes 2023

Various scratch notes from 2023.
""")

write("memory/archive/2024/decommissioned-project.md", """
---
title: Decommissioned Project Alpha
type: Project
status: archived
---
# Decommissioned Project Alpha

## Observations
- [status] archived
""")

write("memory/templates/meeting-template.md", """
---
title: Meeting Template
type: template
---
# Meeting Notes Template

Use this for all meeting notes.
Fill in: date, attendees, decisions.
""")

write("logs/import-log-2024.txt", """
2024-01-15 INFO: Imported 45 notes from legacy system
2024-01-15 WARN: 12 notes missing type field
2024-02-01 INFO: Schema inference run completed
""")

write("exports/backup-manifest.json", """
{
  "created": "2024-06-01",
  "notes_count": 142,
  "schema_count": 0,
  "last_validated": null
}
""")

# --- CORE PROBLEM: Messy Person notes (the type the agent must schematize) ---
# These notes have consistent structure but NO schema/Person.md exists yet.
# They have various fields, some optional, one enum-like, one array, one relation.
# Critically: some fields are ONLY in frontmatter (not observations) — these will fail validation.

write("memory/people/alice-chen.md", """
---
title: Alice Chen
type: Person
role: Principal Investigator
department: Computer Science
email: alice.chen@lab.edu
orcid: 0000-0001-2345-6789
active: true
projects: [quantum-sim, ml-genomics]
---
# Alice Chen

## Observations
- [role] Principal Investigator
- [department] Computer Science
- [email] alice.chen@lab.edu
- [active] true
- [projects] quantum-sim
- [projects] ml-genomics
""")

write("memory/people/bob-torres.md", """
---
title: Bob Torres
type: Person
role: Postdoc
department: Physics
email: bob.torres@lab.edu
orcid: 0000-0002-9876-5432
active: true
projects: [quantum-sim]
---
# Bob Torres

## Observations
- [role] Postdoc
- [department] Physics
- [email] bob.torres@lab.edu
- [active] true
- [projects] quantum-sim
""")

write("memory/people/carol-wu.md", """
---
title: Carol Wu
type: Person
role: PhD Student
department: Computer Science
email: carol.wu@lab.edu
active: true
---
# Carol Wu

## Observations
- [role] PhD Student
- [department] Computer Science
- [email] carol.wu@lab.edu
- [active] true
""")

write("memory/people/david-okonkwo.md", """
---
title: David Okonkwo
type: Person
role: Research Engineer
department: Data Science
email: david.okonkwo@lab.edu
orcid: 0000-0003-1111-2222
active: true
projects: [ml-genomics]
---
# David Okonkwo

## Observations
- [role] Research Engineer
- [department] Data Science
- [email] david.okonkwo@lab.edu
- [active] true
- [projects] ml-genomics
""")

write("memory/people/elena-vasquez.md", """
---
title: Elena Vasquez
type: Person
role: Principal Investigator
department: Physics
email: elena.vasquez@lab.edu
orcid: 0000-0004-5555-6666
active: true
projects: [quantum-sim]
---
# Elena Vasquez

## Observations
- [role] Principal Investigator
- [department] Physics
- [email] elena.vasquez@lab.edu
- [active] true
- [projects] quantum-sim
""")

# TWO notes that are intentionally MISSING required 'email' observation (only have frontmatter)
# and are missing 'role' observation entirely — these should FAIL schema_validate.

write("memory/people/frank-lee.md", """
---
title: Frank Lee
type: Person
role: Visiting Scholar
department: Chemistry
email: frank.lee@external.edu
active: false
---
# Frank Lee

Visiting scholar from External University.

## Observations
- [department] Chemistry
- [active] false
""")

write("memory/people/grace-kim.md", """
---
title: Grace Kim
type: Person
role: Masters Student
department: Computer Science
active: true
---
# Grace Kim

## Observations
- [department] Computer Science
- [active] true
""")

# One note with a NEW field 'homepage' that will appear during schema_diff (schema evolution)
write("memory/people/henry-shaw.md", """
---
title: Henry Shaw
type: Person
role: Postdoc
department: Physics
email: henry.shaw@lab.edu
orcid: 0000-0005-7777-8888
active: true
projects: [quantum-sim]
homepage: https://henryshaw.science
---
# Henry Shaw

## Observations
- [role] Postdoc
- [department] Physics
- [email] henry.shaw@lab.edu
- [active] true
- [projects] quantum-sim
- [homepage] https://henryshaw.science
""")

write("memory/people/iris-patel.md", """
---
title: Iris Patel
type: Person
role: Research Scientist
department: Data Science
email: iris.patel@lab.edu
active: true
projects: [ml-genomics]
homepage: https://irispatel.io
---
# Iris Patel

## Observations
- [role] Research Scientist
- [department] Data Science
- [email] iris.patel@lab.edu
- [active] true
- [projects] ml-genomics
- [homepage] https://irispatel.io
""")

print("Workspace initialized successfully.")
print(f"Created {len(dirs)} directories and multiple note files.")
print("Person notes: alice-chen, bob-torres, carol-wu, david-okonkwo, elena-vasquez, frank-lee, grace-kim, henry-shaw, iris-patel")
print("schema/ directory exists but is EMPTY (no Person schema yet).")