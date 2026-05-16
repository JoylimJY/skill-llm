#!/bin/bash
set -e

# Ensure the fitness memory directory exists (as per SKILL.md: ~/fitness/memory.md)
mkdir -p ~/fitness

# Make sure workspace files are readable
chmod -R 644 /workspace/raw_exports/garmin/export_full_2024.txt
chmod -R 644 /workspace/chat_logs/marcus_coach_2024.txt
chmod -R 644 /workspace/race_results/race_results_2024.txt
chmod -R 644 /workspace/raw_exports/strava/activities_summary_2024.txt

echo "Setup complete. Raw fitness data ready in /workspace."
echo "Agent should process data and write to ~/fitness/memory.md"