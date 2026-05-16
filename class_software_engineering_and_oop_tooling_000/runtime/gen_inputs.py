import os
import stat
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Build the skill's scripts/ structure ──────────────────────────────────
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# The actual script that the agent must discover and invoke
script_content = r'''#!/usr/bin/env bash
# class skill v1.0.0 — OOP Reference Tool

CLASS_DIR="${CLASS_DIR:-$HOME/.class}"
mkdir -p "$CLASS_DIR"

CMD="${1:-help}"

case "$CMD" in
  intro)
    echo "=== OOP FUNDAMENTALS ==="
    echo "Object-Oriented Programming organizes code around objects rather than functions."
    echo ""
    echo "FOUR PILLARS:"
    echo "  1. Encapsulation  — bundling data and methods; hiding internal state"
    echo "  2. Abstraction    — exposing only essential features; hiding complexity"
    echo "  3. Inheritance    — deriving new classes from existing ones"
    echo "  4. Polymorphism   — same interface, different implementations"
    echo ""
    echo "A CLASS is a blueprint; an OBJECT is an instance of that blueprint."
    echo "Constructor (__init__ / constructor) initializes object state."
    echo ""
    # Write cache
    echo "intro_visited=$(date +%s)" > "$CLASS_DIR/intro.cache"
    ;;

  solid)
    echo "=== SOLID PRINCIPLES ==="
    echo ""
    echo "S — Single Responsibility Principle (SRP)"
    echo "    A class should have only ONE reason to change."
    echo "    Bad:  class UserManager handles DB, email, logging"
    echo "    Good: separate UserRepo, EmailService, Logger"
    echo ""
    echo "O — Open/Closed Principle (OCP)"
    echo "    Open for extension, closed for modification."
    echo "    Use abstract base classes; extend via subclasses."
    echo ""
    echo "L — Liskov Substitution Principle (LSP)"
    echo "    Subtypes must be substitutable for their base types."
    echo "    Violating: Square extends Rectangle but breaks setWidth."
    echo ""
    echo "I — Interface Segregation Principle (ISP)"
    echo "    No client should be forced to depend on methods it doesn't use."
    echo "    Prefer many small interfaces over one large interface."
    echo ""
    echo "D — Dependency Inversion Principle (DIP)"
    echo "    Depend on abstractions, not concretions."
    echo "    High-level modules should not import low-level modules directly."
    echo ""
    echo "SOLID_PRINCIPLES_COUNT=5" >> "$CLASS_DIR/solid.cache"
    echo "solid_visited=$(date +%s)" >> "$CLASS_DIR/solid.cache"
    ;;

  inheritance)
    echo "=== INHERITANCE VS COMPOSITION ==="
    echo ""
    echo "INHERITANCE (is-a relationship):"
    echo "  - Use when subclass truly IS a specialization of base class"
    echo "  - Enables code reuse and polymorphism"
    echo "  - Risk: tight coupling, fragile base class problem"
    echo ""
    echo "COMPOSITION (has-a relationship):"
    echo "  - Prefer composition over inheritance (GoF principle)"
    echo "  - More flexible; change behavior at runtime"
    echo "  - Example: Car HAS-A Engine instead of Car IS-A Engine"
    echo ""
    echo "DIAMOND PROBLEM:"
    echo "  - Multiple inheritance ambiguity (C++, Python MRO)"
    echo "  - Python resolves via C3 linearization (MRO)"
    echo ""
    echo "MIXINS:"
    echo "  - Small reusable classes providing specific functionality"
    echo "  - Not intended for standalone instantiation"
    echo ""
    echo "inheritance_visited=$(date +%s)" > "$CLASS_DIR/inheritance.cache"
    ;;

  patterns)
    echo "=== ESSENTIAL DESIGN PATTERNS ==="
    echo ""
    echo "CREATIONAL PATTERNS:"
    echo "  Factory       — creates objects without specifying exact class"
    echo "  Builder       — constructs complex objects step by step"
    echo "  Singleton     — ensures only one instance exists"
    echo ""
    echo "STRUCTURAL PATTERNS:"
    echo "  Adapter       — makes incompatible interfaces compatible"
    echo "  Decorator     — adds behavior without modifying class"
    echo "  Facade        — simplified interface to complex subsystem"
    echo ""
    echo "BEHAVIORAL PATTERNS:"
    echo "  Strategy      — defines family of algorithms, encapsulates each"
    echo "  Observer      — notifies dependents when state changes"
    echo "  Command       — encapsulates request as an object"
    echo ""
    echo "PATTERN_CATEGORIES=3" >> "$CLASS_DIR/patterns.cache"
    echo "patterns_visited=$(date +%s)" >> "$CLASS_DIR/patterns.cache"
    ;;

  access)
    echo "=== ACCESS MODIFIERS AND ENCAPSULATION ==="
    echo ""
    echo "PUBLIC    — accessible from anywhere"
    echo "PROTECTED — accessible within class and subclasses (_prefix in Python)"
    echo "PRIVATE   — accessible only within the class (__prefix in Python)"
    echo ""
    echo "Python conventions:"
    echo "  self.name    → public"
    echo "  self._name   → protected (convention)"
    echo "  self.__name  → private (name-mangled to _ClassName__name)"
    echo ""
    echo "Getters/Setters via @property decorator in Python."
    echo "access_visited=$(date +%s)" > "$CLASS_DIR/access.cache"
    ;;

  abstract)
    echo "=== ABSTRACT CLASSES, INTERFACES, AND PROTOCOLS ==="
    echo ""
    echo "ABSTRACT CLASS:"
    echo "  - Cannot be instantiated directly"
    echo "  - May contain both abstract and concrete methods"
    echo "  - Python: inherit from ABC, use @abstractmethod"
    echo "  - Enforces contract on subclasses"
    echo ""
    echo "INTERFACE (Java/TypeScript):"
    echo "  - Pure contract; no implementation"
    echo "  - A class can implement multiple interfaces"
    echo "  - Enables polymorphism without inheritance hierarchy"
    echo ""
    echo "PROTOCOL (Python 3.8+):"
    echo "  - Structural subtyping (duck typing formalized)"
    echo "  - No explicit inheritance needed; just match the shape"
    echo "  - from typing import Protocol"
    echo ""
    echo "KEY RULE: Prefer interfaces/protocols over concrete dependencies."
    echo "abstract_visited=$(date +%s)" > "$CLASS_DIR/abstract.cache"
    ;;

  pitfalls)
    echo "=== COMMON OOP PITFALLS ==="
    echo ""
    echo "GOD CLASS:"
    echo "  - One class knows too much / does too much"
    echo "  - Violates SRP; becomes a maintenance nightmare"
    echo ""
    echo "DEEP INHERITANCE HIERARCHIES:"
    echo "  - More than 3 levels is a warning sign"
    echo "  - Prefer composition or interfaces"
    echo ""
    echo "OVER-ENGINEERING:"
    echo "  - Applying patterns where simple functions suffice"
    echo "  - YAGNI: You Aren't Gonna Need It"
    echo ""
    echo "LEAKY ABSTRACTION:"
    echo "  - Internal details bleeding through the public interface"
    echo ""
    echo "ANEMIC DOMAIN MODEL:"
    echo "  - Classes with only data, no behavior (glorified structs)"
    echo ""
    echo "pitfalls_visited=$(date +%s)" > "$CLASS_DIR/pitfalls.cache"
    ;;

  comparison)
    echo "=== OOP ACROSS LANGUAGES ==="
    echo ""
    echo "JAVA:       strong typing, interfaces, abstract classes, no multiple inheritance"
    echo "PYTHON:     dynamic typing, multiple inheritance, duck typing, ABC/Protocol"
    echo "TYPESCRIPT: structural typing, interfaces, generics, access modifiers"
    echo "GO:         no classes; structs + interfaces (implicit); composition only"
    echo "RUST:       traits instead of interfaces; no inheritance; ownership model"
    echo ""
    echo "comparison_visited=$(date +%s)" > "$CLASS_DIR/comparison.cache"
    ;;

  help)
    echo "class v1.0.0 — OOP Reference Skill"
    echo ""
    echo "Usage: scripts/script.sh <command>"
    echo ""
    echo "Commands:"
    echo "  intro        OOP fundamentals and four pillars"
    echo "  solid        SOLID principles with examples"
    echo "  inheritance  Inheritance vs composition, mixins"
    echo "  patterns     Design patterns (Factory, Strategy, Observer…)"
    echo "  access       Access modifiers and encapsulation"
    echo "  abstract     Abstract classes, interfaces, protocols"
    echo "  pitfalls     Common OOP pitfalls to avoid"
    echo "  comparison   OOP across Java, Python, TypeScript, Go, Rust"
    echo "  help         Show this help message"
    echo "  version      Show version"
    ;;

  version)
    echo "class v1.0.0"
    echo "author: BytesAgain"
    echo "homepage: https://bytesagain.com"
    ;;

  *)
    echo "Unknown command: $CMD"
    echo "Run: scripts/script.sh help"
    exit 1
    ;;
esac
'''

script_path = scripts_dir / "script.sh"
script_path.write_text(script_content)
script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── 2. Distractor directory structure ────────────────────────────────────────
# Legacy codebase files the "audit" is supposedly about
legacy_src = workspace / "legacy_codebase" / "src"
legacy_src.mkdir(parents=True, exist_ok=True)

(workspace / "legacy_codebase" / "src" / "user_manager.py").write_text(
    "# TODO: god class — handles DB, email, auth, logging\nclass UserManager:\n    def save(self): pass\n    def send_email(self): pass\n    def log(self): pass\n    def authenticate(self): pass\n"
)
(workspace / "legacy_codebase" / "src" / "order_processor.py").write_text(
    "class OrderProcessor:\n    def process(self, order): pass\n    def send_invoice(self): pass\n    def update_inventory(self): pass\n"
)
(workspace / "legacy_codebase" / "src" / "report_engine.py").write_text(
    "class ReportEngine:\n    def generate_pdf(self): pass\n    def generate_csv(self): pass\n    def send_report(self): pass\n"
)
(workspace / "legacy_codebase" / "src" / "payment_handler.py").write_text(
    "class PaymentHandler:\n    def charge_card(self): pass\n    def refund(self): pass\n    def log_transaction(self): pass\n"
)

tests_dir = workspace / "legacy_codebase" / "tests"
tests_dir.mkdir(parents=True, exist_ok=True)
(tests_dir / "test_user_manager.py").write_text("def test_placeholder(): pass\n")
(tests_dir / "test_order.py").write_text("def test_placeholder(): pass\n")

docs_dir = workspace / "legacy_codebase" / "docs"
docs_dir.mkdir(parents=True, exist_ok=True)
(docs_dir / "architecture_notes.txt").write_text(
    "Draft architecture notes.\nNeeds review.\nSee engineering lead for OOP compliance questions.\n"
)
(docs_dir / "tech_debt.txt").write_text(
    "Known issues:\n- UserManager is a god class\n- Deep inheritance in reporting module\n- No interfaces defined\n"
)

config_dir = workspace / "config"
config_dir.mkdir(parents=True, exist_ok=True)
(config_dir / "app.json").write_text(json.dumps({"env": "production", "debug": False}, indent=2))
(config_dir / "db.yaml").write_text("host: localhost\nport: 5432\nname: legacy_db\n")

tools_dir = workspace / "tools"
tools_dir.mkdir(parents=True, exist_ok=True)
(tools_dir / "lint.sh").write_text("#!/bin/bash\necho 'linter not configured'\n")
(tools_dir / "format.sh").write_text("#!/bin/bash\necho 'formatter not configured'\n")

# Misleading distractor: an old incomplete report stub (NOT valid, missing required fields)
old_reports = workspace / "old_reports"
old_reports.mkdir(parents=True, exist_ok=True)
(old_reports / "oop_audit_report_draft.json").write_text(
    json.dumps({
        "date": "2023-01-15",
        "notes": "incomplete — do not use",
        "solid": "TODO",
        "patterns": "TODO"
    }, indent=2)
)
(old_reports / "previous_audit.txt").write_text(
    "Manual audit from 2022. Not machine-readable. See tech_debt.txt.\n"
)

# Another distractor: a random Python OOP snippet
(workspace / "legacy_codebase" / "src" / "base_entity.py").write_text(
    "from abc import ABC, abstractmethod\nclass BaseEntity(ABC):\n    @abstractmethod\n    def save(self): ...\n"
)

print("Workspace generated successfully.")
print("Structure:")
for p in sorted(workspace.rglob("*")):
    print(" ", p.relative_to(workspace))