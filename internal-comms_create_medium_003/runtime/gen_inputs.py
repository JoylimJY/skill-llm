import json
# Generate a simulated Slack message feed with updates from the Mobile Dev Team for input context

slack_messages = [
    {
        "channel": "mobile-team",
        "date": "2024-04-20",
        "user": "alice",
        "message": "Deployed version 2.1 to iOS with a 15% speed improvement."
    },
    {
        "channel": "mobile-team",
        "date": "2024-04-18",
        "user": "bob",
        "message": "Fixed 10 critical bugs reported last sprint."
    },
    {
        "channel": "mobile-team",
        "date": "2024-04-16",
        "user": "carol",
        "message": "Blocked by API rate limits slowing feature rollout."
    },
    {
        "channel": "mobile-team",
        "date": "2024-04-22",
        "user": "dave",
        "message": "Planning implementation of biometric login next week."
    },
    {
        "channel": "mobile-team",
        "date": "2024-04-21",
        "user": "eve",
        "message": "Need design resource to unblock UI revamp."
    }
]

with open('slack_mobile_team.json', 'w') as f:
    json.dump(slack_messages, f, indent=2)

# Also create a dummy calendar event file describing upcoming meetings
calendar_events = [
    {
        "title": "Mobile Dev Weekly Review",
        "date": "2024-04-22",
        "attendees": 15,
        "notes": "Discuss roadmap and blockers for next sprint."
    }
]

with open('calendar_events.json', 'w') as f:
    json.dump(calendar_events, f, indent=2)
