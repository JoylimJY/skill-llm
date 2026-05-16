import os
import random
import csv
import json

random.seed(42)

BASE = "/workspace"

# ── directory structure with distractor files ──────────────────────────────
dirs = [
    "data/raw",
    "data/processed",
    "reports/q3",
    "reports/q4",
    "config",
    "archive/2022",
    "archive/2023",
    "scripts/utils",
    "docs",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# Distractor files
distractor_files = {
    "config/app_config.yaml": "database:\n  host: localhost\n  port: 5432\n  name: consulting_db\n",
    "config/logging.conf": "[loggers]\nkeys=root\n[handlers]\nkeys=consoleHandler\n",
    "docs/onboarding_checklist.txt": "1. Setup laptop\n2. Meet the team\n3. Review project docs\n",
    "archive/2022/old_contacts.csv": "name,email\nLegacy Person,legacy@old.com\n",
    "archive/2023/team_snapshot.json": '{"team": "Alpha", "headcount": 5, "year": 2023}',
    "scripts/utils/helpers.py": "def normalize_name(n):\n    return n.strip().title()\n",
    "tmp/scratch.txt": "temporary notes\ndo not use\n",
    "reports/q3/q3_summary.pdf.placeholder": "PDF placeholder - not real",
    "reports/q4/q4_kpis.txt": "Revenue: $2.1M\nHeadcount: 12\nNPS: 47\n",
    "data/processed/schema_v2.sql": "CREATE TABLE IF NOT EXISTS legacy_contacts (id INTEGER PRIMARY KEY, name TEXT);\n",
    "data/raw/README_DO_NOT_USE.txt": "This folder contains raw unprocessed data only.",
}
for rel_path, content in distractor_files.items():
    with open(os.path.join(BASE, rel_path), "w") as f:
        f.write(content)

# ── the actual messy input: team_roster.csv ────────────────────────────────
# Headers are messy/inconsistent with the skill's field names.
# Some rows have extra whitespace, mixed case, missing fields.
# The CSV uses "relation" not "relation_to_me", "org" not "organization", "personality" not "character"
roster_rows = [
    {
        "full_name": "Diana Osei",
        "job_title": "  Managing Partner  ",   # extra whitespace
        "relation": "Client",
        "org": "Meridian Consulting",
        "personality": "Decisive, big-picture thinker",
        "memo": "Lead partner on Project Helios; key decision maker",
    },
    {
        "full_name": "Carlos Reyes",
        "job_title": "Senior Consultant",
        "relation": "Colleague",
        "org": "Meridian Consulting",
        "personality": "Analytical, detail-oriented",
        "memo": "Reports to Diana; mentoring junior staff",
    },
    {
        "full_name": "Priya Nambiar",
        "job_title": "Consultant",
        "relation": "Colleague",
        "org": "Meridian Consulting",
        "personality": "Creative, collaborative",
        "memo": "Reports to Carlos; works with Sam on deliverables",
    },
    {
        "full_name": "Sam Okafor",
        "job_title": "Consultant",
        "relation": "Colleague",
        "org": "Meridian Consulting",
        "personality": "Pragmatic, fast learner",
        "memo": "Reports to Carlos; works with Priya on deliverables",
    },
    {
        "full_name": "Lin Wei",
        "job_title": "  Data Analyst  ",       # extra whitespace
        "relation": "Colleague",
        "org": "Meridian Consulting",
        "personality": "Meticulous, data-driven",
        "memo": "Reports to Priya; supports analytics workstream",
    },
    {
        "full_name": "Jordan Blake",
        "job_title": "Associate",
        "relation": "Mentee",
        "org": "Meridian Consulting",
        "personality": "Eager, quick learner",
        "memo": "New hire; mentored by Carlos",
    },
]

roster_path = os.path.join(BASE, "data/raw/team_roster.csv")
fieldnames = ["full_name", "job_title", "relation", "org", "personality", "memo"]
with open(roster_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(roster_rows)

# ── relationship spec file (deliberately uses IDs by name, not numeric ID) ──
# Agent must infer IDs after inserting people.
# Relationships encoded as: source_name | target_name | type | description
relationships = [
    ("Carlos Reyes",  "Diana Osei",   "reports_to",   "Senior consultant reports to managing partner"),
    ("Priya Nambiar", "Carlos Reyes", "reports_to",   "Consultant reports to senior consultant"),
    ("Sam Okafor",    "Carlos Reyes", "reports_to",   "Consultant reports to senior consultant"),
    ("Lin Wei",       "Priya Nambiar","reports_to",   "Analyst reports to consultant"),
    ("Jordan Blake",  "Carlos Reyes", "reports_to",   "Associate reports to senior consultant"),
    ("Carlos Reyes",  "Jordan Blake", "mentors",      "Career development mentorship"),
    ("Priya Nambiar", "Sam Okafor",   "works_with",   "Joint deliverable ownership on Project Helios"),
    ("Sam Okafor",    "Priya Nambiar","works_with",   "Joint deliverable ownership on Project Helios"),
    # Duplicate attempt — agent must handle gracefully (UNIQUE constraint)
    ("Carlos Reyes",  "Jordan Blake", "mentors",      "Duplicate mentorship — should not create second edge"),
]

rel_path = os.path.join(BASE, "data/raw/relationships_spec.json")
with open(rel_path, "w") as f:
    json.dump([
        {"from": r[0], "to": r[1], "type": r[2], "description": r[3]}
        for r in relationships
    ], f, indent=2)

# ── place the skill files in workspace root ────────────────────────────────
# database.py
database_py = '''#!/usr/bin/env python3
"""
SQLite database layer for People-Strategy Agent Skill.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any


class PeopleDatabase:
    def __init__(self, db_path: str = "people.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT DEFAULT \'\',
                relation_to_me TEXT DEFAULT \'\',
                organization TEXT DEFAULT \'\',
                character TEXT DEFAULT \'\',
                notes TEXT DEFAULT \'\',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_person_id INTEGER NOT NULL,
                to_person_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                description TEXT DEFAULT \'\',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_person_id) REFERENCES people(id) ON DELETE CASCADE,
                FOREIGN KEY (to_person_id) REFERENCES people(id) ON DELETE CASCADE,
                UNIQUE(from_person_id, to_person_id, relationship_type)
            );
            CREATE INDEX IF NOT EXISTS idx_people_name ON people(name);
            CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_person_id);
            CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_person_id);
        """)
        self.conn.commit()

    def add_person(self, name, role="", relation_to_me="", organization="", character="", notes="") -> int:
        cur = self.conn.execute(
            "INSERT INTO people (name, role, relation_to_me, organization, character, notes) VALUES (?,?,?,?,?,?)",
            (name, role, relation_to_me, organization, character, notes)
        )
        self.conn.commit()
        return cur.lastrowid

    def get_person(self, person_id: int) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM people WHERE id=?", (person_id,)).fetchone()
        return dict(row) if row else None

    def get_all_people(self) -> List[Dict]:
        rows = self.conn.execute("SELECT * FROM people ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def get_people_by_organization(self, org: str) -> List[Dict]:
        rows = self.conn.execute("SELECT * FROM people WHERE organization=? ORDER BY id", (org,)).fetchall()
        return [dict(r) for r in rows]

    def get_people_by_relation(self, relation: str) -> List[Dict]:
        rows = self.conn.execute("SELECT * FROM people WHERE relation_to_me=? ORDER BY id", (relation,)).fetchall()
        return [dict(r) for r in rows]

    def search_people(self, term: str) -> List[Dict]:
        like = f"%{term}%"
        rows = self.conn.execute(
            "SELECT * FROM people WHERE name LIKE ? OR role LIKE ? OR organization LIKE ?",
            (like, like, like)
        ).fetchall()
        return [dict(r) for r in rows]

    def update_person(self, person_id: int, name=None, role=None, relation_to_me=None,
                      organization=None, character=None, notes=None) -> bool:
        fields, vals = [], []
        for col, val in [("name", name), ("role", role), ("relation_to_me", relation_to_me),
                         ("organization", organization), ("character", character), ("notes", notes)]:
            if val is not None:
                fields.append(f"{col}=?")
                vals.append(val)
        if not fields:
            return False
        fields.append("updated_at=?")
        vals.append(datetime.now().isoformat())
        vals.append(person_id)
        cur = self.conn.execute(f"UPDATE people SET {\', \'.join(fields)} WHERE id=?", vals)
        self.conn.commit()
        return cur.rowcount > 0

    def delete_person(self, person_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM people WHERE id=?", (person_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def add_edge(self, from_id: int, to_id: int, rel_type: str, description: str = "") -> int:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO edges (from_person_id, to_person_id, relationship_type, description) VALUES (?,?,?,?)",
            (from_id, to_id, rel_type, description)
        )
        self.conn.commit()
        if cur.lastrowid == 0:
            row = self.conn.execute(
                "SELECT id FROM edges WHERE from_person_id=? AND to_person_id=? AND relationship_type=?",
                (from_id, to_id, rel_type)
            ).fetchone()
            return row["id"] if row else 0
        return cur.lastrowid

    def get_edges_from_person(self, person_id: int) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT e.*, p1.name as from_person_name, p2.name as to_person_name
            FROM edges e
            JOIN people p1 ON e.from_person_id = p1.id
            JOIN people p2 ON e.to_person_id = p2.id
            WHERE e.from_person_id=?
        """, (person_id,)).fetchall()
        return [dict(r) for r in rows]

    def get_edges_to_person(self, person_id: int) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT e.*, p1.name as from_person_name, p2.name as to_person_name
            FROM edges e
            JOIN people p1 ON e.from_person_id = p1.id
            JOIN people p2 ON e.to_person_id = p2.id
            WHERE e.to_person_id=?
        """, (person_id,)).fetchall()
        return [dict(r) for r in rows]

    def get_all_edges_for_person(self, person_id: int) -> Dict:
        return {
            "outgoing": self.get_edges_from_person(person_id),
            "incoming": self.get_edges_to_person(person_id)
        }

    def get_all_edges(self) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT e.*, p1.name as from_person_name, p2.name as to_person_name
            FROM edges e
            JOIN people p1 ON e.from_person_id = p1.id
            JOIN people p2 ON e.to_person_id = p2.id
            ORDER BY e.id
        """).fetchall()
        return [dict(r) for r in rows]

    def get_edge(self, edge_id: int) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM edges WHERE id=?", (edge_id,)).fetchone()
        return dict(row) if row else None

    def update_edge(self, edge_id: int, relationship_type=None, description=None) -> bool:
        fields, vals = [], []
        for col, val in [("relationship_type", relationship_type), ("description", description)]:
            if val is not None:
                fields.append(f"{col}=?")
                vals.append(val)
        if not fields:
            return False
        fields.append("updated_at=?")
        vals.append(datetime.now().isoformat())
        vals.append(edge_id)
        cur = self.conn.execute(f"UPDATE edges SET {\', \'.join(fields)} WHERE id=?", vals)
        self.conn.commit()
        return cur.rowcount > 0

    def delete_edge(self, edge_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM edges WHERE id=?", (edge_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def get_relationship_graph(self) -> Dict:
        nodes = self.get_all_people()
        edges = self.get_all_edges()
        return {"nodes": nodes, "edges": edges}
'''

with open(os.path.join(BASE, "database.py"), "w") as f:
    f.write(database_py)

# Copy people_skill.py content
people_skill_py = open("/dev/stdin").read() if False else None
# Write a minimal shim — the full people_skill.py is provided by setup_script
# Actually we write the full file here since we can't COPY
import textwrap

people_skill_content = r'''#!/usr/bin/env python3
"""
People-Strategy Agent Skill
A command-line agent for managing people relationships with graph database.
"""

import sys
import json
from typing import Optional
from database import PeopleDatabase


class PeopleAgent:
    def __init__(self, db_path: str = "people.db"):
        self.db = PeopleDatabase(db_path)

    def add_person(self, name, role="", relation_to_me="", organization="", character="", notes=""):
        person_id = self.db.add_person(name, role, relation_to_me, organization, character, notes)
        return {"success": True, "person_id": person_id, "message": f"Person '{name}' created with ID: {person_id}"}

    def get_person(self, person_id):
        person = self.db.get_person(person_id)
        if person:
            return {"success": True, "person": person}
        return {"success": False, "message": f"Person {person_id} not found"}

    def search_people(self, search_term):
        people = self.db.search_people(search_term)
        return {"success": True, "people": people, "count": len(people)}

    def list_people(self, organization=None, relation=None):
        if organization:
            people = self.db.get_people_by_organization(organization)
        elif relation:
            people = self.db.get_people_by_relation(relation)
        else:
            people = self.db.get_all_people()
        return {"success": True, "people": people, "count": len(people)}

    def update_person(self, person_id, name=None, role=None, relation_to_me=None,
                      organization=None, character=None, notes=None):
        updated = self.db.update_person(person_id, name, role, relation_to_me, organization, character, notes)
        if updated:
            return {"success": True, "message": f"Person {person_id} updated"}
        return {"success": False, "message": f"Person {person_id} not found or no changes made"}

    def delete_person(self, person_id):
        deleted = self.db.delete_person(person_id)
        if deleted:
            return {"success": True, "message": f"Person {person_id} deleted"}
        return {"success": False, "message": f"Person {person_id} not found"}

    def add_relationship(self, from_person_id, to_person_id, relationship_type, description=""):
        edge_id = self.db.add_edge(from_person_id, to_person_id, relationship_type, description)
        return {"success": True, "edge_id": edge_id, "message": f"Relationship created with ID: {edge_id}"}

    def get_relationships(self, person_id, direction="all"):
        if direction == "outgoing":
            edges = self.db.get_edges_from_person(person_id)
            return {"success": True, "relationships": edges, "count": len(edges)}
        elif direction == "incoming":
            edges = self.db.get_edges_to_person(person_id)
            return {"success": True, "relationships": edges, "count": len(edges)}
        else:
            edges = self.db.get_all_edges_for_person(person_id)
            total = len(edges["outgoing"]) + len(edges["incoming"])
            return {"success": True, "relationships": edges, "count": total}

    def list_all_relationships(self):
        edges = self.db.get_all_edges()
        return {"success": True, "relationships": edges, "count": len(edges)}

    def update_relationship(self, edge_id, relationship_type=None, description=None):
        updated = self.db.update_edge(edge_id, relationship_type, description)
        if updated:
            return {"success": True, "message": f"Relationship {edge_id} updated"}
        return {"success": False, "message": f"Relationship {edge_id} not found or no changes made"}

    def delete_relationship(self, edge_id):
        deleted = self.db.delete_edge(edge_id)
        if deleted:
            return {"success": True, "message": f"Relationship {edge_id} deleted"}
        return {"success": False, "message": f"Relationship {edge_id} not found"}

    def get_graph(self):
        graph = self.db.get_relationship_graph()
        return {"success": True, "graph": graph,
                "nodes_count": len(graph["nodes"]), "edges_count": len(graph["edges"])}

    def get_person_network(self, person_id):
        person = self.db.get_person(person_id)
        if not person:
            return {"success": False, "message": f"Person {person_id} not found"}
        edges = self.db.get_all_edges_for_person(person_id)
        connected_ids = set()
        for edge in edges["outgoing"]:
            connected_ids.add(edge["to_person_id"])
        for edge in edges["incoming"]:
            connected_ids.add(edge["from_person_id"])
        connected_people = [self.db.get_person(pid) for pid in connected_ids]
        return {"success": True, "person": person, "relationships": edges,
                "connected_people": connected_people, "connections_count": len(connected_people)}


def format_person(person):
    lines = [f"ID: {person['id']}", f"Name: {person['name']}"]
    if person.get('role'): lines.append(f"Role: {person['role']}")
    if person.get('relation_to_me'): lines.append(f"Relation: {person['relation_to_me']}")
    if person.get('organization'): lines.append(f"Organization: {person['organization']}")
    if person.get('character'): lines.append(f"Character: {person['character']}")
    if person.get('notes'): lines.append(f"Notes: {person['notes']}")
    lines.append(f"Created: {person['created_at']}")
    return "\n".join(lines)


def format_edge(edge):
    lines = [
        f"ID: {edge['id']}",
        f"From: {edge.get('from_person_name', edge['from_person_id'])} (ID: {edge['from_person_id']})",
        f"To: {edge.get('to_person_name', edge['to_person_id'])} (ID: {edge['to_person_id']})",
        f"Type: {edge['relationship_type']}",
    ]
    if edge.get('description'): lines.append(f"Description: {edge['description']}")
    lines.append(f"Created: {edge['created_at']}")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python people_skill.py <command> [args]")
        sys.exit(1)

    agent = PeopleAgent()
    command = sys.argv[1]

    try:
        if command == "add-person":
            if len(sys.argv) < 3:
                print("Error: Name required"); sys.exit(1)
            name = sys.argv[2]
            role = relation = org = character = notes = ""
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == "--role" and i+1 < len(sys.argv): role = sys.argv[i+1]; i += 2
                elif sys.argv[i] == "--relation" and i+1 < len(sys.argv): relation = sys.argv[i+1]; i += 2
                elif sys.argv[i] == "--org" and i+1 < len(sys.argv): org = sys.argv[i+1]; i += 2
                elif sys.argv[i] == "--character" and i+1 < len(sys.argv): character = sys.argv[i+1]; i += 2
                elif sys.argv[i] == "--notes" and i+1 < len(sys.argv): notes = sys.argv[i+1]; i += 2
                else: i += 1
            result = agent.add_person(name, role, relation, org, character, notes)
            print(result["message"])

        elif command == "get-person":
            result = agent.get_person(int(sys.argv[2]))
            if result["success"]: print(format_person(result["person"]))
            else: print(result["message"])

        elif command == "search":
            result = agent.search_people(sys.argv[2])
            print(f"Found {result['count']} people:\n")
            for p in result["people"]: print(format_person(p)); print("-"*50)

        elif command == "list-people":
            org = relation = None
            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == "--org" and i+1 < len(sys.argv): org = sys.argv[i+1]; i += 2
                elif sys.argv[i] == "--relation" and i+1 < len(sys.argv): relation = sys.argv[i+1]; i += 2
                else: i += 1
            result = agent.list_people(org, relation)
            print(f"Total: {result['count']} people\n")
            for p in result["people"]: print(format_person(p)); print("-"*50)

        elif command == "update-person":
            person_id = int(sys.argv[2])
            name = role = relation = org = character = notes = None
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == "--name" and i+1 < len(sys.argv): name = sys.argv[i+1]; i += 2
                elif sys.argv[i] == "--role" and i+1 < len(sys.argv): role = sys.argv[i+1]; i += 2
                elif sys.argv[i] == "--relation" and i+1 < len(sys.argv): relation = sys.argv[i+1]; i += 2
                elif sys.argv[i] == "--org" and i+1 < len(sys.argv): org = sys.argv[i+1]; i += 2
                elif sys.argv[i] == "--character" and i+1 < len(sys.argv): character = sys.argv[i+1]; i += 2
                elif sys.argv[i] == "--notes" and i+1 < len(sys.argv): notes = sys.argv[i+1]; i += 2
                else: i += 1
            result = agent.update_person(person_id, name, role, relation, org, character, notes)
            print(result["message"])

        elif command == "delete-person":
            result = agent.delete_person(int(sys.argv[2]))
            print(result["message"])

        elif command == "add-relationship":
            if len(sys.argv) < 5: print("Error: from_id, to_id, and type required"); sys.exit(1)
            from_id = int(sys.argv[2]); to_id = int(sys.argv[3]); rel_type = sys.argv[4]
            description = ""
            if len(sys.argv) > 5 and sys.argv[5] == "--description":
                description = sys.argv[6] if len(sys.argv) > 6 else ""
            result = agent.add_relationship(from_id, to_id, rel_type, description)
            print(result["message"])

        elif command == "get-relationships":
            person_id = int(sys.argv[2])
            direction = "all"
            if len(sys.argv) > 3 and sys.argv[3] == "--direction":
                direction = sys.argv[4] if len(sys.argv) > 4 else "all"
            result = agent.get_relationships(person_id, direction)
            if result["success"]:
                print(f"Total: {result['count']} relationships\n")
                if direction == "all":
                    print("OUTGOING:")
                    for e in result["relationships"]["outgoing"]: print(format_edge(e)); print("-"*50)
                    print("\nINCOMING:")
                    for e in result["relationships"]["incoming"]: print(format_edge(e)); print("-"*50)
                else:
                    for e in result["relationships"]: print(format_edge(e)); print("-"*50)

        elif command == "list-relationships":
            result = agent.list_all_relationships()
            print(f"Total: {result['count']} relationships\n")
            for e in result["relationships"]: print(format_edge(e)); print("-"*50)

        elif command == "update-relationship":
            edge_id = int(sys.argv[2]); rel_type = description = None
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == "--type" and i+1 < len(sys.argv): rel_type = sys.argv[i+1]; i += 2
                elif sys.argv[i] == "--description" and i+1 < len(sys.argv): description = sys.argv[i+1]; i += 2
                else: i += 1
            result = agent.update_relationship(edge_id, rel_type, description)
            print(result["message"])

        elif command == "delete-relationship":
            result = agent.delete_relationship(int(sys.argv[2]))
            print(result["message"])

        elif command == "get-graph":
            result = agent.get_graph()
            print(f"Graph: {result['nodes_count']} people, {result['edges_count']} relationships")
            print("\nJSON Output:")
            print(json.dumps(result["graph"], indent=2))

        elif command == "get-network":
            person_id = int(sys.argv[2])
            result = agent.get_person_network(person_id)
            if result["success"]:
                print("PERSON:"); print(format_person(result["person"]))
                print("\n" + "="*50 + "\n")
                print(f"NETWORK: {result['connections_count']} connections\n")
                print("CONNECTED PEOPLE:")
                for p in result["connected_people"]: print(format_person(p)); print("-"*50)
                print("\nRELATIONSHIPS:")
                print("\nOutgoing:")
                for e in result["relationships"]["outgoing"]: print(format_edge(e)); print("-"*50)
                print("\nIncoming:")
                for e in result["relationships"]["incoming"]: print(format_edge(e)); print("-"*50)
            else:
                print(result["message"])
        else:
            print(f"Unknown command: {command}"); sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}"); sys.exit(1)


if __name__ == "__main__":
    main()
'''

with open(os.path.join(BASE, "people_skill.py"), "w") as f:
    f.write(people_skill_content)

print("Workspace generated successfully.")
print(f"Files created: {sum(len(files) for _, _, files in os.walk(BASE))} total")