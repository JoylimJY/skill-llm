import os
import random
import stat

random.seed(42)

workspace = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "docs/architecture",
    "docs/wiki",
    "docs/meetings",
    "scripts",
    "assets/examples",
    "assets/icons",
    "references",
    "src/intake",
    "src/triage",
    "src/billing",
    "tests",
    "config",
    "reports/q3",
    "reports/q4",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """\
---
name: mermaid-architect
description: Generate beautiful, hand-drawn Mermaid diagrams with robust syntax (quoted labels, ELK layout). Use this skill when the user asks for "diagram", "flowchart", "sequence diagram", or "visualize this process".
---

# Mermaid Architect

## Usage
- **Role**: Diagram Architect & Designer.
- **Trigger**: "Draw this", "Make a diagram", "Visualize".
- **Output**: Mermaid code block (```mermaid```) + Explanation.

## Capabilities
1.  **Flowcharts**: Process mapping, decision trees.
2.  **Sequence Diagrams**: API calls, user interactions.
3.  **Class Diagrams**: OOP structures, database schemas.
4.  **State Diagrams**: Lifecycle management.

## Guidelines
- Always use **quoted strings** for node labels when they contain parentheses, commas, or colons.
- Use safe node IDs: no spaces; use camelCase, PascalCase, or underscores. Avoid reserved IDs: `end`, `subgraph`, `graph`, `flowchart`.
- Prefer `TD` (Top-Down) for hierarchies, `LR` (Left-Right) for timelines.
- Use `subgraph id [Label]` with an explicit ID and label (no spaces in ID).
- See [references/syntax-guide.md](references/syntax-guide.md) for full safe-syntax rules.

## Reference Materials
- [Syntax Guide](references/syntax-guide.md)
- [Example: Microservices](assets/examples/microservice-arch.mmd)
- [Example: Sequence API](assets/examples/sequence-api.mmd)
- [Example: State Lifecycle](assets/examples/state-lifecycle.mmd)

## Validation
Run the validator on one or more `.mmd` files:
```bash
scripts/validate-mmd assets/examples/*.mmd
```
"""

with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_md)

# ── references/syntax-guide.md ───────────────────────────────────────────────
syntax_guide = r"""# Mermaid Syntax Reference

## Safe Syntax (Cursor-compatible)

Follow these rules so diagrams render correctly in Cursor and avoid parse errors.

- **Node IDs**: No spaces. Use `camelCase`, `PascalCase`, or underscores (e.g. `userNode`, `LoadBalancer`, `api_gateway`). Do not use reserved IDs: `end`, `subgraph`, `graph`, `flowchart`.
- **Labels with special characters**: Use double-quoted labels for text containing parentheses, commas, or colons (e.g. `A["Process (main)"]`, `B["Step 1: Init"]`).
- **Edge labels with special characters**: Wrap in quotes (e.g. `A -->|"O(1) lookup"| B`).
- **Subgraphs**: Use explicit ID and label: `subgraph id [Label]` (e.g. `subgraph backend [Backend]`). Do not use spaces in the subgraph ID.
- **Theme**: Avoid explicit colors or `style`/`classDef` fill so the renderer can apply theme colors.

---

## Flowchart

```mermaid
flowchart TD
    startNode["Start"] --> decisionNode{"Decision?"}
    decisionNode -->|Yes| processNode["Process"]
    decisionNode -->|No| endNode["End"]
    processNode --> endNode
```

- **LR**: Left-to-Right layout
- **TD**: Top-Down layout
- `{}`: Rhombus (Decision)
- `[]`: Rectangle (Process)
- `()`: Rounded Rectangle
- Use quoted labels when the label contains special characters.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant System
    User->>System: Request Data
    activate System
    System-->>User: Return Data
    deactivate System
```

- `->>`: Solid line with arrow (Sync call)
- `-->>`: Dashed line with arrow (Async reply)
- `activate`/`deactivate`: Lifeline status
- Keep participant names without spaces; use PascalCase or camelCase.

## Class Diagram

```mermaid
classDiagram
    class Animal {
        +String name
        +void eat()
    }
    class Dog {
        +void bark()
    }
    Animal <|-- Dog
```

- `<|--`: Inheritance
- `+`: Public
- `-`: Private

## State Diagram

```mermaid
stateDiagram-v2
    [*] --> idle
    idle --> processing: start
    processing --> idle: done
    processing --> error: fail
    error --> [*]
```

- `[*]`: Start or end state
- `-->`: Transition; use `: label` for transition text
- State names: prefer single words or camelCase; use quoted labels if needed (e.g. `"In Progress"`)

---

## Other diagram types (reference)

- **ER**: Entity-relationship with `erDiagram` and `ENTITY { }` blocks
- **Gantt**: `gantt` with `title`, `dateFormat`, and section/task lines
- **Pie**: `pie` with `title` and `"label" : value` pairs
"""

with open(os.path.join(workspace, "references/syntax-guide.md"), "w") as f:
    f.write(syntax_guide)

# ── assets/examples/*.mmd  (valid reference examples) ───────────────────────
microservice_mmd = """\
flowchart LR
    subgraph frontend [Frontend]
        webApp["Web App (React)"]
    end
    subgraph backend [Backend]
        apiGateway["API Gateway"]
        authService["Auth Service"]
        dataService["Data Service"]
    end
    webApp -->|"POST /login"| apiGateway
    apiGateway --> authService
    apiGateway --> dataService
"""
with open(os.path.join(workspace, "assets/examples/microservice-arch.mmd"), "w") as f:
    f.write(microservice_mmd)

sequence_mmd = """\
sequenceDiagram
    participant Client
    participant APIGateway
    participant AuthService
    Client->>APIGateway: POST /api/login
    activate APIGateway
    APIGateway->>AuthService: Validate token
    activate AuthService
    AuthService-->>APIGateway: Token valid
    deactivate AuthService
    APIGateway-->>Client: 200 OK
    deactivate APIGateway
"""
with open(os.path.join(workspace, "assets/examples/sequence-api.mmd"), "w") as f:
    f.write(sequence_mmd)

state_mmd = """\
stateDiagram-v2
    [*] --> idle
    idle --> processing: start
    processing --> idle: done
    processing --> errorState: fail
    errorState --> [*]
"""
with open(os.path.join(workspace, "assets/examples/state-lifecycle.mmd"), "w") as f:
    f.write(state_mmd)

# ── scripts/validate-mmd  (the validator) ────────────────────────────────────
validate_script = r"""#!/usr/bin/env python3
"""
validate_script += '''"""
Mermaid .mmd syntax validator.

Checks the proprietary safe-syntax rules documented in references/syntax-guide.md:
  1. Node IDs must not contain spaces.
  2. Node IDs must not be reserved words: end, subgraph, graph, flowchart.
  3. Labels with parentheses, commas, or colons must be double-quoted.
  4. Subgraph declarations must use the two-token form: subgraph <id> [<label>]
     (the ID must contain no spaces; the bracketed label is mandatory).
  5. Edge labels with special characters must be wrapped in pipe-quoted form |"..."|.
  6. No style / classDef fill directives.

Usage:
  scripts/validate-mmd file1.mmd [file2.mmd ...]

Exit codes:
  0  all files pass
  1  one or more files have violations
"""
import sys, re
from pathlib import Path

RESERVED_IDS = {"end", "subgraph", "graph", "flowchart"}

# Patterns
NODE_DEF_RE    = re.compile(r\'\\b([A-Za-z_][\\w]*)\\s*(?:[\\[\\{\\(])\')
SUBGRAPH_RE    = re.compile(r\'^\\s*subgraph\\s+(\\S+)\\s+\\[([^\\]]+)\\]\')
SUBGRAPH_BARE  = re.compile(r\'^\\s*subgraph\\s+(.+)$\')
EDGE_LABEL_RE  = re.compile(r\'\\|([^|]+)\\|\')

SPECIAL_CHARS  = re.compile(r\'[(),:]\')

def unquoted_label_re():
    # matches node with an unquoted label containing special chars
    # e.g.   foo[Step 1: Init]   or   bar{Decision (main)}
    return re.compile(r\'\\b\\w+\\s*[\\[\\{\\(]([^\\"\\]\\}\\)][^\\]\\}\\)]*[(),:][^\\]\\}\\)]*)\\]\')

errors = []

def validate_file(path: Path):
    text = path.read_text()
    lines = text.splitlines()
    file_errors = []

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip comment lines
        if stripped.startswith(\'%%\'):
            continue

        # ── Rule 4: subgraph must have explicit id [Label] ─────────────────
        if re.match(r\'\\s*subgraph\\b\', line):
            m_good = SUBGRAPH_RE.match(line)
            m_bare = SUBGRAPH_BARE.match(line)
            if not m_good:
                if m_bare:
                    token = m_bare.group(1).strip()
                    # allow "end" alone (closing subgraph)
                    if token.lower() != \'end\':
                        file_errors.append(
                            f"  Line {lineno}: subgraph missing bracketed label: {line.rstrip()}"
                        )
            else:
                # Check subgraph ID has no spaces
                sg_id = m_good.group(1)
                if \' \' in sg_id:
                    file_errors.append(
                        f"  Line {lineno}: subgraph ID contains spaces: \\"{sg_id}\\""
                    )
                # Check ID not reserved
                if sg_id.lower() in RESERVED_IDS:
                    file_errors.append(
                        f"  Line {lineno}: subgraph uses reserved ID: \\"{sg_id}\\""
                    )
            continue

        # ── Rule 2 & 1: node IDs ──────────────────────────────────────────
        for m in NODE_DEF_RE.finditer(line):
            node_id = m.group(1)
            if \' \' in node_id:
                file_errors.append(f"  Line {lineno}: node ID with spaces: \\"{node_id}\\"")
            if node_id.lower() in RESERVED_IDS:
                file_errors.append(f"  Line {lineno}: reserved node ID: \\"{node_id}\\"")

        # ── Rule 3: unquoted labels with special chars ────────────────────
        # Find bracket content that is NOT quoted
        # Pattern: nodeId[...] or nodeId{...} — capture inner text
        for bracket_m in re.finditer(r\'\\w+\\s*(?:[\\[\\{])([^\\"\\n][^\\]\\}\\n]*)\\]|\\w+\\s*\\{([^\\"\\n][^\\}\\n]*)\\}\', line):
            inner = bracket_m.group(1) or bracket_m.group(2) or \'\'
            if SPECIAL_CHARS.search(inner):
                file_errors.append(
                    f"  Line {lineno}: label with special chars must be quoted: ...{inner[:40]}..."
                )

        # ── Rule 5: edge labels with special chars must use |"..."| ───────
        for el_m in EDGE_LABEL_RE.finditer(line):
            el_text = el_m.group(1)
            # If it starts and ends with " it is already quoted — fine
            if not (el_text.startswith(\'"\') and el_text.endswith(\'"\') ):
                if SPECIAL_CHARS.search(el_text):
                    file_errors.append(
                        f"  Line {lineno}: edge label with special chars must be quoted: |{el_text}|"
                    )

        # ── Rule 6: no style/classDef fill ───────────────────────────────
        if re.search(r\'(style\\s+\\w+.*fill|classDef\\s+\\w+.*fill)\', line, re.IGNORECASE):
            file_errors.append(f"  Line {lineno}: explicit fill color not allowed: {line.rstrip()}")

    return file_errors

all_passed = True
for arg in sys.argv[1:]:
    p = Path(arg)
    if not p.exists():
        print(f"ERROR: file not found: {arg}")
        all_passed = False
        continue
    errs = validate_file(p)
    if errs:
        print(f"FAIL {p}")
        for e in errs:
            print(e)
        all_passed = False
    else:
        print(f"PASS {p}")

sys.exit(0 if all_passed else 1)
'''

scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)
validate_path = os.path.join(scripts_dir, "validate-mmd")
with open(validate_path, "w") as f:
    f.write(validate_script)
os.chmod(validate_path, 0o755)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "docs/meetings/2024-09-kickoff.md": "# Kickoff Meeting Notes\n\nDiscussed patient intake flow. Need diagrams for wiki.\n",
    "docs/meetings/2024-10-review.md": "# October Review\n\nTriage process needs clearer visualization.\n",
    "docs/wiki/patient-intake-overview.md": "# Patient Intake Overview\n\nThis page will host architecture diagrams (TBD).\n",
    "docs/architecture/old-flowchart.txt": "START -> Registration -> Triage -> Bed Assignment -> END\n(legacy, hand-drawn, not machine-readable)\n",
    "src/intake/register.py": "def register_patient(name, dob, insurance):\n    pass\n",
    "src/triage/assess.py": "def assess(patient_id, vitals):\n    # Level 1: Critical, Level 2: Urgent\n    pass\n",
    "src/billing/invoice.py": "def generate_invoice(patient_id, procedures):\n    pass\n",
    "config/app.yaml": "env: production\ndatabase:\n  host: db.internal\n  port: 5432\n",
    "tests/test_intake.py": "def test_register():\n    assert True\n",
    "tests/test_triage.py": "def test_assess():\n    assert True\n",
    "reports/q3/summary.txt": "Q3: 1,240 patients processed. Average triage time: 8 min.\n",
    "reports/q4/summary.txt": "Q4: 1,580 patients processed. Bottleneck: HL7 ADT^A01 message parsing.\n",
    "assets/icons/hospital.svg": "<svg></svg>\n",
    "docs/architecture/system-notes.md": (
        "## Key Flows\n"
        "1. Patient arrives -> Reception (front desk) -> Triage (Level 1, 2, or 3)\n"
        "2. EHR system sends HL7: ADT^A01 message on admission\n"
        "3. Billing: ICD-10 code assigned after discharge\n"
        "States: Waiting, In Assessment, Admitted, Discharged, Error\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")