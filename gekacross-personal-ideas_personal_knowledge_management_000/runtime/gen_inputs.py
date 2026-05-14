import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create deeply nested distractor directory structure
dirs = [
    "knowledge/personal",
    "knowledge/work",
    "knowledge/reading",
    "knowledge/projects/active",
    "knowledge/projects/archive",
    "notes/2023",
    "notes/2024/q1",
    "notes/2024/q2",
    "notes/2024/q3",
    "notes/2024/q4",
    "journal/daily",
    "journal/weekly",
    "resources/articles",
    "resources/books",
    "templates",
    "inbox",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

(workspace / "knowledge/work/projects.md").write_text(
    "# Work Projects\n\n- Q4 launch\n- Partnership negotiation\n- Hiring plan\n", encoding="utf-8"
)

(workspace / "knowledge/work/contacts.md").write_text(
    "# Contacts\n\n- Ivan Petrov: investor\n- Maria S.: potential cofounder\n", encoding="utf-8"
)

(workspace / "knowledge/reading/books.md").write_text(
    "# Reading List\n\n- Zero to One\n- The Mom Test\n- Antifragile\n", encoding="utf-8"
)

(workspace / "knowledge/projects/active/saas_dashboard.md").write_text(
    "# SaaS Dashboard\n\nStatus: in progress\nStack: React, FastAPI\n", encoding="utf-8"
)

(workspace / "knowledge/projects/archive/old_app.md").write_text(
    "# Old App (archived)\n\nShut down in 2022. Lessons learned: pricing was wrong.\n", encoding="utf-8"
)

(workspace / "notes/2024/q3/meeting_notes.md").write_text(
    "# Meeting Notes Q3\n\nDiscussed new features with team. Decided to postpone mobile app.\n", encoding="utf-8"
)

(workspace / "notes/2024/q4/retrospective.md").write_text(
    "# Q4 Retrospective\n\nRevenue grew 12%. Churn still high. Need to improve onboarding.\n", encoding="utf-8"
)

(workspace / "journal/daily/2024-11-15.md").write_text(
    "Feeling productive. Shipped new feature. Need to think about pricing model.\n", encoding="utf-8"
)

(workspace / "journal/weekly/week_46.md").write_text(
    "# Week 46\n\nFocused on product. Had 3 sales calls. One promising lead.\n", encoding="utf-8"
)

(workspace / "resources/articles/saved.md").write_text(
    "# Saved Articles\n\n- https://example.com/pricing-strategies\n- https://example.com/no-code-tools\n", encoding="utf-8"
)

(workspace / "resources/books/notes.md").write_text(
    "# Book Notes\n\nThe Mom Test: talk about their life, not your idea. Ask about past, not future.\n", encoding="utf-8"
)

(workspace / "templates/weekly_review.md").write_text(
    "# Weekly Review Template\n\n## What went well\n## What didn't\n## Next week goals\n", encoding="utf-8"
)

(workspace / "inbox/random_links.md").write_text(
    "https://news.ycombinator.com/item?id=12345\nhttps://producthunt.com/posts/example\n", encoding="utf-8"
)

# --- The CORE file the agent must READ and MODIFY ---
# This is the existing ideas.md with 3 pre-existing ideas (some connected to what user will input)

ideas_content = """# Идеи

## [2024-09-10] Телеграм-бот для привычек
**Теги:** #продукт #бизнес
**Статус:** raw
Сделать телеграм-бота, который помогает трекать ежедневные привычки. Пользователь отмечает выполнение, бот присылает напоминания и статистику.

## [2024-10-02] Подписка на кураторскую рассылку о стартапах
**Теги:** #контент #бизнес
**Статус:** exploring
Еженедельный дайджест: отбираю 5 лучших материалов о стартапах, монетизация через платную подписку. Уже есть 30 подписчиков в тестовом режиме.

## [2024-10-25] Ноу-код конструктор лендингов для фрилансеров
**Теги:** #продукт
**Статус:** raw
Простой инструмент для фрилансеров — собрать лендинг за 15 минут без кода. Фокус на портфолио и форме заявки.
"""

(workspace / "knowledge/personal/ideas.md").write_text(ideas_content, encoding="utf-8")

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")