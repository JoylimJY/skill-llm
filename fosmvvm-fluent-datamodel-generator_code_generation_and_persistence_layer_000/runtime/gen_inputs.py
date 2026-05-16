import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Create the full project directory structure ---
dirs = [
    "Sources/LegalDocServer/DataModels",
    "Sources/LegalDocServer/Migrations",
    "Sources/LegalDocServer/Controllers",
    "Sources/LegalDocServer/Routes",
    "Sources/LegalDocViewModels/FieldModels",
    "Sources/LegalDocViewModels/ViewModels",
    "Resources/LegalDocViewModels/FieldModels",
    "Tests/LegalDocViewModelsTests/FieldModels",
    "Tests/LegalDocViewModelsTests/ViewModels",
    "docs",
    "scripts",
    "config",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Package.swift (shows Fluent is present) ---
package_swift = '''\
// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "LegalDocServer",
    platforms: [.macOS(.v14)],
    dependencies: [
        .package(url: "https://github.com/vapor/vapor.git", from: "4.0.0"),
        .package(url: "https://github.com/vapor/fluent.git", from: "4.0.0"),
        .package(url: "https://github.com/vapor/fluent-postgres-driver.git", from: "2.0.0"),
        .package(url: "https://github.com/foscomputerservices/FOSUtilities.git", from: "1.0.0"),
    ],
    targets: [
        .target(
            name: "LegalDocServer",
            dependencies: [
                .product(name: "Vapor", package: "vapor"),
                .product(name: "Fluent", package: "fluent"),
                .product(name: "FluentPostgresDriver", package: "fluent-postgres-driver"),
                .product(name: "FOSMVVM", package: "FOSUtilities"),
                .product(name: "FOSMVVMVapor", package: "FOSUtilities"),
                "LegalDocViewModels",
            ]
        ),
        .target(
            name: "LegalDocViewModels",
            dependencies: [
                .product(name: "FOSMVVM", package: "FOSUtilities"),
                .product(name: "FOSFoundation", package: "FOSUtilities"),
            ]
        ),
        .testTarget(
            name: "LegalDocViewModelsTests",
            dependencies: [
                "LegalDocViewModels",
                .product(name: "FOSTesting", package: "FOSUtilities"),
            ],
            resources: [.process("Resources")]
        ),
    ]
)
'''
with open(os.path.join(WORKSPACE, "Package.swift"), "w") as f:
    f.write(package_swift)

# --- Existing Author DataModel (distractor + reference for patterns) ---
author_model = '''\
import FluentKit
import FOSFoundation
import FOSMVVM
import FOSMVVMVapor
import Foundation
import LegalDocViewModels

final class Author: DataModel, AuthorFields, Hashable, @unchecked Sendable {
    static let schema = "authors"

    @ID(key: .id) var id: ModelIdType?

    @Field(key: "first_name") var firstName: String
    @Field(key: "last_name") var lastName: String
    @Field(key: "bar_number") var barNumber: String

    let authorValidationMessages: AuthorFieldsMessages

    @Timestamp(key: "created_at", on: .create) var createdAt: Date?
    @Timestamp(key: "updated_at", on: .update) var updatedAt: Date?

    init() {
        self.authorValidationMessages = .init()
    }

    init(id: ModelIdType? = nil, firstName: String, lastName: String, barNumber: String) {
        self.authorValidationMessages = .init()
        self.id = id
        self.firstName = firstName
        self.lastName = lastName
        self.barNumber = barNumber
    }
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocServer/DataModels/Author.swift"), "w") as f:
    f.write(author_model)

# --- Existing Author migration ---
author_schema = '''\
import Fluent

extension Author {
    struct Initial: AsyncMigration {
        let name = "\\(Author.schema)-initial"

        func prepare(on database: any Database) async throws {
            try await database.schema(Author.schema)
                .id()
                .field("first_name", .string, .required)
                .field("last_name", .string, .required)
                .field("bar_number", .string, .required)
                .field("created_at", .datetime)
                .field("updated_at", .datetime)
                .unique(on: "bar_number")
                .create()
        }

        func revert(on database: any Database) async throws {
            try await database.schema(Author.schema).delete()
        }
    }
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocServer/Migrations/Author+Schema.swift"), "w") as f:
    f.write(author_schema)

# --- Existing Author seed ---
author_seed = '''\
import Fluent
import Vapor

extension Author {
    struct Seed: AsyncMigration {
        let name = "\\(Author.schema)-seed"

        func prepare(on database: any Database) async throws {
            guard try await Author.query(on: database).count() == 0 else { return }

            let items: [Author]
            switch Vapor.Environment.deployment {
            case .debug:
                items = try Author.defaultDebugItems
            case .test:
                items = try Author.defaultTestItems
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

private extension Author {
    static var defaultDebugItems: [Author] {
        get throws { [
            .init(firstName: "Jane", lastName: "Smith", barNumber: "CA-10001"),
            .init(firstName: "John", lastName: "Doe", barNumber: "CA-10002"),
        ] }
    }

    static var defaultTestItems: [Author] {
        get throws { [
            .init(firstName: "Test", lastName: "Lawyer", barNumber: "TEST-001"),
        ] }
    }
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocServer/Migrations/Author+Seed.swift"), "w") as f:
    f.write(author_seed)

# --- Existing Tag DataModel ---
tag_model = '''\
import FluentKit
import FOSFoundation
import FOSMVVM
import FOSMVVMVapor
import Foundation
import LegalDocViewModels

final class Tag: DataModel, TagFields, Hashable, @unchecked Sendable {
    static let schema = "tags"

    @ID(key: .id) var id: ModelIdType?

    @Field(key: "name") var name: String
    @Field(key: "color_hex") var colorHex: String

    let tagValidationMessages: TagFieldsMessages

    @Timestamp(key: "created_at", on: .create) var createdAt: Date?
    @Timestamp(key: "updated_at", on: .update) var updatedAt: Date?

    init() {
        self.tagValidationMessages = .init()
    }

    init(id: ModelIdType? = nil, name: String, colorHex: String) {
        self.tagValidationMessages = .init()
        self.id = id
        self.name = name
        self.colorHex = colorHex
    }
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocServer/DataModels/Tag.swift"), "w") as f:
    f.write(tag_model)

# --- Existing Tag migration ---
tag_schema = '''\
import Fluent

extension Tag {
    struct Initial: AsyncMigration {
        let name = "\\(Tag.schema)-initial"

        func prepare(on database: any Database) async throws {
            try await database.schema(Tag.schema)
                .id()
                .field("name", .string, .required)
                .field("color_hex", .string, .required)
                .field("created_at", .datetime)
                .field("updated_at", .datetime)
                .unique(on: "name")
                .create()
        }

        func revert(on database: any Database) async throws {
            try await database.schema(Tag.schema).delete()
        }
    }
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocServer/Migrations/Tag+Schema.swift"), "w") as f:
    f.write(tag_schema)

# --- Pre-existing AuthorFields protocol (distractor + required for Document to reference) ---
author_fields = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public protocol AuthorFields: ValidatableModel, Codable, Sendable {
    var id: ModelIdType? { get set }
    var firstName: String { get set }
    var lastName: String { get set }
    var barNumber: String { get set }

    var authorValidationMessages: AuthorFieldsMessages { get }
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocViewModels/FieldModels/AuthorFields.swift"), "w") as f:
    f.write(author_fields)

# --- Pre-existing TagFields protocol ---
tag_fields = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public protocol TagFields: ValidatableModel, Codable, Sendable {
    var id: ModelIdType? { get set }
    var name: String { get set }
    var colorHex: String { get set }

    var tagValidationMessages: TagFieldsMessages { get }
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocViewModels/FieldModels/TagFields.swift"), "w") as f:
    f.write(tag_fields)

# --- Pre-existing AuthorFieldsMessages struct ---
author_messages = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public struct AuthorFieldsMessages: FieldsMessages, Codable, Sendable {
    public init() {}
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocViewModels/FieldModels/AuthorFieldsMessages.swift"), "w") as f:
    f.write(author_messages)

# --- Pre-existing TagFieldsMessages struct ---
tag_messages = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public struct TagFieldsMessages: FieldsMessages, Codable, Sendable {
    public init() {}
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocViewModels/FieldModels/TagFieldsMessages.swift"), "w") as f:
    f.write(tag_messages)

# --- DocumentFields protocol (pre-created by fields-generator, as per skill dependency) ---
document_fields = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public protocol DocumentFields: ValidatableModel, Codable, Sendable {
    associatedtype Author: AuthorFields

    var id: ModelIdType? { get set }
    var title: String { get set }
    var content: String { get set }
    var caseNumber: String { get set }
    var author: Author { get set }

    var documentValidationMessages: DocumentFieldsMessages { get }
}

public extension DocumentFields {
    static var titleField: FieldDescriptor { .init(fieldId: "title") }
    static var contentField: FieldDescriptor { .init(fieldId: "content") }
    static var caseNumberField: FieldDescriptor { .init(fieldId: "caseNumber") }
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocViewModels/FieldModels/DocumentFields.swift"), "w") as f:
    f.write(document_fields)

# --- DocumentFieldsMessages struct ---
document_messages = '''\
import FOSFoundation
import FOSMVVM
import Foundation

public struct DocumentFieldsMessages: FieldsMessages, Codable, Sendable {
    public init() {}
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocViewModels/FieldModels/DocumentFieldsMessages.swift"), "w") as f:
    f.write(document_messages)

# --- Existing database.swift (agent must add migrations here) ---
database_swift = '''\
import Fluent
import FluentPostgresDriver
import Vapor

public func configureDatabases(_ app: Application) async throws {
    let dbId = DatabaseID.psql

    app.databases.use(
        .postgres(configuration: .init(
            hostname: Environment.get("DB_HOST") ?? "localhost",
            port: 5432,
            username: Environment.get("DB_USER") ?? "vapor",
            password: Environment.get("DB_PASSWORD") ?? "vapor",
            database: Environment.get("DB_NAME") ?? "legaldoc"
        )),
        as: dbId
    )

    // MARK: Migrations
    app.migrations.add(Author.Initial())
    app.migrations.add(Tag.Initial())

    // MARK: Seed
    if !app.environment.isRelease {
        app.migrations.add(Author.Seed(), to: dbId)
        app.migrations.add(Tag.Seed(), to: dbId)
    }
}
'''
with open(os.path.join(WORKSPACE, "Sources/LegalDocServer/database.swift"), "w") as f:
    f.write(database_swift)

# --- Distractor files ---

# Controller stubs
with open(os.path.join(WORKSPACE, "Sources/LegalDocServer/Controllers/AuthorController.swift"), "w") as f:
    f.write("// AuthorController stub\nimport Vapor\n\nstruct AuthorController: RouteCollection {\n    func boot(routes: RoutesBuilder) throws {}\n}\n")

with open(os.path.join(WORKSPACE, "Sources/LegalDocServer/Controllers/TagController.swift"), "w") as f:
    f.write("// TagController stub\nimport Vapor\n\nstruct TagController: RouteCollection {\n    func boot(routes: RoutesBuilder) throws {}\n}\n")

# Routes
with open(os.path.join(WORKSPACE, "Sources/LegalDocServer/Routes/routes.swift"), "w") as f:
    f.write("import Vapor\n\npublic func registerRoutes(_ app: Application) throws {\n    try app.register(collection: AuthorController())\n    try app.register(collection: TagController())\n}\n")

# Docs
with open(os.path.join(WORKSPACE, "docs/architecture_overview.md"), "w") as f:
    f.write("# LegalDoc Architecture\n\nThis platform manages legal documents with author attribution and categorical tagging.\n")

with open(os.path.join(WORKSPACE, "docs/database_schema.md"), "w") as f:
    f.write("# Database Schema Notes\n\n- authors: stores attorney records\n- tags: topic taxonomy (litigation, contract, IP, etc.)\n- documents: the main legal documents\n- documents <-> tags: many-to-many\n")

# Config
with open(os.path.join(WORKSPACE, "config/app.json"), "w") as f:
    f.write('{\n  "environment": "debug",\n  "db_pool_size": 10\n}\n')

# Scripts
with open(os.path.join(WORKSPACE, "scripts/reset_db.sh"), "w") as f:
    f.write("#!/bin/bash\n# Drop and recreate the database\necho 'Resetting database...'\n")

# Existing ViewModel distractor
with open(os.path.join(WORKSPACE, "Sources/LegalDocViewModels/ViewModels/AuthorViewModel.swift"), "w") as f:
    f.write("import FOSMVVM\nimport Foundation\n\npublic struct AuthorViewModel: ViewModel, Codable, Sendable {\n    public var id: ModelIdType?\n    public var displayName: String\n    public init(id: ModelIdType? = nil, displayName: String) {\n        self.id = id\n        self.displayName = displayName\n    }\n}\n")

# Test distractor
with open(os.path.join(WORKSPACE, "Tests/LegalDocViewModelsTests/FieldModels/AuthorFieldsTests.swift"), "w") as f:
    f.write('''\
import FOSFoundation
import FOSMVVM
import FOSTesting
import Foundation
import Testing
import LegalDocViewModels

@Suite("Author Fields")
struct AuthorFieldsTests: LocalizableTestCase {
    let locStore: LocalizationStore

    init() async throws {
        self.locStore = try Self.loadLocalizationStore(
            bundle: Bundle.module,
            resourceDirectoryName: ""
        )
    }
}
''')

with open(os.path.join(WORKSPACE, "Tests/LegalDocViewModelsTests/ViewModels/AuthorViewModelTests.swift"), "w") as f:
    f.write("import Testing\nimport LegalDocViewModels\n\n@Suite(\"Author ViewModel Tests\")\nstruct AuthorViewModelTests {}\n")

print("Workspace generated successfully.")
print("\nDirectory structure:")
for root, dirs_list, files in os.walk(WORKSPACE):
    level = root.replace(WORKSPACE, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')