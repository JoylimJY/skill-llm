import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "workspace/community_data/raw_exports",
    "workspace/community_data/archived",
    "workspace/content_team/drafts",
    "workspace/content_team/published",
    "workspace/analytics/weekly_reports",
    "workspace/analytics/old",
    "workspace/product/specs",
    "workspace/product/changelogs",
    "workspace/hr/onboarding",
    "workspace/legal/licenses",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files (irrelevant content)
distractors = {
    "workspace/analytics/weekly_reports/week42_traffic.csv": "date,pageviews,sessions\n2024-10-14,4200,1800\n2024-10-15,3900,1650",
    "workspace/analytics/old/q3_summary.txt": "Q3 summary: traffic up 12%, bounce rate 58%",
    "workspace/content_team/published/blog_post_oct.md": "# How Smart Homes Save Energy\nThis is a published blog post about smart home energy saving.",
    "workspace/content_team/drafts/video_script_draft1.txt": "DRAFT: Intro hook for smart lock video - needs approval",
    "workspace/product/specs/hub_v2_specs.json": json.dumps({"model": "SmartHub v2", "connectivity": ["WiFi", "Zigbee", "Z-Wave"], "power": "USB-C"}),
    "workspace/product/changelogs/firmware_3.2.1.md": "## Firmware 3.2.1\n- Fixed connection drop on 2.4GHz\n- Improved Zigbee pairing",
    "workspace/hr/onboarding/content_guidelines.txt": "All content must be approved by legal. No third-party trademarks.",
    "workspace/legal/licenses/cc_attribution.txt": "This workspace uses CC BY-SA 4.0 licensed assets.",
    "workspace/community_data/archived/comments_q2_2024.txt": "Old archived comments from Q2 2024 - do not use for current analysis.",
    "workspace/product/specs/sensor_compatibility.csv": "sensor,protocol,range_m\nMotion PIR,Zigbee,15\nDoor contact,Z-Wave,20\nTemp sensor,WiFi,50",
    "workspace/analytics/weekly_reports/engagement_oct.json": json.dumps({"avg_comments_per_post": 34, "top_platform": "YouTube", "dms_received": 87}),
}
for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# --- THE MAIN PROBLEM FILE: Raw messy community comments/DMs ---
# These are realistic, messy, partially duplicate, varied-phrasing comments
# from a smart home device community (hub, sensors, automations)
raw_comments = [
    # HOW-TO cluster
    {"id": "c001", "source": "youtube_comment", "date": "2024-10-15", "text": "how do i connect my hub to google home??"},
    {"id": "c002", "source": "youtube_comment", "date": "2024-10-15", "text": "HOW DO I CONNECT THE HUB TO GOOGLE HOME"},
    {"id": "c003", "source": "dm", "date": "2024-10-16", "text": "Hey, can you do a video on connecting the SmartHub to Google Home? I've been stuck for hours"},
    {"id": "c004", "source": "youtube_comment", "date": "2024-10-17", "text": "anyone know how to set up automations with sunrise/sunset? the app is confusing"},
    {"id": "c005", "source": "faq_thread", "date": "2024-10-18", "text": "How to create a sunrise sunset automation? Step by step please"},
    {"id": "c006", "source": "youtube_comment", "date": "2024-10-18", "text": "can you explain how to set up sunrise automation step by step"},
    {"id": "c007", "source": "dm", "date": "2024-10-19", "text": "how to add zigbee devices without the hub resetting? mine keeps resetting when I pair"},
    {"id": "c008", "source": "youtube_comment", "date": "2024-10-19", "text": "How do I pair zigbee sensors? the pairing mode keeps timing out"},
    # TROUBLESHOOTING cluster
    {"id": "c009", "source": "youtube_comment", "date": "2024-10-14", "text": "my hub keeps dropping wifi every night around 3am, anyone else?"},
    {"id": "c010", "source": "faq_thread", "date": "2024-10-15", "text": "Hub disconnects from WiFi randomly - is this a known bug?"},
    {"id": "c011", "source": "dm", "date": "2024-10-16", "text": "hub loses wifi connection overnight and I have to manually restart it every morning, super frustrating"},
    {"id": "c012", "source": "youtube_comment", "date": "2024-10-17", "text": "automations not triggering at the right time. Is it a timezone bug?"},
    {"id": "c013", "source": "faq_thread", "date": "2024-10-18", "text": "My schedules are off by 1 hour - daylight savings issue?"},
    {"id": "c014", "source": "youtube_comment", "date": "2024-10-20", "text": "schedules off by one hour since clocks changed"},
    # COMPARISON cluster
    {"id": "c015", "source": "youtube_comment", "date": "2024-10-14", "text": "SmartHub vs Home Assistant - which one should I get?"},
    {"id": "c016", "source": "dm", "date": "2024-10-15", "text": "Is SmartHub better than Home Assistant for beginners? I don't want to deal with complex setup"},
    {"id": "c017", "source": "youtube_comment", "date": "2024-10-16", "text": "what's the difference between SmartHub and Hubitat?"},
    {"id": "c018", "source": "faq_thread", "date": "2024-10-17", "text": "SmartHub vs Hubitat - pros and cons?"},
    {"id": "c019", "source": "youtube_comment", "date": "2024-10-19", "text": "comparing smarthub to home assistant - which has better local processing?"},
    # BUYING CONCERNS cluster
    {"id": "c020", "source": "youtube_comment", "date": "2024-10-14", "text": "Is the SmartHub worth $129? Seems expensive for what it does"},
    {"id": "c021", "source": "dm", "date": "2024-10-15", "text": "honestly $129 seems too much - is there a cheaper alternative that does the same thing?"},
    {"id": "c022", "source": "youtube_comment", "date": "2024-10-16", "text": "will this work with my old Philips Hue bulbs or do I need to buy new ones?"},
    {"id": "c023", "source": "faq_thread", "date": "2024-10-17", "text": "Does SmartHub work with existing Philips Hue setup? Don't want to replace everything"},
    {"id": "c024", "source": "dm", "date": "2024-10-18", "text": "Is there a monthly subscription fee? The website isn't clear about this"},
    {"id": "c025", "source": "youtube_comment", "date": "2024-10-19", "text": "do I have to pay monthly for cloud features? That's a dealbreaker for me"},
    # OBJECTIONS/MYTHS cluster
    {"id": "c026", "source": "youtube_comment", "date": "2024-10-14", "text": "smart home stuff is just a gimmick, nothing actually saves you time"},
    {"id": "c027", "source": "dm", "date": "2024-10-15", "text": "I heard smart home devices are a security risk and can get hacked easily"},
    {"id": "c028", "source": "youtube_comment", "date": "2024-10-16", "text": "these things are always listening right? Not sure I trust it in my house"},
    {"id": "c029", "source": "faq_thread", "date": "2024-10-17", "text": "Is local processing really more private than cloud? My IT friend says it doesn't matter"},
    {"id": "c030", "source": "youtube_comment", "date": "2024-10-18", "text": "smart home is too complicated for non-tech people, I tried and gave up"},
    # Near-duplicates / noise
    {"id": "c031", "source": "youtube_comment", "date": "2024-10-20", "text": "hub disconnects from wifi at night AGAIN"},
    {"id": "c032", "source": "youtube_comment", "date": "2024-10-20", "text": "How do I connect hub to google home? Can't find the option"},
    {"id": "c033", "source": "dm", "date": "2024-10-21", "text": "SmartHub vs Home Assistant which is better for beginners?"},
    {"id": "c034", "source": "youtube_comment", "date": "2024-10-21", "text": "worth buying at $129? Or wait for a sale?"},
    {"id": "c035", "source": "faq_thread", "date": "2024-10-21", "text": "Is this a gimmick or does it actually save time in real life?"},
    # Extra noise
    {"id": "c036", "source": "youtube_comment", "date": "2024-10-22", "text": "great video as always!"},
    {"id": "c037", "source": "youtube_comment", "date": "2024-10-22", "text": "Love your content, keep it up!"},
    {"id": "c038", "source": "dm", "date": "2024-10-22", "text": "Can you review the new SmartHub Pro when it comes out?"},
    {"id": "c039", "source": "youtube_comment", "date": "2024-10-22", "text": "first!"},
    {"id": "c040", "source": "faq_thread", "date": "2024-10-22", "text": "Spam: Buy cheap smart home devices at myspamsite.com"},
]

output_path = "workspace/community_data/raw_exports/comments_oct2024.json"
with open(output_path, "w") as f:
    json.dump(raw_comments, f, indent=2)

print(f"Generated {len(raw_comments)} raw community comments in {output_path}")
print("Workspace structure created with distractor files.")