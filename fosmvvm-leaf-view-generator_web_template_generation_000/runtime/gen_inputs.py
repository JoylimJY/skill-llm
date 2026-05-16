import os
import random

random.seed(42)

workspace = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "Sources/TaskFlowViewModels/ViewModels/Kanban",
    "Sources/TaskFlowViewModels/ViewModels/Dashboard",
    "Sources/TaskFlowViewModels/ViewModels/Settings",
    "Sources/TaskFlowWebApp/Resources/Views/Dashboard",
    "Sources/TaskFlowWebApp/Resources/Views/Settings",
    "Sources/TaskFlowWebApp/Resources/Views/Shared",
    "Sources/TaskFlowWebApp/Public/styles",
    "Sources/TaskFlowWebApp/Public/scripts",
    "Sources/TaskFlowServer/Controllers",
    "Sources/TaskFlowServer/Routes",
    "docs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────

# 1. An EXISTING (but unrelated) full-page view  – Dashboard
with open(os.path.join(workspace, "Sources/TaskFlowWebApp/Resources/Views/Dashboard/DashboardView.leaf"), "w") as f:
    f.write('''\
#extend("base"):

#export("title"):
#(viewModel.pageTitle)
#endexport

#export("content"):
<div class="dashboard-container">
    <header class="dashboard-header">
        <h1>#(viewModel.title)</h1>
    </header>
    <main class="dashboard-content">
        #for(summary in viewModel.summaries):
        #extend("Dashboard/SummaryCardView")
        #endfor
    </main>
</div>
#endexport

#endextend
''')

# 2. An EXISTING fragment (unrelated) – SummaryCardView
with open(os.path.join(workspace, "Sources/TaskFlowWebApp/Resources/Views/Dashboard/SummaryCardView.leaf"), "w") as f:
    f.write('''\
<div class="summary-card"
     data-summary-id="#(card.id)"
     data-type="#(card.type)">
    <h3>#(card.title)</h3>
    <p>#(card.valueDisplay)</p>
</div>
''')

# 3. base.leaf (already exists)
with open(os.path.join(workspace, "Sources/TaskFlowWebApp/Resources/Views/base.leaf"), "w") as f:
    f.write('''\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>#import("title")</title>
    <link rel="stylesheet" href="/styles/main.css">
</head>
<body>
    <header class="site-header">
        #import("header")
    </header>
    <main class="site-content">
        #import("content")
    </main>
    <footer class="site-footer">
        #import("footer")
    </footer>
    <script src="/scripts/main.js"></script>
</body>
</html>
''')

# 4. Settings full-page view (distractor)
with open(os.path.join(workspace, "Sources/TaskFlowWebApp/Resources/Views/Settings/SettingsView.leaf"), "w") as f:
    f.write('''\
#extend("base"):
#export("title"):
#(viewModel.pageTitle)
#endexport
#export("content"):
<div class="settings-container">
    <h1>#(viewModel.title)</h1>
</div>
#endexport
#endextend
''')

# ── THE KEY ViewModels the agent must analyse ───────────────────────────────

# TaskCardViewModel (fragment target)
with open(os.path.join(workspace, "Sources/TaskFlowViewModels/ViewModels/Kanban/TaskCardViewModel.swift"), "w") as f:
    f.write('''\
import FOSMVVM
import Foundation

/// ViewModel for a single Kanban task card (fragment / HTML-over-the-wire).
@ViewModel
public struct TaskCardViewModel: Codable {

    // MARK: - Identity
    public let id: ModelIdType
    public var vmId: ViewModelId

    // MARK: - State (raw enums → data-* attributes, DO NOT use display names for data attrs)
    public let status: TaskStatus          // raw: "todo" | "in_progress" | "done"
    public let priority: TaskPriority      // raw: "low" | "medium" | "high"

    // MARK: - Display (localized, use these for visible text only)
    public let statusDisplay: LocalizableString   // e.g. "In Progress"
    public let priorityDisplay: LocalizableString // e.g. "High Priority"
    public let title: LocalizableString
    public let descriptionPreview: LocalizableString
    public let assigneeName: LocalizableString
    public let assigneeInitial: LocalizableString
    public let dueDateDisplay: LocalizableDate    // locale-aware
    public let createdDisplay: LocalizableDate

    // MARK: - Flags (stored, Codable-safe)
    public let isOverdue: Bool
    public let overdueLabel: LocalizableString    // e.g. "Overdue!"
    public let hasAssignee: Bool
    public let unassignedLabel: LocalizableString

    // MARK: - Message count (pre-composed by ViewModel; do NOT concatenate in template)
    public let messageCountDisplay: LocalizableString  // e.g. "3 messages"

    public init(
        id: ModelIdType,
        status: TaskStatus,
        priority: TaskPriority,
        statusDisplay: LocalizableString,
        priorityDisplay: LocalizableString,
        title: LocalizableString,
        descriptionPreview: LocalizableString,
        assigneeName: LocalizableString,
        assigneeInitial: LocalizableString,
        dueDateDisplay: LocalizableDate,
        createdDisplay: LocalizableDate,
        isOverdue: Bool,
        overdueLabel: LocalizableString,
        hasAssignee: Bool,
        unassignedLabel: LocalizableString,
        messageCountDisplay: LocalizableString
    ) {
        self.id = id
        self.vmId = .init(id: id)        // data-based identity
        self.status = status
        self.priority = priority
        self.statusDisplay = statusDisplay
        self.priorityDisplay = priorityDisplay
        self.title = title
        self.descriptionPreview = descriptionPreview
        self.assigneeName = assigneeName
        self.assigneeInitial = assigneeInitial
        self.dueDateDisplay = dueDateDisplay
        self.createdDisplay = createdDisplay
        self.isOverdue = isOverdue
        self.overdueLabel = overdueLabel
        self.hasAssignee = hasAssignee
        self.unassignedLabel = unassignedLabel
        self.messageCountDisplay = messageCountDisplay
    }
}
''')

# KanbanBoardViewModel (full-page target)
with open(os.path.join(workspace, "Sources/TaskFlowViewModels/ViewModels/Kanban/KanbanBoardViewModel.swift"), "w") as f:
    f.write('''\
import FOSMVVM
import Foundation

/// ViewModel for the full Kanban board page.
@ViewModel
public struct KanbanBoardViewModel: Codable {

    // MARK: - Identity
    public var vmId: ViewModelId = .init(type: Self.self)

    // MARK: - Page metadata
    public let pageTitle: LocalizableString
    public let boardTitle: LocalizableString

    // MARK: - Columns (each column holds task cards)
    public let columns: [KanbanColumnViewModel]

    // MARK: - Empty state
    public let emptyBoardMessage: LocalizableString

    // MARK: - Stored derived flag (Codable-safe)
    public let hasColumns: Bool

    public init(
        pageTitle: LocalizableString,
        boardTitle: LocalizableString,
        columns: [KanbanColumnViewModel],
        emptyBoardMessage: LocalizableString
    ) {
        self.pageTitle = pageTitle
        self.boardTitle = boardTitle
        self.columns = columns
        self.emptyBoardMessage = emptyBoardMessage
        self.hasColumns = !columns.isEmpty
    }
}

/// ViewModel for a single column within the board.
@ViewModel
public struct KanbanColumnViewModel: Codable {

    public var vmId: ViewModelId = .init(type: Self.self)

    public let status: TaskStatus           // raw enum → data-status attribute
    public let columnTitle: LocalizableString
    public let taskCount: Int               // stored, not computed
    public let emptyColumnMessage: LocalizableString
    public let cards: [TaskCardViewModel]

    public init(
        status: TaskStatus,
        columnTitle: LocalizableString,
        taskCount: Int,
        emptyColumnMessage: LocalizableString,
        cards: [TaskCardViewModel]
    ) {
        self.status = status
        self.columnTitle = columnTitle
        self.taskCount = taskCount
        self.emptyColumnMessage = emptyColumnMessage
        self.cards = cards
    }
}
''')

# ── Additional distractor Swift files ──────────────────────────────────────

with open(os.path.join(workspace, "Sources/TaskFlowViewModels/ViewModels/Dashboard/DashboardViewModel.swift"), "w") as f:
    f.write('''\
import FOSMVVM
@ViewModel
public struct DashboardViewModel: Codable {
    public var vmId: ViewModelId = .init(type: Self.self)
    public let title: LocalizableString
    public let pageTitle: LocalizableString
    public let summaries: [SummaryCardViewModel]
}
@ViewModel
public struct SummaryCardViewModel: Codable {
    public let id: ModelIdType
    public var vmId: ViewModelId
    public let type: String
    public let title: LocalizableString
    public let valueDisplay: LocalizableString
    public init(id: ModelIdType, type: String, title: LocalizableString, valueDisplay: LocalizableString) {
        self.id = id
        self.vmId = .init(id: id)
        self.type = type
        self.title = title
        self.valueDisplay = valueDisplay
    }
}
''')

with open(os.path.join(workspace, "Sources/TaskFlowViewModels/ViewModels/Settings/SettingsViewModel.swift"), "w") as f:
    f.write('''\
import FOSMVVM
@ViewModel
public struct SettingsViewModel: Codable {
    public var vmId: ViewModelId = .init(type: Self.self)
    public let title: LocalizableString
    public let pageTitle: LocalizableString
}
''')

# Enum definitions (distractor / context)
with open(os.path.join(workspace, "Sources/TaskFlowViewModels/ViewModels/Kanban/TaskEnums.swift"), "w") as f:
    f.write('''\
import Foundation

public enum TaskStatus: String, Codable, CaseIterable {
    case todo         = "todo"
    case inProgress   = "in_progress"
    case done         = "done"
}

public enum TaskPriority: String, Codable, CaseIterable {
    case low    = "low"
    case medium = "medium"
    case high   = "high"
}
''')

# Server route file (distractor)
with open(os.path.join(workspace, "Sources/TaskFlowServer/Routes/KanbanRoutes.swift"), "w") as f:
    f.write('''\
import Vapor
import FOSMVVM

func registerKanbanRoutes(_ app: Application) throws {
    // GET /kanban  -> full page
    app.get("kanban") { req async throws -> View in
        let serverRequest = KanbanBoardViewModelRequest()
        guard let response = try await serverRequest.processRequest(baseURL: app.serverBaseURL) else {
            throw Abort(.internalServerError)
        }
        return try await req.view.render("Kanban/KanbanBoardView", ["viewModel": response])
    }

    // POST /move-task -> fragment (HTML-over-the-wire)
    app.post("move-task") { req async throws -> Response in
        let body = try req.content.decode(MoveTaskRequest.RequestBody.self)
        let serverRequest = MoveTaskRequest(requestBody: body)
        guard let response = try await serverRequest.processRequest(baseURL: app.serverBaseURL) else {
            throw Abort(.internalServerError)
        }
        return try await req.view.render(
            "Kanban/TaskCardView",
            ["card": response.viewModel]
        ).encodeResponse(for: req)
    }
}
''')

with open(os.path.join(workspace, "Sources/TaskFlowServer/Controllers/KanbanController.swift"), "w") as f:
    f.write('''\
import Vapor
import FOSMVVM

struct KanbanController {
    func moveTask(req: Request) async throws -> Response {
        // Controller logic here
        fatalError("not implemented")
    }
}
''')

# CSS / JS distractors
with open(os.path.join(workspace, "Sources/TaskFlowWebApp/Public/styles/main.css"), "w") as f:
    f.write('''\
.kanban-board { display: flex; gap: 1rem; }
.task-card { border: 1px solid #ccc; border-radius: 8px; padding: 1rem; }
.column-header { font-weight: bold; margin-bottom: 0.5rem; }
''')

with open(os.path.join(workspace, "Sources/TaskFlowWebApp/Public/scripts/main.js"), "w") as f:
    f.write('''\
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".task-card").forEach(card => {
        card.addEventListener("dragstart", e => {
            e.dataTransfer.setData("taskId", card.dataset.taskId);
            e.dataTransfer.setData("currentStatus", card.dataset.status);
        });
    });

    document.querySelectorAll(".kanban-column").forEach(col => {
        col.addEventListener("drop", async e => {
            const taskId = e.dataTransfer.getData("taskId");
            const newStatus = col.dataset.status;
            const resp = await fetch("/move-task", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ taskId, newStatus })
            });
            const html = await resp.text();
            document.querySelector(`[data-task-id="${taskId}"]`).outerHTML = html;
        });
    });
});
''')

# docs distractor
with open(os.path.join(workspace, "docs/architecture-notes.md"), "w") as f:
    f.write('''\
# TaskFlow Architecture Notes

- Swift/Vapor backend
- Leaf templates for web views
- ViewModels shared between web and SwiftUI native clients
- FOSMVVM framework used throughout
''')

with open(os.path.join(workspace, "docs/deployment.md"), "w") as f:
    f.write('''\
# Deployment

Standard Vapor deployment. See Vapor docs for configuration.
''')

# Package.swift distractor
with open(os.path.join(workspace, "Package.swift"), "w") as f:
    f.write('''\
// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "TaskFlow",
    platforms: [.macOS(.v14)],
    products: [
        .library(name: "TaskFlowViewModels", targets: ["TaskFlowViewModels"]),
        .executable(name: "TaskFlowWebApp", targets: ["TaskFlowWebApp"]),
        .executable(name: "TaskFlowServer", targets: ["TaskFlowServer"]),
    ],
    dependencies: [
        .package(url: "https://github.com/foscomputerservices/FOSUtilities", branch: "main"),
        .package(url: "https://github.com/vapor/vapor", from: "4.0.0"),
        .package(url: "https://github.com/vapor/leaf", from: "4.0.0"),
    ],
    targets: [
        .target(name: "TaskFlowViewModels", dependencies: [
            .product(name: "FOSMVVM", package: "FOSUtilities"),
        ]),
        .target(name: "TaskFlowWebApp", dependencies: [
            "TaskFlowViewModels",
            .product(name: "Vapor", package: "vapor"),
            .product(name: "Leaf", package: "leaf"),
            .product(name: "FOSMVVMVapor", package: "FOSUtilities"),
        ]),
        .target(name: "TaskFlowServer", dependencies: [
            "TaskFlowViewModels",
            .product(name: "Vapor", package: "vapor"),
        ]),
    ]
)
''')

print("Workspace generated successfully.")
print("Key files:")
print("  - Sources/TaskFlowViewModels/ViewModels/Kanban/TaskCardViewModel.swift")
print("  - Sources/TaskFlowViewModels/ViewModels/Kanban/KanbanBoardViewModel.swift")
print("  - Sources/TaskFlowWebApp/Resources/Views/base.leaf  (base layout, DO NOT modify)")
print("Agent must create:")
print("  - TaskCardView.leaf  (fragment)")
print("  - KanbanBoardView.leaf  (full page)")