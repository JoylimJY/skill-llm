import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ─────────────────────────────────────────────────────────────────────────────
# Helper: find the canonical locations for the two files.
# Per FOSMVVM naming rules, they MUST be named exactly:
#   TaskCardView.leaf       (fragment)
#   KanbanBoardView.leaf    (full-page)
# ─────────────────────────────────────────────────────────────────────────────

def find_leaf(filename):
    """Return the first match in the workspace, or None."""
    matches = list(workspace.rglob(filename))
    return matches[0] if matches else None

# ══════════════════════════════════════════════════════════════════
# SECTION 1 – FILE EXISTENCE & NAMING (proprietary alignment rule)
# ══════════════════════════════════════════════════════════════════

card_path = find_leaf("TaskCardView.leaf")
board_path = find_leaf("KanbanBoardView.leaf")

score += add_check(
    "TaskCardView.leaf exists (correct filename)",
    card_path is not None,
    f"Found at: {card_path}" if card_path else "File not found. Must be named TaskCardView.leaf (not TaskCard.leaf or TaskCardTemplate.leaf).",
)

score += add_check(
    "KanbanBoardView.leaf exists (correct filename)",
    board_path is not None,
    f"Found at: {board_path}" if board_path else "File not found. Must be named KanbanBoardView.leaf.",
)

card_content = ""
board_content = ""

try:
    if card_path:
        card_content = card_path.read_text()
except Exception as e:
    checks.append({"name": "Read TaskCardView.leaf", "passed": False, "detail": str(e)})

try:
    if board_path:
        board_content = board_path.read_text()
except Exception as e:
    checks.append({"name": "Read KanbanBoardView.leaf", "passed": False, "detail": str(e)})

# ══════════════════════════════════════════════════════════════════
# SECTION 2 – FRAGMENT RULES (TaskCardView.leaf)
# ══════════════════════════════════════════════════════════════════

# 2a. Fragment must NOT extend base layout
no_extend_in_fragment = '#extend("base")' not in card_content and "#extend('base')" not in card_content
score += add_check(
    "TaskCardView.leaf: NO #extend(\"base\") (fragment rule)",
    no_extend_in_fragment,
    "Fragment must NOT extend the base layout." if not no_extend_in_fragment else "Correct – no layout extension.",
)

# 2b. Fragment must NOT have #export blocks
no_export_in_fragment = '#export(' not in card_content
score += add_check(
    "TaskCardView.leaf: NO #export blocks (fragment rule)",
    no_export_in_fragment,
    "Fragment must not contain #export blocks." if not no_export_in_fragment else "Correct – no #export blocks.",
)

# 2c. Fragment should have a SINGLE root element (not multiple top-level block tags)
# Count top-level opening div/article/section tags that are not indented (rough heuristic)
lines = card_content.strip().splitlines()
top_level_open = [l for l in lines if re.match(r'^<(div|article|section|li|tr)\b', l.strip())]
# More precise: count root-level tags by checking lines with zero leading whitespace that open a tag
root_opens = [l for l in lines if re.match(r'^<[a-zA-Z]', l)]
root_closes = [l for l in lines if re.match(r'^</', l)]
# Heuristic: first line should be an opening tag, not a comment or whitespace
first_content_line = next((l.strip() for l in lines if l.strip() and not l.strip().startswith('#')), "")
single_root_heuristic = first_content_line.startswith("<") and not first_content_line.startswith("</")
score += add_check(
    "TaskCardView.leaf: starts with a single root HTML element",
    single_root_heuristic,
    f"First content line: '{first_content_line}'" if card_content else "File empty.",
)

# 2d. data-task-id attribute uses #(card.id)  — raw identifier
has_data_task_id = bool(re.search(r'data-task-id\s*=\s*"#\(card\.id\)"', card_content))
score += add_check(
    "TaskCardView.leaf: data-task-id=\"#(card.id)\" present",
    has_data_task_id,
    "Must include data-task-id=\"#(card.id)\" for JS identification." if not has_data_task_id else "Correct.",
    weight=1.5,
)

# 2e. data-status uses raw enum #(card.status) NOT #(card.statusDisplay)
has_data_status_raw = bool(re.search(r'data-status\s*=\s*"#\(card\.status\)"', card_content))
score += add_check(
    "TaskCardView.leaf: data-status uses raw enum #(card.status)",
    has_data_status_raw,
    "data-status must use raw enum #(card.status), not #(card.statusDisplay)." if not has_data_status_raw else "Correct.",
    weight=1.5,
)

# 2f. data-priority uses raw enum #(card.priority) NOT #(card.priorityDisplay)
has_data_priority_raw = bool(re.search(r'data-priority\s*=\s*"#\(card\.priority\)"', card_content))
score += add_check(
    "TaskCardView.leaf: data-priority uses raw enum #(card.priority)",
    has_data_priority_raw,
    "data-priority must use raw enum #(card.priority), not #(card.priorityDisplay)." if not has_data_priority_raw else "Correct.",
    weight=1.5,
)

# 2g. statusDisplay used for visible text (localized display in span/p)
has_status_display_text = bool(re.search(r'#\(card\.statusDisplay\)', card_content))
score += add_check(
    "TaskCardView.leaf: #(card.statusDisplay) used for visible text",
    has_status_display_text,
    "Should use #(card.statusDisplay) for visible status text (localized)." if not has_status_display_text else "Correct.",
)

# 2h. LocalizableDate rendered directly (no #date() format call)
# dueDateDisplay or createdDisplay should appear without a hardcoded #date() filter
has_localizable_date = bool(re.search(r'#\(card\.(dueDateDisplay|createdDisplay)\)', card_content))
score += add_check(
    "TaskCardView.leaf: LocalizableDate rendered via #(card.dueDateDisplay) or #(card.createdDisplay)",
    has_localizable_date,
    "LocalizableDate properties (dueDateDisplay/createdDisplay) should be rendered directly, not via #date()." if not has_localizable_date else "Correct.",
)

# 2i. messageCountDisplay used (pre-composed) — NOT manual concatenation of messageCount + messagesLabel
has_message_count_display = bool(re.search(r'#\(card\.messageCountDisplay\)', card_content))
bad_concat = bool(re.search(r'#\(card\.(messageCount|messagesLabel)\)', card_content))
score += add_check(
    "TaskCardView.leaf: messageCountDisplay used (no manual localized concatenation)",
    has_message_count_display and not bad_concat,
    "Must use #(card.messageCountDisplay) (pre-composed). Do not concatenate messageCount + messagesLabel." if not (has_message_count_display and not bad_concat) else "Correct.",
    weight=1.5,
)

# 2j. isOverdue conditional rendering
has_overdue_if = bool(re.search(r'#if\s*\(\s*card\.isOverdue\s*\)', card_content))
score += add_check(
    "TaskCardView.leaf: #if(card.isOverdue) conditional present",
    has_overdue_if,
    "Should include #if(card.isOverdue): ... #endif for overdue label." if not has_overdue_if else "Correct.",
)

# 2k. hasAssignee conditional (assignee vs unassigned)
has_assignee_if = bool(re.search(r'#if\s*\(\s*card\.hasAssignee\s*\)', card_content))
score += add_check(
    "TaskCardView.leaf: #if(card.hasAssignee) conditional for assignee/unassigned",
    has_assignee_if,
    "Should have #if(card.hasAssignee): ... #else: ... #endif." if not has_assignee_if else "Correct.",
)

# ══════════════════════════════════════════════════════════════════
# SECTION 3 – FULL-PAGE RULES (KanbanBoardView.leaf)
# ══════════════════════════════════════════════════════════════════

# 3a. Extends base layout
has_extend_base = bool(re.search(r'#extend\s*\(\s*["\']base["\']\s*\)', board_content))
score += add_check(
    "KanbanBoardView.leaf: #extend(\"base\") present",
    has_extend_base,
    "Full-page template must extend base layout with #extend(\"base\"):" if not has_extend_base else "Correct.",
    weight=1.5,
)

# 3b. Exports title block
has_export_title = bool(re.search(r'#export\s*\(\s*["\']title["\']\s*\)', board_content))
score += add_check(
    "KanbanBoardView.leaf: #export(\"title\") block present",
    has_export_title,
    "Must export a title block." if not has_export_title else "Correct.",
)

# 3c. Exports content block
has_export_content = bool(re.search(r'#export\s*\(\s*["\']content["\']\s*\)', board_content))
score += add_check(
    "KanbanBoardView.leaf: #export(\"content\") block present",
    has_export_content,
    "Must export a content block." if not has_export_content else "Correct.",
    weight=1.5,
)

# 3d. #endextend present
has_endextend = '#endextend' in board_content
score += add_check(
    "KanbanBoardView.leaf: #endextend present",
    has_endextend,
    "Must close the layout extension with #endextend." if not has_endextend else "Correct.",
)

# 3e. Loops over viewModel.columns
has_for_columns = bool(re.search(r'#for\s*\(\s*\w+\s+in\s+viewModel\.columns\s*\)', board_content))
score += add_check(
    "KanbanBoardView.leaf: #for loop over viewModel.columns",
    has_for_columns,
    "Must iterate over viewModel.columns with #for." if not has_for_columns else "Correct.",
    weight=1.5,
)

# 3f. Columns have data-status attribute using column's raw status enum
has_col_data_status = bool(re.search(r'data-status\s*=\s*"#\(\w+\.status\)"', board_content))
score += add_check(
    "KanbanBoardView.leaf: column element has data-status=\"#(column.status)\" (raw enum)",
    has_col_data_status,
    "Each column div must have data-status with raw enum value from the column ViewModel." if not has_col_data_status else "Correct.",
    weight=1.5,
)

# 3g. Embeds TaskCardView fragment (not reimplementing inline)
# Should reference "Kanban/TaskCardView" via #extend
has_card_fragment_ref = bool(re.search(r'#extend\s*\(\s*["\']Kanban/TaskCardView["\']\s*\)', board_content))
score += add_check(
    "KanbanBoardView.leaf: references Kanban/TaskCardView fragment via #extend",
    has_card_fragment_ref,
    "Full-page template must embed the card fragment with #extend(\"Kanban/TaskCardView\") rather than inlining card HTML." if not has_card_fragment_ref else "Correct.",
    weight=2.0,
)

# 3h. Empty board state: uses viewModel.emptyBoardMessage (not hardcoded text)
has_empty_board_msg = bool(re.search(r'#\(viewModel\.emptyBoardMessage\)', board_content))
score += add_check(
    "KanbanBoardView.leaf: #(viewModel.emptyBoardMessage) for empty state",
    has_empty_board_msg,
    "Must use #(viewModel.emptyBoardMessage) for empty state, not hardcoded text." if not has_empty_board_msg else "Correct.",
)

# 3i. viewModel.boardTitle rendered in header (localized, not pageTitle used as h1 etc.)
has_board_title = bool(re.search(r'#\(viewModel\.boardTitle\)', board_content))
score += add_check(
    "KanbanBoardView.leaf: #(viewModel.boardTitle) used for visible heading",
    has_board_title,
    "Should render #(viewModel.boardTitle) as the main heading." if not has_board_title else "Correct.",
)

# 3j. pageTitle exported in title block (not boardTitle)
# The title export should contain viewModel.pageTitle
title_export_match = re.search(
    r'#export\s*\(\s*["\']title["\']\s*\)\s*:?(.*?)#endexport',
    board_content, re.DOTALL
)
title_export_has_page_title = False
if title_export_match:
    title_export_has_page_title = 'viewModel.pageTitle' in title_export_match.group(1)
score += add_check(
    "KanbanBoardView.leaf: #export(\"title\") contains #(viewModel.pageTitle)",
    title_export_has_page_title,
    "The title export block should render #(viewModel.pageTitle)." if not title_export_has_page_title else "Correct.",
)

# ══════════════════════════════════════════════════════════════════
# SECTION 4 – FILE LOCATION CHECK (must be inside correct Views dir)
# ══════════════════════════════════════════════════════════════════

kanban_views_dir = workspace / "Sources/TaskFlowWebApp/Resources/Views/Kanban"

if card_path:
    card_in_kanban = str(card_path).startswith(str(kanban_views_dir))
    score += add_check(
        "TaskCardView.leaf: placed in Sources/TaskFlowWebApp/Resources/Views/Kanban/",
        card_in_kanban,
        f"Actual location: {card_path}. Expected: {kanban_views_dir}/" if not card_in_kanban else "Correct location.",
    )
else:
    checks.append({"name": "TaskCardView.leaf: placed in Kanban/ directory", "passed": False, "detail": "File missing."})

if board_path:
    board_in_kanban = str(board_path).startswith(str(kanban_views_dir))
    score += add_check(
        "KanbanBoardView.leaf: placed in Sources/TaskFlowWebApp/Resources/Views/Kanban/",
        board_in_kanban,
        f"Actual location: {board_path}. Expected: {kanban_views_dir}/" if not board_in_kanban else "Correct location.",
    )
else:
    checks.append({"name": "KanbanBoardView.leaf: placed in Kanban/ directory", "passed": False, "detail": "File missing."})

# ══════════════════════════════════════════════════════════════════
# SCORING
# ══════════════════════════════════════════════════════════════════

max_score = sum([
    1,    # 1a file exists card
    1,    # 1b file exists board
    1,    # 2a no extend in fragment
    1,    # 2b no export in fragment
    1,    # 2c single root
    1.5,  # 2d data-task-id
    1.5,  # 2e data-status raw
    1.5,  # 2f data-priority raw
    1,    # 2g statusDisplay for text
    1,    # 2h LocalizableDate direct
    1.5,  # 2i messageCountDisplay
    1,    # 2j isOverdue if
    1,    # 2k hasAssignee if
    1.5,  # 3a extend base
    1,    # 3b export title
    1.5,  # 3c export content
    1,    # 3d endextend
    1.5,  # 3e for columns
    1.5,  # 3f col data-status
    2.0,  # 3g card fragment ref
    1,    # 3h emptyBoardMessage
    1,    # 3i boardTitle
    1,    # 3j pageTitle in title export
    1,    # 4a card location
    1,    # 4b board location
])

normalized = round(score / max_score, 4)
passed = normalized >= 0.75

result = {
    "passed": passed,
    "score": normalized,
    "checks": checks
}

print(json.dumps(result, indent=2))