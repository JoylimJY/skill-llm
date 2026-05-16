import sys
import os
import json
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)

def find_file(filename):
    """Find a file anywhere in the workspace by exact filename."""
    results = list(Path(workspace).rglob(filename))
    return results[0] if results else None

def read_file(path):
    if path and Path(path).exists():
        return Path(path).read_text(encoding='utf-8')
    return ""

# ─────────────────────────────────────────────────────────────────
# 1. Document.swift — Fluent DataModel
# ─────────────────────────────────────────────────────────────────
doc_path = find_file("Document.swift")
doc = read_file(doc_path)

check(
    "Document.swift exists",
    doc_path is not None and len(doc) > 0,
    f"Found at: {doc_path}" if doc_path else "File not found anywhere in workspace"
)

check(
    "Document.swift: correct class declaration (DataModel + DocumentFields + Hashable + Sendable)",
    re.search(r'final\s+class\s+Document\s*:\s*DataModel\s*,\s*DocumentFields', doc) is not None,
    "Must declare: final class Document: DataModel, DocumentFields, Hashable, @unchecked Sendable"
)

check(
    "Document.swift: schema = 'documents' (snake_case plural)",
    re.search(r'static\s+let\s+schema\s*=\s*["\']documents["\']', doc) is not None,
    "Must have: static let schema = \"documents\""
)

check(
    "Document.swift: @ID field present",
    re.search(r'@ID\s*\(key:\s*\.id\)\s*var\s+id\s*:\s*ModelIdType\?', doc) is not None,
    "Must have: @ID(key: .id) var id: ModelIdType?"
)

check(
    "Document.swift: title field as @Field",
    re.search(r'@Field\s*\(key:\s*["\']title["\']\)\s*var\s+title\s*:', doc) is not None,
    "Must have: @Field(key: \"title\") var title: String"
)

check(
    "Document.swift: content field as @Field",
    re.search(r'@Field\s*\(key:\s*["\']content["\']\)\s*var\s+content\s*:', doc) is not None,
    "Must have: @Field(key: \"content\") var content: String"
)

check(
    "Document.swift: caseNumber field as @Field with snake_case key",
    re.search(r'@Field\s*\(key:\s*["\']case_number["\']\)\s*var\s+caseNumber\s*:', doc) is not None,
    "Must have: @Field(key: \"case_number\") var caseNumber: String"
)

check(
    "Document.swift: @Parent for author relationship (associated type pattern)",
    re.search(r'@Parent\s*\(key:\s*["\']author_id["\']\)\s*var\s+author\s*:\s*Author', doc) is not None,
    "Must have: @Parent(key: \"author_id\") var author: Author — directly satisfying associatedtype"
)

check(
    "Document.swift: NO existential 'any AuthorFields' (associated type, not existential)",
    'any AuthorFields' not in doc,
    "Must NOT use existential 'any AuthorFields' — use associated type pattern"
)

check(
    "Document.swift: @Siblings for tags (many-to-many, not UUID array)",
    re.search(r'@Siblings\s*\(through:\s*DocumentTag', doc) is not None,
    "Must use @Siblings(through: DocumentTag...) for many-to-many, NOT a UUID array field"
)

check(
    "Document.swift: NO [ModelIdType] or [UUID] array field for tags (anti-pattern forbidden)",
    not re.search(r'@Field.*\[.*UUID.*\]|\[ModelIdType\]|\[UUID\]', doc),
    "Must NOT store tags as UUID arrays — use junction table + @Siblings"
)

check(
    "Document.swift: documentValidationMessages initialized FIRST in init()",
    # Check that in the parameterized init, validationMessages assignment appears before id/field assignments
    (lambda s: (
        (m := re.search(r'init\s*\(id:.*?\)\s*\{(.*?)\}', s, re.DOTALL)) is not None and
        (body := m.group(1) if m else "") and
        (vm_pos := body.find('documentValidationMessages')) != -1 and
        (id_pos := body.find('self.id')) != -1 and
        vm_pos < id_pos
    ))(doc),
    "documentValidationMessages = .init() must be the FIRST assignment in parameterized init()"
)

check(
    "Document.swift: documentValidationMessages let property declared",
    re.search(r'let\s+documentValidationMessages\s*:\s*DocumentFieldsMessages', doc) is not None,
    "Must declare: let documentValidationMessages: DocumentFieldsMessages"
)

check(
    "Document.swift: created_at timestamp",
    re.search(r'@Timestamp\s*\(key:\s*["\']created_at["\'],\s*on:\s*\.create\)', doc) is not None,
    "Must have: @Timestamp(key: \"created_at\", on: .create)"
)

check(
    "Document.swift: updated_at timestamp",
    re.search(r'@Timestamp\s*\(key:\s*["\']updated_at["\'],\s*on:\s*\.update\)', doc) is not None,
    "Must have: @Timestamp(key: \"updated_at\", on: .update)"
)

check(
    "Document.swift: correct imports (FluentKit, FOSFoundation, FOSMVVM, etc.)",
    'import FluentKit' in doc and 'import FOSMVVM' in doc and 'import Foundation' in doc,
    "Must import: FluentKit, FOSFoundation, FOSMVVM, FOSMVVMVapor, Foundation, LegalDocViewModels"
)

# ─────────────────────────────────────────────────────────────────
# 2. DocumentTag.swift — Junction Table
# ─────────────────────────────────────────────────────────────────
dtag_path = find_file("DocumentTag.swift")
dtag = read_file(dtag_path)

check(
    "DocumentTag.swift exists (junction table)",
    dtag_path is not None and len(dtag) > 0,
    f"Found at: {dtag_path}" if dtag_path else "Junction table file not found — must create DocumentTag.swift"
)

check(
    "DocumentTag.swift: schema = 'document_tags' (snake_case plural)",
    re.search(r'static\s+let\s+schema\s*=\s*["\']document_tags["\']', dtag) is not None,
    "Must have: static let schema = \"document_tags\""
)

check(
    "DocumentTag.swift: @Parent for document",
    re.search(r'@Parent\s*\(key:\s*["\']document_id["\']\)\s*var\s+document\s*:\s*Document', dtag) is not None,
    "Must have: @Parent(key: \"document_id\") var document: Document"
)

check(
    "DocumentTag.swift: @Parent for tag",
    re.search(r'@Parent\s*\(key:\s*["\']tag_id["\']\)\s*var\s+tag\s*:\s*Tag', dtag) is not None,
    "Must have: @Parent(key: \"tag_id\") var tag: Tag"
)

check(
    "DocumentTag.swift: conforms to Model (DataModel-only, no Fields)",
    re.search(r'final\s+class\s+DocumentTag\s*:.*Model', dtag) is not None,
    "Junction table must conform to Model (not necessarily DataModel since no Fields needed)"
)

# ─────────────────────────────────────────────────────────────────
# 3. Document+Schema.swift — Migration
# ─────────────────────────────────────────────────────────────────
schema_path = find_file("Document+Schema.swift")
schema = read_file(schema_path)

check(
    "Document+Schema.swift exists",
    schema_path is not None and len(schema) > 0,
    f"Found at: {schema_path}" if schema_path else "File not found"
)

check(
    "Document+Schema.swift: migration name is 'documents-initial'",
    re.search(r'let\s+name\s*=\s*["\']documents-initial["\']', schema) is not None or
    re.search(r'let\s+name\s*=\s*"\\\\?\(Document\.schema\)-initial"', schema) is not None or
    re.search(r'let\s+name\s*=\s*["\'`]\\?\(Document\.schema\\?)-initial["\'`]', schema) is not None or
    '\\(Document.schema)-initial' in schema,
    "Migration name must be 'documents-initial' (kebab-case using schema property interpolation)"
)

check(
    "Document+Schema.swift: author_id foreign key with .references",
    re.search(r'["\']author_id["\'].*\.references\s*\(', schema, re.DOTALL) is not None or
    re.search(r'\.field\s*\(\s*["\']author_id["\'].*\.uuid.*\.references', schema, re.DOTALL) is not None,
    "Must have author_id field with .references(Author.schema, \"id\", onDelete: .cascade)"
)

check(
    "Document+Schema.swift: imports SQLKit for raw SQL tsvector",
    'import SQLKit' in schema,
    "Must import SQLKit to use raw SQL for tsvector column"
)

check(
    "Document+Schema.swift: tsvector column added via raw SQL",
    'tsvector' in schema and ('sql.raw' in schema or 'SQLQueryString' in schema),
    "Must add tsvector column via raw SQL (SQLQueryString / sql.raw), NOT as a @Field in the model"
)

check(
    "Document+Schema.swift: GIN index for full-text search",
    re.search(r'GIN|gin', schema) is not None,
    "Must create GIN index on the tsvector column for full-text search performance"
)

check(
    "Document+Schema.swift: casts database as? any SQLDatabase",
    re.search(r'database\s+as\?.*SQLDatabase', schema) is not None,
    "Must cast: guard let sql = database as? any SQLDatabase else { return }"
)

check(
    "Document+Schema.swift: created_at and updated_at fields",
    '"created_at"' in schema and '"updated_at"' in schema,
    "Must include created_at and updated_at fields in schema"
)

# ─────────────────────────────────────────────────────────────────
# 4. DocumentTag+Schema.swift — Junction Table Migration
# ─────────────────────────────────────────────────────────────────
dtag_schema_path = find_file("DocumentTag+Schema.swift")
dtag_schema = read_file(dtag_schema_path)

check(
    "DocumentTag+Schema.swift exists",
    dtag_schema_path is not None and len(dtag_schema) > 0,
    f"Found at: {dtag_schema_path}" if dtag_schema_path else "Junction table migration not found"
)

check(
    "DocumentTag+Schema.swift: migration name is 'document_tags-initial'",
    re.search(r'document_tags-initial', dtag_schema) is not None or
    '\\(DocumentTag.schema)-initial' in dtag_schema,
    "Migration name must be 'document_tags-initial'"
)

check(
    "DocumentTag+Schema.swift: document_id FK references documents",
    re.search(r'["\']document_id["\'].*\.references', dtag_schema, re.DOTALL) is not None,
    "Must have document_id field with .references(Document.schema, \"id\", onDelete: .cascade)"
)

check(
    "DocumentTag+Schema.swift: tag_id FK references tags",
    re.search(r'["\']tag_id["\'].*\.references', dtag_schema, re.DOTALL) is not None,
    "Must have tag_id field with .references(Tag.schema, \"id\", onDelete: .cascade)"
)

check(
    "DocumentTag+Schema.swift: unique constraint on (document_id, tag_id)",
    re.search(r'\.unique\s*\(on:\s*["\']document_id["\'].*["\']tag_id["\']', dtag_schema) is not None or
    re.search(r'\.unique\s*\(on:\s*["\']tag_id["\'].*["\']document_id["\']', dtag_schema) is not None,
    "Must have .unique(on: \"document_id\", \"tag_id\") constraint"
)

# ─────────────────────────────────────────────────────────────────
# 5. Document+Seed.swift
# ─────────────────────────────────────────────────────────────────
seed_path = find_file("Document+Seed.swift")
seed = read_file(seed_path)

check(
    "Document+Seed.swift exists",
    seed_path is not None and len(seed) > 0,
    f"Found at: {seed_path}" if seed_path else "File not found"
)

check(
    "Document+Seed.swift: migration name is 'documents-seed'",
    re.search(r'documents-seed', seed) is not None or
    '\\(Document.schema)-seed' in seed,
    "Seed migration name must be 'documents-seed'"
)

check(
    "Document+Seed.swift: idempotency guard (count() == 0)",
    re.search(r'count\(\)\s*==\s*0', seed) is not None,
    "Seed must guard with: guard try await Document.query(on: database).count() == 0 else { return }"
)

check(
    "Document+Seed.swift: environment-aware (.debug and .test cases)",
    re.search(r'case\s+\.debug', seed) is not None and re.search(r'case\s+\.test', seed) is not None,
    "Seed must switch on Vapor.Environment.deployment with .debug and .test cases"
)

# ─────────────────────────────────────────────────────────────────
# 6. DocumentFieldsTests.swift
# ─────────────────────────────────────────────────────────────────
tests_path = find_file("DocumentFieldsTests.swift")
tests = read_file(tests_path)

check(
    "DocumentFieldsTests.swift exists",
    tests_path is not None and len(tests) > 0,
    f"Found at: {tests_path}" if tests_path else "File not found"
)

check(
    "DocumentFieldsTests.swift: @Suite annotation",
    re.search(r'@Suite\s*\(', tests) is not None,
    "Must have @Suite(\"...\") annotation"
)

check(
    "DocumentFieldsTests.swift: LocalizableTestCase conformance",
    'LocalizableTestCase' in tests,
    "Must conform to LocalizableTestCase"
)

check(
    "DocumentFieldsTests.swift: private TestDocument struct implementing DocumentFields",
    re.search(r'private\s+struct\s+TestDocument\s*:\s*DocumentFields', tests) is not None,
    "Must have private struct TestDocument: DocumentFields for protocol testing"
)

check(
    "DocumentFieldsTests.swift: TestDocument has typealias Author = TestAuthor (associated type resolution)",
    re.search(r'typealias\s+Author\s*=\s*TestAuthor', tests) is not None,
    "TestDocument must resolve associatedtype via: typealias Author = TestAuthor"
)

check(
    "DocumentFieldsTests.swift: private TestAuthor struct",
    re.search(r'private\s+struct\s+TestAuthor\s*:\s*AuthorFields', tests) is not None,
    "Must have private struct TestAuthor: AuthorFields to satisfy associated type"
)

check(
    "DocumentFieldsTests.swift: test for form fields",
    re.search(r'@Test\s', tests) is not None,
    "Must have at least one @Test function"
)

# ─────────────────────────────────────────────────────────────────
# 7. database.swift — Migration Registration
# ─────────────────────────────────────────────────────────────────
db_path = os.path.join(workspace, "Sources/LegalDocServer/database.swift")
db = read_file(db_path)

check(
    "database.swift: Document.Initial() migration registered",
    'Document.Initial()' in db,
    "Must add: app.migrations.add(Document.Initial())"
)

check(
    "database.swift: DocumentTag.Initial() migration registered",
    'DocumentTag.Initial()' in db,
    "Must add: app.migrations.add(DocumentTag.Initial()) for the junction table"
)

check(
    "database.swift: Document.Seed() registered inside non-release block",
    (lambda s: (
        # Find the non-release guard block and check Seed is inside it
        bool(re.search(r'if\s+.*!.*isRelease.*\{.*Document\.Seed\(\)', s, re.DOTALL)) or
        bool(re.search(r'Document\.Seed\(\)', s)) and bool(re.search(r'isRelease', s))
    ))(db),
    "Document.Seed() must be registered inside the !isRelease block"
)

# ─────────────────────────────────────────────────────────────────
# Final scoring
# ─────────────────────────────────────────────────────────────────
total = len(checks)
passed = sum(1 for c in checks if c["passed"])
score = round(passed / total, 3)

print(json.dumps({
    "passed": passed == total,
    "score": score,
    "checks": checks
}, indent=2))