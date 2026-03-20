import os

# Create a simple input file with team context
with open('team_context.txt', 'w') as f:
    f.write("Mobile Engineering Team Context\n")
    f.write("Team Size: 8 engineers\n")
    f.write("Focus: iOS and Android mobile applications\n")
    f.write("Manager: Sarah Chen\n")
    f.write("MARKER_TEAM_MOBILE_ENG")

# Create sample slack messages file
with open('recent_updates.txt', 'w') as f:
    f.write("Recent team updates from Slack:\n")
    f.write("- Push notifications now working across all devices\n")
    f.write("- Bug fix sprint completed with 15 issues resolved\n")
    f.write("- A/B test framework integrated successfully\n")
    f.write("- Payment flow redesign approved by design team\n")
    f.write("- Performance benchmarks show 20% improvement needed\n")
    f.write("MARKER_SLACK_UPDATES")

print("Input files created successfully")