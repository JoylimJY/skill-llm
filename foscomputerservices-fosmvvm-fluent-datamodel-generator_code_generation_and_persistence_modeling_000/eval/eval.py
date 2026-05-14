import sys
import json
import re
from pathlib import Path

def find_file(workspace: Path, filename: str):
    """Find a file anywhere in the workspace."""
    matches = list(workspace.rglob(filename))
    return matches[0] if matches else None

def read_file(path) -> str:
    if path is None:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""

def check(name: str, passed: bool, detail: str):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []

    # ─────────────────────────────────────────────────────────────────────────
    # FILE DISCOVERY
    # ─────────────────────────────────────────────────────────────────────────
    contract_model_path     = find_file(workspace, "Contract.swift")
    contract_schema_path    = find_file(workspace, "Contract+Schema.swift")
    contract_seed_path      = find_file(workspace, "Contract+Seed.swift")
    junction_model_path     = find_file(workspace, "ContractClause.swift")
    junction_schema_path    = find_file(workspace, "ContractClause+Schema.swift")
    contract_tests_path     = find_file(workspace, "ContractFieldsTests.swift")
    database_path           = workspace / "Sources" / "LegalServer" / "database.swift"

    contract_model   = read_file(contract_model_path)
    contract_schema  = read_file(contract_schema_path)
    contract_seed    = read_file(contract_seed_path)
    junction_model   = read_file(junction_model_path)
    junction_schema  = read_file(junction_schema_path)
    contract_tests   = read_file(contract_tests_path)
    database_src     = read_file(database_path)

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1: Contract.swift exists with correct class declaration
    # ─────────────────────────────────────────────────────────────────────────
    has_contract = bool(contract_model)
    checks.append(check(
        "Contract.swift exists",
        has_contract,
        f"Found at: {contract_model_path}" if has_contract else "Contract.swift not found anywhere in workspace"
    ))

    # CHECK 2: Contract conforms to DataModel, ContractFields, Hashable, @unchecked Sendable
    if has_contract:
        conformances = ["DataModel", "ContractFields", "Hashable", "@unchecked Sendable"]
        missing = [c for c in conformances if c not in contract_model]
        checks.append(check(
            "Contract conforms to required protocols",
            len(missing) == 0,
            f"Missing conformances: {missing}" if missing else "All required conformances present"
        ))
    else:
        checks.append(check("Contract conforms to required protocols", False, "File not found"))

    # CHECK 3: Contract.schema = "contracts" (snake_case plural)
    if has_contract:
        schema_match = re.search(r'static\s+let\s+schema\s*=\s*"contracts"', contract_model)
        checks.append(check(
            "Contract.schema is 'contracts'",
            bool(schema_match),
            "Found: static let schema = \"contracts\"" if schema_match else "Missing or incorrect static let schema = \"contracts\""
        ))
    else:
        checks.append(check("Contract.schema is 'contracts'", False, "File not found"))

    # CHECK 4: @Parent for createdBy (required relationship via associated type, not plain field)
    if has_contract:
        parent_created_by = re.search(r'@Parent\s*\([^)]*key:\s*"created_by"[^)]*\)\s*var\s+createdBy\s*:\s*LegalUser', contract_model)
        checks.append(check(
            "@Parent(key: 'created_by') var createdBy: LegalUser",
            bool(parent_created_by),
            "Correct @Parent declaration found" if parent_created_by else
            "@Parent(key: 'created_by') var createdBy: LegalUser not found — must use @Parent, not @Field or plain property"
        ))
    else:
        checks.append(check("@Parent for createdBy", False, "File not found"))

    # CHECK 5: @Siblings for clauses (many-to-many, NOT UUID array)
    if has_contract:
        has_uuid_array = bool(re.search(r'@Field.*\[.*UUID.*\]|@Field.*\[.*ModelIdType.*\]', contract_model))
        has_siblings = bool(re.search(r'@Siblings', contract_model))
        no_uuid_array = not has_uuid_array
        checks.append(check(
            "@Siblings used for clauses (not UUID array anti-pattern)",
            has_siblings and no_uuid_array,
            ("@Siblings found, no UUID array anti-pattern" if (has_siblings and no_uuid_array)
             else f"@Siblings present: {has_siblings}, UUID array anti-pattern present: {has_uuid_array}")
        ))
    else:
        checks.append(check("@Siblings for clauses", False, "File not found"))

    # CHECK 6: Timestamps present in Contract
    if has_contract:
        has_created_at = bool(re.search(r'@Timestamp\s*\(key:\s*"created_at",\s*on:\s*\.create\)', contract_model))
        has_updated_at = bool(re.search(r'@Timestamp\s*\(key:\s*"updated_at",\s*on:\s*\.update\)', contract_model))
        checks.append(check(
            "Timestamps (@Timestamp created_at and updated_at) in Contract",
            has_created_at and has_updated_at,
            "Both timestamps found" if (has_created_at and has_updated_at)
            else f"created_at: {has_created_at}, updated_at: {has_updated_at}"
        ))
    else:
        checks.append(check("Timestamps in Contract", False, "File not found"))

    # CHECK 7: contractValidationMessages initialized FIRST in init()
    # The first assignment in init() must be contractValidationMessages = .init()
    if has_contract:
        # Find the init() body and check that contractValidationMessages is assigned before self.id or field assignments
        # Look for pattern where validationMessages init comes first
        init_blocks = re.findall(r'init\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', contract_model, re.DOTALL)
        validation_first = False
        for block in init_blocks:
            lines = [l.strip() for l in block.strip().splitlines() if l.strip() and not l.strip().startswith("//")]
            if lines:
                first_line = lines[0]
                if "ValidationMessages" in first_line and ".init()" in first_line:
                    validation_first = True
                    break
        checks.append(check(
            "contractValidationMessages initialized FIRST in init()",
            validation_first,
            "Validation messages correctly initialized first" if validation_first
            else "contractValidationMessages must be the FIRST assignment in every init() — critical ordering constraint"
        ))
    else:
        checks.append(check("contractValidationMessages initialized first", False, "File not found"))

    # CHECK 8: Contract+Schema.swift exists with correct migration name
    has_schema = bool(contract_schema)
    checks.append(check(
        "Contract+Schema.swift exists",
        has_schema,
        f"Found at: {contract_schema_path}" if has_schema else "Contract+Schema.swift not found"
    ))

    if has_schema:
        # Migration name must be "contracts-initial"
        name_match = re.search(r'let\s+name\s*=\s*"contracts-initial"', contract_schema)
        checks.append(check(
            "Schema migration name is 'contracts-initial'",
            bool(name_match),
            "Correct migration name found" if name_match else
            "Migration name must be exactly \"contracts-initial\" (let name = \"contracts-initial\")"
        ))

        # Must have foreign key reference to legal_users for created_by
        fk_match = re.search(r'\.references\s*\(\s*(?:LegalUser\.schema|"legal_users")', contract_schema)
        # Also check field definition for created_by
        field_match = re.search(r'"created_by"', contract_schema)
        checks.append(check(
            "Schema has created_by FK referencing legal_users",
            bool(fk_match) and bool(field_match),
            "FK reference to legal_users found" if (fk_match and field_match)
            else f"FK to legal_users present: {bool(fk_match)}, 'created_by' field present: {bool(field_match)}"
        ))
    else:
        checks.append(check("Schema migration name", False, "File not found"))
        checks.append(check("Schema FK reference", False, "File not found"))

    # CHECK 9: Contract+Seed.swift with correct name and idempotency
    has_seed = bool(contract_seed)
    checks.append(check(
        "Contract+Seed.swift exists",
        has_seed,
        f"Found at: {contract_seed_path}" if has_seed else "Contract+Seed.swift not found"
    ))

    if has_seed:
        seed_name_match = re.search(r'let\s+name\s*=\s*"contracts-seed"', contract_seed)
        checks.append(check(
            "Seed migration name is 'contracts-seed'",
            bool(seed_name_match),
            "Correct seed name found" if seed_name_match else
            "Seed name must be exactly \"contracts-seed\""
        ))

        # Idempotency guard
        idempotent = bool(re.search(r'guard.*count\(\)\s*==\s*0', contract_seed))
        checks.append(check(
            "Seed is idempotent (guard count() == 0)",
            idempotent,
            "Idempotency guard found" if idempotent else
            "Seed must check guard try await Contract.query(on: database).count() == 0"
        ))

        # Environment awareness
        env_aware = bool(re.search(r'Environment\.deployment|environment\.isRelease|\.debug|\.test', contract_seed))
        checks.append(check(
            "Seed is environment-aware",
            env_aware,
            "Environment check found" if env_aware else
            "Seed must branch on Vapor.Environment.deployment for debug/test/release"
        ))
    else:
        checks.append(check("Seed migration name", False, "File not found"))
        checks.append(check("Seed idempotency", False, "File not found"))
        checks.append(check("Seed environment awareness", False, "File not found"))

    # CHECK 10: ContractClause junction model
    has_junction = bool(junction_model)
    checks.append(check(
        "ContractClause.swift (junction model) exists",
        has_junction,
        f"Found at: {junction_model_path}" if has_junction else
        "ContractClause.swift not found — many-to-many requires a junction table, not UUID arrays"
    ))

    if has_junction:
        # Junction schema name should be "contract_clauses" or similar snake_case plural
        junction_schema_val = re.search(r'static\s+let\s+schema\s*=\s*"([^"]+)"', junction_model)
        junction_schema_name = junction_schema_val.group(1) if junction_schema_val else ""
        # Accept contract_clauses or similar
        schema_ok = bool(re.search(r'contract.clauses?', junction_schema_name, re.IGNORECASE))
        checks.append(check(
            "Junction table schema is snake_case plural (e.g., contract_clauses)",
            schema_ok,
            f"Junction schema: '{junction_schema_name}'" if junction_schema_val else
            "Junction model schema name not found or incorrect"
        ))

        # Has two @Parent properties pointing to Contract and Clause
        parent_contract = bool(re.search(r'@Parent.*var\s+\w*[Cc]ontract\w*\s*:\s*Contract', junction_model))
        parent_clause   = bool(re.search(r'@Parent.*var\s+\w*[Cc]lause\w*\s*:\s*Clause', junction_model))
        checks.append(check(
            "Junction model has @Parent for both Contract and Clause",
            parent_contract and parent_clause,
            f"Contract @Parent: {parent_contract}, Clause @Parent: {parent_clause}"
        ))
    else:
        checks.append(check("Junction table schema name", False, "File not found"))
        checks.append(check("Junction @Parent properties", False, "File not found"))

    # CHECK 11: ContractClause+Schema.swift with unique constraint
    has_junction_schema = bool(junction_schema)
    checks.append(check(
        "ContractClause+Schema.swift exists",
        has_junction_schema,
        f"Found at: {junction_schema_path}" if has_junction_schema else "ContractClause+Schema.swift not found"
    ))

    if has_junction_schema:
        # Must have unique constraint on both FKs
        unique_match = re.search(r'\.unique\s*\(', junction_schema)
        checks.append(check(
            "Junction schema has unique constraint",
            bool(unique_match),
            "Unique constraint found" if unique_match else
            "Junction migration must include .unique(on: \"contract_id\", \"clause_id\") to prevent duplicates"
        ))

        # Migration name convention
        junc_name = re.search(r'let\s+name\s*=\s*"([^"]+)-initial"', junction_schema)
        checks.append(check(
            "Junction schema migration uses '-initial' naming convention",
            bool(junc_name),
            f"Found name: '{junc_name.group(0)}'" if junc_name else
            "Junction migration must follow naming: \"<schema>-initial\""
        ))

        # Must have cascade delete references
        cascade = bool(re.search(r'onDelete:\s*\.cascade', junction_schema))
        checks.append(check(
            "Junction schema has onDelete: .cascade references",
            cascade,
            "Cascade delete found" if cascade else
            "Junction FK constraints must include onDelete: .cascade"
        ))
    else:
        checks.append(check("Junction schema unique constraint", False, "File not found"))
        checks.append(check("Junction schema naming convention", False, "File not found"))
        checks.append(check("Junction schema cascade delete", False, "File not found"))

    # CHECK 12: ContractFieldsTests.swift with correct structure
    has_tests = bool(contract_tests)
    checks.append(check(
        "ContractFieldsTests.swift exists",
        has_tests,
        f"Found at: {contract_tests_path}" if has_tests else "ContractFieldsTests.swift not found"
    ))

    if has_tests:
        # @Suite annotation
        suite_match = re.search(r'@Suite\s*\(', contract_tests)
        checks.append(check(
            "Tests use @Suite annotation",
            bool(suite_match),
            "@Suite annotation found" if suite_match else "@Suite annotation missing"
        ))

        # LocalizableTestCase conformance
        localizable = bool(re.search(r'LocalizableTestCase', contract_tests))
        checks.append(check(
            "Tests conform to LocalizableTestCase",
            localizable,
            "LocalizableTestCase conformance found" if localizable else
            "Test struct must conform to LocalizableTestCase"
        ))

        # typealias for associated type satisfaction (Creator = TestLegalUser or similar)
        typealias_match = re.search(r'typealias\s+Creator\s*=\s*Test\w+', contract_tests)
        checks.append(check(
            "Test struct uses typealias to satisfy Creator associated type",
            bool(typealias_match),
            "typealias Creator = ... found" if typealias_match else
            "TestContract struct must use 'typealias Creator = TestLegalUser' to satisfy the associated type — NOT an existential type"
        ))

        # locStore: LocalizationStore property
        loc_store = bool(re.search(r'let\s+locStore\s*:\s*LocalizationStore', contract_tests))
        checks.append(check(
            "Tests have let locStore: LocalizationStore",
            loc_store,
            "locStore found" if loc_store else "locStore: LocalizationStore property missing in test suite"
        ))
    else:
        checks.append(check("@Suite annotation in tests", False, "File not found"))
        checks.append(check("LocalizableTestCase conformance in tests", False, "File not found"))
        checks.append(check("typealias for associated type in tests", False, "File not found"))
        checks.append(check("locStore in tests", False, "File not found"))

    # CHECK 13: database.swift updated with Contract migrations
    db_has_contract_initial = bool(re.search(r'Contract\.Initial\(\)', database_src))
    db_has_contract_seed    = bool(re.search(r'Contract\.Seed\(\)', database_src))
    checks.append(check(
        "database.swift registers Contract.Initial() migration",
        db_has_contract_initial,
        "Contract.Initial() found in database.swift" if db_has_contract_initial else
        "database.swift must have app.migrations.add(Contract.Initial())"
    ))
    checks.append(check(
        "database.swift registers Contract.Seed() migration",
        db_has_contract_seed,
        "Contract.Seed() found in database.swift" if db_has_contract_seed else
        "database.swift must have app.migrations.add(Contract.Seed(), to: dbId)"
    ))

    # CHECK 14: No existential types (any ContractFields, any LegalUserFields) in Contract.swift
    if has_contract:
        existential = bool(re.search(r'\bany\s+(?:ContractFields|LegalUserFields|ClauseFields)\b', contract_model))
        checks.append(check(
            "No existential types (any Protocol) used in Contract.swift",
            not existential,
            "No existential types found — correct" if not existential else
            "Existential types (any Protocol) are a code smell per FOSMVVM rules; use associated types or concrete types"
        ))
    else:
        checks.append(check("No existential types in Contract.swift", False, "File not found"))

    # ─────────────────────────────────────────────────────────────────────────
    # SCORING
    # ─────────────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument check", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    run_eval(sys.argv[1])