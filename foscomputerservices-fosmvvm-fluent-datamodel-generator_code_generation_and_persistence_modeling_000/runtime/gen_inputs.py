import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure for a Vapor/FOSMVVM project ──────────────────────────

dirs = [
    "Sources/LegalServer/DataModels",
    "Sources/LegalServer/Migrations",
    "Sources/LegalServer/Controllers",
    "Sources/LegalServer/Routes",
    "Sources/SharedViewModels/FieldModels",
    "Sources/SharedViewModels/ViewModels",
    "Tests/SharedViewModelsTests/FieldModels",
    "Tests/SharedViewModelsTests/ViewModels",
    "Resources/FieldModels",
    "docs",
    "scripts",
    "config",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Package.swift ─────────────────────────────────────────────────────────────
package_swift = '''\
// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "LegalServer",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "SharedViewModels", targets: ["SharedViewModels"]),
        .executable(name: "LegalServer", targets: ["LegalServer"]),
    ],
    dependencies: [
        .package(url: "https://github.com/vapor/vapor.git", from: "4.0.0"),
        .package(url: "https://github.com/vapor/fluent.git", from: "4.0.0"),
        .package(url: "https://github.com/vapor/fluent-postgres-driver.git", from: "2.0.0"),
        .package(url: "https://github.com/foscomputerservices/FOSUtilities.git", from: "1.0.0"),
    ],
    targets: [
        .target(
            name: "SharedViewModels",
            dependencies: [
                .product(name: "FOSMVVM", package: "FOSUtilities"),
                .product(name: "FOSFoundation", package: "FOSUtilities"),
            ]
        ),
        .target(
            name: "LegalServer",
            dependencies: [
                "SharedViewModels",
                .product(name: "Vapor", package: "vapor"),
                .product(name: "Fluent", package: "fluent"),
                .product(name: "FluentPostgresDriver", package: "fluent-postgres-driver"),
                .product(name: "FOSMVVMVapor", package: "FOSUtilities"),
            ]
        ),
        .testTarget(
            name: "SharedViewModelsTests",
            dependencies: [
                "SharedViewModels",
                .product(name: "FOSTesting", package: "FOSUtilities"),
            ],
            resources: [.copy("Resources")]
        ),
    ]
)
'''
with open(os.path.join(workspace, "Package.swift"), "w") as f:
    f.write(package_swift)

# ── Existing LegalUser DataModel (already exists - reference model) ──────────
legal_user_model = '''\
import FluentKit
import FOSFoundation
import FOSMVVM
import FOSMVVMVapor
import Foundation
import SharedViewModels

final class LegalUser: DataModel, LegalUserFields, Hashable, @unchecked Sendable {
    static let schema = "legal_users"

    @ID(key: .id) var id: ModelIdType?

    @Field(key: "email") var email: String
    @Field(key: "full_name") var fullName: String
    @Field(key: "bar_number") var barNumber: String

    let legalUserValidationMessages: LegalUserFieldsMessages

    @Timestamp(key: "created_at", on: .create) var createdAt: Date?
    @Timestamp(key: "updated_at", on: .update) var updatedAt: Date?

    init() {
        self.legalUserValidationMessages = .init()
    }

    init(id: ModelIdType? = nil, email: String, fullName: String, barNumber: String) {
        self.legalUserValidationMessages = .init()
        self.id = id
        self.email = email
        self.fullName = fullName
        self.barNumber = barNumber
    }
}
'''
with open(os.path.join(workspace, "Sources/LegalServer/DataModels/LegalUser.swift"), "w") as f:
    f.write(legal_user_model)

# ── LegalUser Schema migration ────────────────────────────────────────────────
legal_user_schema = '''\
import Fluent

extension LegalUser {
    struct Initial: AsyncMigration {
        let name = "legal_users-initial"

        func prepare(on database: any Database) async throws {
            try await database.schema(LegalUser.schema)
                .id()
                .field("email", .string, .required)
                .field("full_name", .string, .required)
                .field("bar_number", .string, .required)
                .field("created_at", .datetime)
                .field("updated_at", .datetime)
                .unique(on: "email")
                .create()
        }

        func revert(on database: any Database) async throws {
            try await database.schema(LegalUser.schema).delete()
        }
    }
}
'''
with open(os.path.join(workspace, "Sources/LegalServer/Migrations/LegalUser+Schema.swift"), "w") as f:
    f.write(legal_user_schema)

# ── Existing Clause DataModel ─────────────────────────────────────────────────
clause_model = '''\
import FluentKit
import FOSFoundation
import FOSMVVM
import FOSMVVMVapor
import Foundation
import SharedViewModels

final class Clause: DataModel, ClauseFields, Hashable, @unchecked Sendable {
    static let schema = "clauses"

    @ID(key: .id) var id: ModelIdType?

    @Field(key: "title") var title: String
    @Field(key: "body") var body: String
    @Field(key: "clause_type") var clauseType: String

    let clauseValidationMessages: ClauseFieldsMessages

    @Timestamp(key: "created_at", on: .create) var createdAt: Date?
    @Timestamp(key: "updated_at", on: .update) var updatedAt: Date?

    init() {
        self.clauseValidationMessages = .init()
    }

    init(id: ModelIdType? = nil, title: String, body: String, clauseType: String) {
        self.clauseValidationMessages = .init()
        self.id = id
        self.title = title
        self.body = body
        self.clauseType = clauseType
    }
}
'''
with open(os.path.join(workspace, "Sources/LegalServer/DataModels/Clause.swift"), "w") as f:
    f.write(clause_model)

# ── Clause Schema migration ───────────────────────────────────────────────────
clause_schema = '''\
import Fluent

extension Clause {
    struct Initial: AsyncMigration {
        let name = "clauses-initial"

        func prepare(on database: any Database) async throws {
            try await database.schema(Clause.schema)
                .id()
                .field("title", .string, .required)
                .field("body", .string, .required)
                .field("clause_type", .string, .required)
                .field("created_at", .datetime)
                .field("updated_at", .datetime)
                .create()
        }

        func revert(on database: any Database) async throws {
            try await database.schema(Clause.schema).delete()
        }
    }
}
'''
with open(os.path.join(workspace, "Sources/LegalServer/Migrations/Clause+Schema.swift"), "w") as f:
    f.write(clause_schema)

# ── ContractFields Protocol (already exists from fields-generator) ────────────
contract_fields_protocol = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public protocol ContractFields: ValidatableModel, Codable, Sendable {
    associatedtype Creator: LegalUserFields

    var id: ModelIdType? { get set }
    var title: String { get set }
    var contractNumber: String { get set }
    var status: String { get set }
    var effectiveDate: Date { get set }
    var createdBy: Creator { get set }

    var contractValidationMessages: ContractFieldsMessages { get }
}

public extension ContractFields {
    static var titleField: FormField<Self, String> {
        .init(keyPath: \\.title, fieldId: "title", label: "Contract Title", placeholder: "Enter contract title")
    }

    static var contractNumberField: FormField<Self, String> {
        .init(keyPath: \\.contractNumber, fieldId: "contract_number", label: "Contract Number", placeholder: "e.g. CTR-2025-001")
    }

    static var statusField: FormField<Self, String> {
        .init(keyPath: \\.status, fieldId: "status", label: "Status", placeholder: "draft, active, expired")
    }

    static var effectiveDateField: FormField<Self, Date> {
        .init(keyPath: \\.effectiveDate, fieldId: "effective_date", label: "Effective Date", placeholder: "Select date")
    }
}
'''
with open(os.path.join(workspace, "Sources/SharedViewModels/FieldModels/ContractFields.swift"), "w") as f:
    f.write(contract_fields_protocol)

# ── LegalUserFields Protocol ──────────────────────────────────────────────────
legal_user_fields_protocol = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public protocol LegalUserFields: ValidatableModel, Codable, Sendable {
    var id: ModelIdType? { get set }
    var email: String { get set }
    var fullName: String { get set }
    var barNumber: String { get set }

    var legalUserValidationMessages: LegalUserFieldsMessages { get }
}
'''
with open(os.path.join(workspace, "Sources/SharedViewModels/FieldModels/LegalUserFields.swift"), "w") as f:
    f.write(legal_user_fields_protocol)

# ── ClauseFields Protocol ─────────────────────────────────────────────────────
clause_fields_protocol = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public protocol ClauseFields: ValidatableModel, Codable, Sendable {
    var id: ModelIdType? { get set }
    var title: String { get set }
    var body: String { get set }
    var clauseType: String { get set }

    var clauseValidationMessages: ClauseFieldsMessages { get }
}
'''
with open(os.path.join(workspace, "Sources/SharedViewModels/FieldModels/ClauseFields.swift"), "w") as f:
    f.write(clause_fields_protocol)

# ── ContractFieldsMessages ────────────────────────────────────────────────────
contract_fields_messages = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public struct ContractFieldsMessages: Codable, Sendable {
    public var titleRequired: String
    public var contractNumberFormat: String
    public var statusInvalid: String

    public init(
        titleRequired: String = "",
        contractNumberFormat: String = "",
        statusInvalid: String = ""
    ) {
        self.titleRequired = titleRequired
        self.contractNumberFormat = contractNumberFormat
        self.statusInvalid = statusInvalid
    }
}
'''
with open(os.path.join(workspace, "Sources/SharedViewModels/FieldModels/ContractFieldsMessages.swift"), "w") as f:
    f.write(contract_fields_messages)

# ── LegalUserFieldsMessages ───────────────────────────────────────────────────
legal_user_fields_messages = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public struct LegalUserFieldsMessages: Codable, Sendable {
    public var emailRequired: String
    public var barNumberInvalid: String

    public init(emailRequired: String = "", barNumberInvalid: String = "") {
        self.emailRequired = emailRequired
        self.barNumberInvalid = barNumberInvalid
    }
}
'''
with open(os.path.join(workspace, "Sources/SharedViewModels/FieldModels/LegalUserFieldsMessages.swift"), "w") as f:
    f.write(legal_user_fields_messages)

# ── ClauseFieldsMessages ──────────────────────────────────────────────────────
clause_fields_messages = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public struct ClauseFieldsMessages: Codable, Sendable {
    public var titleRequired: String
    public var bodyRequired: String

    public init(titleRequired: String = "", bodyRequired: String = "") {
        self.titleRequired = titleRequired
        self.bodyRequired = bodyRequired
    }
}
'''
with open(os.path.join(workspace, "Sources/SharedViewModels/FieldModels/ClauseFieldsMessages.swift"), "w") as f:
    f.write(clause_fields_messages)

# ── Existing database.swift ───────────────────────────────────────────────────
database_swift = '''\
import Fluent
import Vapor

public func configureDatabases(_ app: Application) async throws {
    let dbId = DatabaseID.psql

    // MARK: Migrations
    app.migrations.add(LegalUser.Initial())
    app.migrations.add(Clause.Initial())

    // MARK: Seed
    if !app.environment.isRelease {
        app.migrations.add(LegalUser.Seed(), to: dbId)
        app.migrations.add(Clause.Seed(), to: dbId)
    }

    try await app.autoMigrate()
}
'''
with open(os.path.join(workspace, "Sources/LegalServer/database.swift"), "w") as f:
    f.write(database_swift)

# ── Distractor: a Controller ──────────────────────────────────────────────────
controller = '''\
import Vapor
import Fluent

struct LegalUserController: RouteCollection {
    func boot(routes: RoutesBuilder) throws {
        let users = routes.grouped("users")
        users.get(use: index)
        users.post(use: create)
    }

    func index(req: Request) async throws -> [LegalUser] {
        try await LegalUser.query(on: req.db).all()
    }

    func create(req: Request) async throws -> LegalUser {
        let user = try req.content.decode(LegalUser.self)
        try await user.save(on: req.db)
        return user
    }
}
'''
with open(os.path.join(workspace, "Sources/LegalServer/Controllers/LegalUserController.swift"), "w") as f:
    f.write(controller)

# ── Distractor: a Route file ──────────────────────────────────────────────────
routes = '''\
import Vapor

func routes(_ app: Application) throws {
    try app.register(collection: LegalUserController())
}
'''
with open(os.path.join(workspace, "Sources/LegalServer/Routes/routes.swift"), "w") as f:
    f.write(routes)

# ── Distractor: docs ──────────────────────────────────────────────────────────
with open(os.path.join(workspace, "docs/DEPLOYMENT.md"), "w") as f:
    f.write("# Deployment Guide\n\nDeploy via Docker Compose.\n")

with open(os.path.join(workspace, "docs/API.md"), "w") as f:
    f.write("# API Reference\n\nSee Swagger at /docs.\n")

# ── Distractor: config ────────────────────────────────────────────────────────
with open(os.path.join(workspace, "config/production.env"), "w") as f:
    f.write("DATABASE_URL=postgres://legal:secret@db:5432/legaldb\nPORT=8080\n")

with open(os.path.join(workspace, "config/test.env"), "w") as f:
    f.write("DATABASE_URL=postgres://legal:secret@localhost:5432/legaldb_test\nPORT=8081\n")

# ── Distractor: scripts ───────────────────────────────────────────────────────
with open(os.path.join(workspace, "scripts/reset_db.sh"), "w") as f:
    f.write("#!/bin/bash\necho 'Resetting database...'\n")

with open(os.path.join(workspace, "scripts/run_tests.sh"), "w") as f:
    f.write("#!/bin/bash\nswift test\n")

# ── Existing LegalUser Seed (reference pattern) ───────────────────────────────
legal_user_seed = '''\
import Fluent
import Vapor

extension LegalUser {
    struct Seed: AsyncMigration {
        let name = "legal_users-seed"

        func prepare(on database: any Database) async throws {
            guard try await LegalUser.query(on: database).count() == 0 else { return }

            let items: [LegalUser]
            switch Vapor.Environment.deployment {
            case .debug:
                items = try LegalUser.defaultDebugItems
            case .test:
                items = try LegalUser.defaultTestItems
            default:
                fatalError("Unknown Deployment: \\(Vapor.Environment.deployment)")
            }

            for item in items {
                try await item.save(on: database)
            }
        }

        func revert(on database: any Database) async throws {}
    }
}

private extension LegalUser {
    static var defaultDebugItems: [LegalUser] {
        get throws { [
            .init(email: "alice@lawfirm.com", fullName: "Alice Thornton", barNumber: "BAR-001"),
            .init(email: "bob@lawfirm.com", fullName: "Bob Martinez", barNumber: "BAR-002"),
        ] }
    }

    static var defaultTestItems: [LegalUser] {
        get throws { [
            .init(email: "test@lawfirm.com", fullName: "Test User", barNumber: "BAR-TEST"),
        ] }
    }
}
'''
with open(os.path.join(workspace, "Sources/LegalServer/Migrations/LegalUser+Seed.swift"), "w") as f:
    f.write(legal_user_seed)

# ── Existing LegalUserFieldsTests (reference test pattern) ───────────────────
legal_user_tests = '''\
import FOSFoundation
import FOSMVVM
import FOSTesting
import Foundation
import Testing
import SharedViewModels

@Suite("LegalUser Fields")
struct LegalUserFieldsTests: LocalizableTestCase {
    @Test func legalUserFormFields() throws {
        try expectFullFormFieldTests(LegalUser.emailField)
        try expectFullFormFieldTests(LegalUser.fullNameField)
        try expectFullFormFieldTests(LegalUser.barNumberField)
    }

    let locStore: LocalizationStore

    init() async throws {
        self.locStore = try Self.loadLocalizationStore(
            bundle: Bundle.module,
            resourceDirectoryName: ""
        )
    }
}

private struct TestLegalUser: LegalUserFields {
    var id: ModelIdType?
    var email: String
    var fullName: String
    var barNumber: String

    private(set) var legalUserValidationMessages: LegalUserFieldsMessages

    mutating func localizeMessages(encoder: JSONEncoder) throws {
        legalUserValidationMessages = try LegalUserFieldsMessages().toJSON(encoder: encoder).fromJSON()
    }

    init(
        id: ModelIdType? = .init(),
        email: String = "test@example.com",
        fullName: String = "Test User",
        barNumber: String = "BAR-000"
    ) {
        self.id = id
        self.email = email
        self.fullName = fullName
        self.barNumber = barNumber
        self.legalUserValidationMessages = .init()
    }
}
'''
with open(os.path.join(workspace, "Tests/SharedViewModelsTests/FieldModels/LegalUserFieldsTests.swift"), "w") as f:
    f.write(legal_user_tests)

# ── Distractor ViewModel files ────────────────────────────────────────────────
clause_vm = '''\
import FOSFoundation
import FOSMVVM
import Foundation
import SharedViewModels

public struct ClauseViewModel: ViewModel {
    public var id: ModelIdType?
    public var title: String
    public var clauseType: String
}
'''
with open(os.path.join(workspace, "Sources/SharedViewModels/ViewModels/ClauseViewModel.swift"), "w") as f:
    f.write(clause_vm)

# ── Distractor: bad/incomplete Contract attempt (wrong pattern) ───────────────
# This represents what a naive agent might produce without knowing the rules
bad_attempt_note = '''\
// NOTE: This file was started but never completed.
// TODO: Implement Contract model
// import Fluent
// final class Contract: Model { ... }
'''
with open(os.path.join(workspace, "Sources/LegalServer/DataModels/Contract.swift.draft"), "w") as f:
    f.write(bad_attempt_note)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_, files in os.walk(workspace):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath[len(workspace):]}")