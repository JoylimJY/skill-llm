#!/usr/bin/env python3
import os
import random

# Set deterministic seed
random.seed(42)

# Create a simple context file that might contain team information
with open('team_context.txt', 'w') as f:
    f.write("Mobile Development Team Context\n")
    f.write("Recent accomplishments: shipped user onboarding flow, bug fixes\n")
    f.write("Current blockers: backend API dependencies\n")
    f.write("Upcoming work: notification system, user testing\n")
    f.write("MARKER_MOBILE_TEAM_INFO")

# Create a sample previous update for reference
with open('previous_3p_example.txt', 'w') as f:
    f.write("📱 iOS Team (Dec 4-8)\n")
    f.write("Progress: Launched dark mode feature to 100% of users, resolved 8 crash bugs affecting login flow\n")
    f.write("Plans: Begin work on widget redesign, conduct accessibility audit\n")
    f.write("Problems: Delayed by App Store review process, need additional QA resources\n")
    f.write("MARKER_3P_EXAMPLE_FORMAT")

print("Generated input files for 3P update task")