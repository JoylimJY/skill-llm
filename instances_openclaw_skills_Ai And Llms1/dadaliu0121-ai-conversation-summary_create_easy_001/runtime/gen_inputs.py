from pathlib import Path
import json

conversation = [
    {"role": "user", "content": "Hi, can you help me plan a short trip to Kyoto?"},
    {"role": "assistant", "content": "Absolutely. I can help with itinerary ideas, transportation, and budget tips."},
    {"role": "user", "content": "Great. Also, please summarize our chat at the end."},
    {"role": "assistant", "content": "Sure — I will provide a concise summary when you're ready."},
    {"role": "user", "content": "Let's keep it simple and focus on food, temples, and a relaxed pace."}
]

Path("conversation.json").write_text(json.dumps(conversation, ensure_ascii=False, indent=2), encoding="utf-8")
Path("marker.txt").write_text("MARKER_CONVERSATION_SUMMARY_EASY_001\n", encoding="utf-8")
Path("history_summary.txt").write_text("Previous summary marker: HIST_SUMMARY_ALPHA\n", encoding="utf-8")
