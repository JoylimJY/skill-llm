import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "Sources/KanbanModels/ViewModels",
    "Sources/KanbanModels/Resources",
    "Sources/KanbanApp/Views",
    "Sources/KanbanApp/Controllers",
    "Sources/KanbanApp/Networking",
    "Tests/KanbanModelsTests/Localization",
    "Tests/KanbanModelsTests/TestYAML",
    "Tests/KanbanModelsTests/Snapshots",
    "Tests/KanbanAppTests/UI",
    "Tests/KanbanAppTests/Integration",
    "docs",
    "scripts",
    "config",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── existing source ViewModels (context for the agent) ────────────────────────
board_vm = '''\
// BoardViewModel.swift
import FOSMVVM
import FOSFoundation

@ViewModel
public struct BoardViewModel: RequestableViewModel {
    @LocalizedString public var boardTitle
    @LocalizedString public var boardDescription
    public let columns: [ColumnViewModel]

    public var vmId: ViewModelId = .init()

    public static func stub() -> Self {
        .init(columns: [.stub(), .stub()])
    }
}
'''

column_vm = '''\
// ColumnViewModel.swift
import FOSMVVM
import FOSFoundation

@ViewModel
public struct ColumnViewModel: ViewModel {
    @LocalizedString public var columnName
    public let cards: [CardViewModel]

    public var vmId: ViewModelId = .init()

    public static func stub() -> Self {
        .init(cards: [.stub(), .stub()])
    }
}
'''

card_vm = '''\
// CardViewModel.swift
import FOSMVVM
import FOSFoundation

@ViewModel
public struct CardViewModel: ViewModel {
    @LocalizedString public var cardTitle
    @LocalizedSubs public var dueLabel

    public var vmId: ViewModelId = .init()

    public static func stub() -> Self {
        .init(subs: ["days": "3"])
    }
}
'''

with open(os.path.join(WORKSPACE, "Sources/KanbanModels/ViewModels/BoardViewModel.swift"), "w") as f:
    f.write(board_vm)

with open(os.path.join(WORKSPACE, "Sources/KanbanModels/ViewModels/ColumnViewModel.swift"), "w") as f:
    f.write(column_vm)

with open(os.path.join(WORKSPACE, "Sources/KanbanModels/ViewModels/CardViewModel.swift"), "w") as f:
    f.write(card_vm)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "Sources/KanbanApp/Views/BoardView.swift": '''\
import SwiftUI
struct BoardView: View {
    var body: some View { Text("Board") }
}
''',
    "Sources/KanbanApp/Controllers/BoardController.swift": '''\
import Foundation
class BoardController {
    func loadBoard() {}
}
''',
    "Sources/KanbanApp/Networking/APIClient.swift": '''\
import Foundation
struct APIClient {
    func fetch(url: URL) async throws -> Data { Data() }
}
''',
    "Tests/KanbanAppTests/UI/BoardViewTests.swift": '''\
import XCTest
class BoardViewTests: XCTestCase {
    func testLayout() {}
}
''',
    "Tests/KanbanAppTests/Integration/SyncTests.swift": '''\
import XCTest
class SyncTests: XCTestCase {
    func testSync() {}
}
''',
    "Tests/KanbanModelsTests/Snapshots/BoardSnapshot.json": '{"version": 1, "fields": ["boardTitle", "boardDescription", "columns"]}',
    "docs/architecture.md": "# Architecture\n\nSee source files for details.\n",
    "docs/api.md": "# API Reference\n\nEndpoints described here.\n",
    "scripts/generate_mocks.sh": "#!/bin/bash\necho 'mock generation'\n",
    "config/ci.yml": "name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
    "Sources/KanbanModels/Resources/en.lproj": None,  # directory marker
}

for path, content in distractors.items():
    full = os.path.join(WORKSPACE, path)
    if content is None:
        os.makedirs(full, exist_ok=True)
    else:
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(content)

# ── existing (incomplete) YAML to show the pattern but leave work to do ───────
# Provide only 'en' for BoardViewModel to hint structure; agent must complete all locales
# and add ColumnViewModel, CardViewModel (with substitution syntax)
incomplete_yaml = '''\
# Incomplete - DO NOT USE AS-IS
en:
  BoardViewModel:
    boardTitle: "My Board"
    # boardDescription is missing
'''

with open(os.path.join(WORKSPACE, "Tests/KanbanModelsTests/TestYAML/BoardViewModel.yml.incomplete"), "w") as f:
    f.write(incomplete_yaml)

# ── existing passing test for an unrelated ViewModel (shows the pattern) ─────
existing_test = '''\
// UserViewModelTests.swift
import FOSFoundation
@testable import FOSMVVM
import FOSTesting
import Foundation
import Testing

@Suite("User ViewModel Tests")
struct UserViewModelTests: LocalizableTestCase {
    @Test func userViewModel() throws {
        try expectFullViewModelTests(UserViewModel.self)
    }

    let locStore: LocalizationStore
    init() throws {
        self.locStore = try Self.loadLocalizationStore(
            bundle: Bundle.module,
            resourceDirectoryName: "TestYAML"
        )
    }
}
'''

with open(os.path.join(WORKSPACE, "Tests/KanbanModelsTests/Localization/UserViewModelTests.swift"), "w") as f:
    f.write(existing_test)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(WORKSPACE):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(" ", fpath.replace(WORKSPACE + "/", ""))