from pathlib import Path
import json

chat = [
    {"role": "user", "content": "Hey, can you help me plan a weekend trip to Kyoto?"},
    {"role": "assistant", "content": "Absolutely. Do you prefer temples, food, shopping, or a mix of all three?"},
    {"role": "user", "content": "A mix. Also, I need it to stay under $600 total."},
    {"role": "assistant", "content": "Got it. I can draft a budget-friendly 2-day itinerary and include transit estimates."},
    {"role": "user", "content": "Great. Please also add a reminder to book hotels before Friday."},
]
previous_summary = "The user wants help planning a short trip to Kyoto on a budget."

Path("chat.json").write_text(json.dumps(chat, ensure_ascii=False, indent=2), encoding="utf-8")
Path("history_summary.txt").write_text(previous_summary, encoding="utf-8")
Path("marker.txt").write_text("MARKER:KYOTO_SUMMARY_TASK_v1", encoding="utf-8")
