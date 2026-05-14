#!/usr/bin/env bash
set -e

# Make all scripts executable
chmod +x /workspace/skills/habitchat/scripts/habit_tracker.py
chmod +x /workspace/skills/habitchat/scripts/reminder.py
chmod +x /workspace/skills/habitchat/scripts/coach.py

# Write the SKILL.md into the skill directory so the agent can read it
cat > /workspace/skills/habitchat/SKILL.md << 'SKILLEOF'
---
name: habitchat
version: 1.0.0
description: Personal habit coach that tracks daily habits, streaks, and provides AI-powered coaching.
author: Dinesh18S
---

# HabitChat - Your Personal Habit Coach

## Data Storage

All habit data is stored in `~/.habitchat/` as JSON files. Use the Python scripts in this skill's `scripts/` directory for all data operations.

## First-Time Setup

On first interaction, if `~/.habitchat/` does not exist:
1. Run `python3 {baseDir}/scripts/habit_tracker.py init`

## Core Commands

### Adding a Habit

```bash
python3 {baseDir}/scripts/habit_tracker.py add --name "<habit_name>" --time "<HH:MM>" --days "mon,tue,wed,thu,fri,sat,sun"
```

- `--name`: Natural name like "Morning run" or "Read for 30 minutes"
- `--time`: Reminder time in 24h format. Parse natural language: "9am" -> "09:00", "evening" -> "19:00", "after lunch" -> "13:00"
- `--days`: Comma-separated days. Default is all days. Parse: "weekdays" -> "mon,tue,wed,thu,fri", "weekends" -> "sat,sun"

### Logging a Habit (Done / Skip)

```bash
# Mark as done
python3 {baseDir}/scripts/habit_tracker.py log --habit "<name_or_id>" --status done

# Mark as skipped
python3 {baseDir}/scripts/habit_tracker.py log --habit "<name_or_id>" --status skip

# Mark as missed
python3 {baseDir}/scripts/habit_tracker.py log --habit "<name_or_id>" --status miss
```

### Viewing Habits

```bash
python3 {baseDir}/scripts/habit_tracker.py list
```

### Viewing Stats & Streaks

```bash
python3 {baseDir}/scripts/habit_tracker.py stats --habit "<name_or_id>" --days 30
```

### Overview / Dashboard

```bash
python3 {baseDir}/scripts/habit_tracker.py overview
```

### Editing a Habit

```bash
python3 {baseDir}/scripts/habit_tracker.py edit --habit "<name_or_id>" --name "<new_name>" --time "<new_time>" --days "<new_days>"
```

### Pausing / Resuming

```bash
python3 {baseDir}/scripts/habit_tracker.py pause --habit "<name_or_id>"
python3 {baseDir}/scripts/habit_tracker.py resume --habit "<name_or_id>"
```

### Deleting a Habit

```bash
python3 {baseDir}/scripts/habit_tracker.py delete --habit "<name_or_id>"
```

## Reminders

```bash
# Set up system reminders
python3 {baseDir}/scripts/reminder.py setup --habit "<name_or_id>"

# List active reminders
python3 {baseDir}/scripts/reminder.py list

# Disable reminders
python3 {baseDir}/scripts/reminder.py disable --habit "<name_or_id>"
```

## AI Coaching

```bash
# Get coaching insights
python3 {baseDir}/scripts/coach.py insights --user-data ~/.habitchat/

# Get motivational message for a specific habit
python3 {baseDir}/scripts/coach.py motivate --habit "<name_or_id>"

# Analyze patterns and suggest improvements
python3 {baseDir}/scripts/coach.py analyze --days 30
```

## Natural Language Understanding

Parse these common phrases:
- "weekdays" -> "mon,tue,wed,thu,fri"
- "weekends" -> "sat,sun"
- "9am" -> "09:00"
- "evening" -> "19:00"
- "after lunch" -> "13:00"
- "6:30am" -> "06:30"

## Integration Notes

- All times are stored in UTC internally but displayed in the user's local timezone
- The config.json stores the user's timezone (auto-detected or manually set)
- Habit IDs are short UUIDs (first 8 chars) for easy reference
- The scripts are self-contained Python with no external dependencies beyond the standard library
SKILLEOF

echo "Setup complete. Scripts are executable."
echo "Skill base dir: /workspace/skills/habitchat"
ls /workspace/skills/habitchat/scripts/