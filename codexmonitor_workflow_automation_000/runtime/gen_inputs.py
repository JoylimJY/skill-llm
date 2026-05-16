#!/usr/bin/env python3
"""
Build the sandbox workspace for the codexmonitor audit task.
Creates a realistic session archive with JSONL files, distractor files,
and the mock codexmonitor binary wrapper.
"""
import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Session archive at non-default location ─────────────────────────────
sessions_root = workspace / "codex_archive" / "sessions"

# Target date: 2025/03/15
target_dir = sessions_root / "2025" / "03" / "15"
target_dir.mkdir(parents=True, exist_ok=True)

# Distractor dates (other days)
for date_parts in [("2025","03","14"), ("2025","03","16"), ("2025","02","28"), ("2024","12","31")]:
    (sessions_root / date_parts[0] / date_parts[1] / date_parts[2]).mkdir(parents=True, exist_ok=True)

# ── 2. Session JSONL files for 2025/03/15 ──────────────────────────────────
# Session A: 30 turns (the one agent must pick — most turns)
SESSION_A_ID = "a3f8c2d1-9b4e-4f72-8e1a-0c5d7b3f2a91"

turns_a = []
roles = ["user", "assistant"]
topics = [
    "How do I implement a binary search tree in Python?",
    "Here is a basic implementation with insert and search methods.",
    "Can you add a delete method?",
    "Sure, here is the delete method with three cases.",
    "How do I handle the case where the node has two children?",
    "You use the in-order successor to replace the deleted node.",
    "Can you show me a complete example?",
    "Here is the complete BST class with all methods.",
    "How do I test this with pytest?",
    "Here are some test cases covering insert, search, and delete.",
    "What about edge cases like deleting the root?",
    "Deleting the root follows the same logic, here is the test.",
    "How do I serialize this tree to JSON?",
    "You can use a recursive approach to build a dict representation.",
    "Can you add that method to the class?",
    "Here is the to_dict method added to the BST class.",
    "How do I deserialize it back?",
    "Here is the from_dict class method.",
    "What is the time complexity of each operation?",
    "Insert and search are O(h) where h is the height of the tree.",
    "What about a balanced BST?",
    "An AVL tree or Red-Black tree maintains O(log n) height.",
    "Can you implement an AVL tree?",
    "Here is a basic AVL tree with rotations.",
    "How does the right rotation work exactly?",
    "The right rotation reassigns pointers to maintain BST property.",
    "Can you add a balance factor display?",
    "Here is the updated AVL with balance factor printing.",
    "How do I integrate this with a database?",
    "You can persist nodes to SQLite using the to_dict serialization.",
]

for i, (role, content) in enumerate(zip([roles[i % 2] for i in range(30)], topics), start=1):
    turns_a.append({
        "turn": i,
        "role": role,
        "content": content,
        "timestamp": f"2025-03-15T{9 + i//4:02d}:{(i*2)%60:02d}:00Z",
        "tokens": random.randint(50, 400)
    })

session_a_file = target_dir / f"{SESSION_A_ID}.jsonl"
with open(session_a_file, "w") as f:
    for turn in turns_a:
        f.write(json.dumps(turn) + "\n")

# Session B: 12 turns (shorter, distractor)
SESSION_B_ID = "b7e1a4f0-2c8d-4a15-9f3b-1d6e8c2b5f04"
turns_b = []
short_topics = [
    ("user", "Help me write a Flask REST API."),
    ("assistant", "Here is a basic Flask app with a GET endpoint."),
    ("user", "Add a POST endpoint to create users."),
    ("assistant", "Here is the POST endpoint with request parsing."),
    ("user", "How do I add authentication?"),
    ("assistant", "Use Flask-Login or JWT tokens for authentication."),
    ("user", "Show me JWT example."),
    ("assistant", "Here is a JWT authentication example with PyJWT."),
    ("user", "How do I protect routes?"),
    ("assistant", "Use the @login_required decorator or a JWT verify function."),
    ("user", "Thanks, can you add error handlers?"),
    ("assistant", "Here are 404 and 500 error handlers for your Flask app."),
]
for i, (role, content) in enumerate(short_topics, start=1):
    turns_b.append({
        "turn": i,
        "role": role,
        "content": content,
        "timestamp": f"2025-03-15T14:{i:02d}:00Z",
        "tokens": random.randint(30, 200)
    })

session_b_file = target_dir / f"{SESSION_B_ID}.jsonl"
with open(session_b_file, "w") as f:
    for turn in turns_b:
        f.write(json.dumps(turn) + "\n")

# ── 3. Distractor JSONL files in other dates ───────────────────────────────
distractor_ids = [
    ("2025","03","14", "c9d2e5f1-3a7b-4c81-b2d4-0f8e1a6c3b92"),
    ("2025","03","16", "d4f7a2e0-5b1c-4d93-a8f2-2e9b3c7d1a05"),
    ("2025","02","28", "e1b5c8d3-7f2a-4e64-9c1b-3a4d6e8f2c17"),
    ("2024","12","31", "f8e3b1a6-2d9c-4f75-8b3a-5c2e1d4f7b28"),
]
for y, m, d, sid in distractor_ids:
    fpath = sessions_root / y / m / d / f"{sid}.jsonl"
    with open(fpath, "w") as f:
        for j in range(random.randint(3, 8)):
            f.write(json.dumps({
                "turn": j+1,
                "role": roles[j%2],
                "content": f"Distractor content turn {j+1}",
                "timestamp": f"{y}-{m}-{d}T10:{j:02d}:00Z",
                "tokens": random.randint(20, 100)
            }) + "\n")

# ── 4. Realistic distractor files (non-session) ────────────────────────────
distractors = [
    workspace / "codex_archive" / "README_internal.txt",
    workspace / "codex_archive" / "config" / "archive.conf",
    workspace / "codex_archive" / "config" / "retention_policy.json",
    workspace / "codex_archive" / "exports" / "march_summary.csv",
    workspace / "codex_archive" / "exports" / "february_summary.csv",
    workspace / "codex_archive" / "scripts" / "cleanup.sh",
    workspace / "codex_archive" / "scripts" / "compress_old.py",
    workspace / "codex_archive" / "logs" / "archive.log",
    workspace / "codex_archive" / "logs" / "errors.log",
    workspace / "reports" / "q1_draft.md",
    workspace / "reports" / "compliance_checklist.txt",
]
for p in distractors:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        f.write(f"# {p.name}\nThis is an internal file for reference only.\n")

# ── 5. Write session metadata for mock binary ─────────────────────────────
# Store truth data the mock binary will use to serve correct responses
meta = {
    "target_date": "2025/03/15",
    "sessions_root": str(sessions_root),
    "session_a": {
        "id": SESSION_A_ID,
        "turns": len(turns_a),
        "turns_data": turns_a
    },
    "session_b": {
        "id": SESSION_B_ID,
        "turns": len(turns_b),
        "turns_data": turns_b
    }
}
meta_file = workspace / ".mock_codexmonitor_data.json"
with open(meta_file, "w") as f:
    json.dump(meta, f, indent=2)

print("Workspace created.")
print(f"Sessions root: {sessions_root}")
print(f"Session A (30 turns): {SESSION_A_ID}")
print(f"Session B (12 turns): {SESSION_B_ID}")
print(f"Mock data: {meta_file}")