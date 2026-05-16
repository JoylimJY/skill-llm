import os
import json

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Distractor directory structure ---
distractor_dirs = [
    "customer_support/tickets/pending",
    "customer_support/tickets/resolved",
    "customer_support/templates/old",
    "customer_support/templates/archive",
    "platform_settings/coconala",
    "platform_settings/fiverr",
    "platform_settings/twitter",
    "analytics/monthly",
    "analytics/weekly",
    "team_docs/guidelines",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files (irrelevant content)
distractors = {
    "customer_support/tickets/pending/ticket_001.txt": "案件番号: 001\n依頼者: 田中様\n内容: ロゴデザイン依頼\nステータス: 対応中",
    "customer_support/tickets/resolved/ticket_099.txt": "案件番号: 099\nステータス: 解決済み",
    "customer_support/templates/old/standard_reply_v1.txt": "ご連絡ありがとうございます。担当者が確認し、折り返しご連絡申し上げます。",
    "customer_support/templates/archive/faq_old.txt": "よくある質問\nQ: 納期はどのくらいですか？\nA: 通常3〜5営業日です。",
    "platform_settings/coconala/config.yaml": "platform: coconala\ndefault_language: ja\nresponse_style: business",
    "platform_settings/fiverr/config.yaml": "platform: fiverr\ndefault_language: en\nresponse_style: professional",
    "platform_settings/twitter/config.yaml": "platform: twitter\ndefault_language: ja\nresponse_style: casual",
    "analytics/monthly/report_2024_01.csv": "date,messages_sent,avg_length\n2024-01-01,45,120\n2024-01-02,38,98",
    "analytics/weekly/week_01.csv": "week,platform,count\n1,coconala,22\n1,fiverr,18",
    "team_docs/guidelines/response_policy.txt": "全プラットフォームで24時間以内に返信すること。",
    "team_docs/guidelines/escalation.txt": "クレーム案件はマネージャーにエスカレーション。",
    "customer_support/tickets/pending/ticket_002.txt": "案件番号: 002\n依頼者: 鈴木様\n内容: バナー制作\nステータス: 見積中",
}
for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- THE ACTUAL TASK INPUT FILE ---
# A JSON file containing AI-sounding draft replies that need to be rewritten naturally.
# Each entry has: platform, original_customer_message, ai_draft_reply
# The agent must rewrite ai_draft_reply into a natural version and output to natural_replies.json

draft_replies = [
    {
        "id": 1,
        "platform": "coconala",
        "customer_message": "ロゴのデザインをお願いしたいです。いくつか確認させてください。",
        "ai_draft_reply": "お問い合わせいただきまして誠にありがとうございます。\nご依頼の件について確認いたしました。\n以下の通りご回答させていただきます：\n1. まず、ご希望のスタイルをお聞かせいただけますでしょうか。\n2. 次に、納期のご希望をお聞かせいただけますでしょうか。\n3. 最後に、ご予算の目安をお教えいただけますでしょうか。\nご不明な点がございましたら、お気軽にお申し付けください。"
    },
    {
        "id": 2,
        "platform": "x_threads",
        "customer_message": "このデザインどう思う？",
        "ai_draft_reply": "ご質問ありがとうございます。このデザインについて申し上げますと、以下のポイントをご確認いただけますでしょうか：\n・カラーバランスが良好であると思われます\n・フォントの選択も適切かと思われます\nご不明な点がございましたら、お気軽にお問い合わせください。"
    },
    {
        "id": 3,
        "platform": "fiverr",
        "customer_message": "Hi, I need a logo for my coffee shop. Can you help?",
        "ai_draft_reply": "I would like to express my sincere gratitude for your inquiry. I am pleased to inform you that I would be able to assist you with your request. Please find below my initial questions:\n1. What style are you looking for?\n2. What is your budget?\n3. When do you need it by?\nPlease do not hesitate to contact me should you have any further questions."
    },
    {
        "id": 4,
        "platform": "coconala",
        "customer_message": "納期を少し早めることはできますか？急ぎになってしまって。",
        "ai_draft_reply": "ご連絡いただきまして誠にありがとうございます。\n納期の変更についてご要望をいただきました件、誠に申し訳ございませんが、現在の作業スケジュールの都合上、ご希望に沿えるかどうか確認が必要でございます。\n〜かと思われますが、確認の上、改めてご連絡させていただきます。\nご不明な点がございましたら、お気軽にお申し付けください。"
    },
    {
        "id": 5,
        "platform": "x_threads",
        "customer_message": "修正お願い！",
        "ai_draft_reply": "ご依頼ありがとうございます。修正作業を承りましたことをご報告申し上げます。以下の通り対応させていただきます：\n・修正内容を確認いたしました\n・作業を開始させていただきます\nご確認ください。"
    },
    {
        "id": 6,
        "platform": "fiverr",
        "customer_message": "Looks great! Just one small change needed.",
        "ai_draft_reply": "Thank you very much for your kind feedback. I would be happy to make the requested modification. Please find below my response to your request. I will proceed with the changes as per your instructions and deliver the updated version at the earliest convenience. Please do not hesitate to reach out should you require any further assistance."
    }
]

input_file = os.path.join(workspace, "draft_replies.json")
with open(input_file, "w", encoding="utf-8") as f:
    json.dump(draft_replies, f, ensure_ascii=False, indent=2)

print(f"Generated {input_file} with {len(draft_replies)} draft replies.")
print("Distractor files created in nested directories.")
print("Task: Agent must rewrite ai_draft_reply entries into natural replies and save as natural_replies.json")