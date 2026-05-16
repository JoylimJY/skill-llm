import os
import json
import csv
import random

random.seed(42)

WORKSPACE = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/client_inbox",
    "workspace/archive/2024/Q1",
    "workspace/archive/2024/Q2",
    "workspace/archive/2024/Q3",
    "workspace/templates_old",
    "workspace/logs/system",
    "workspace/reports/monthly",
    "workspace/escalations",
    "workspace/incidents",
    "workspace/responses",
    "workspace/config",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/config/platform_config.yaml": "platform: coconala\ncontact_email: support@example.com\nmax_response_hours: 24\n",
    "workspace/config/old_levels.txt": "old system: A B C D levels - DEPRECATED\n",
    "workspace/templates_old/response_v1.txt": "Dear Customer, We are sorry for the inconvenience. Regards,\n",
    "workspace/templates_old/escalation_v1.txt": "ALERT: Issue detected. Please review.\n",
    "workspace/archive/2024/Q1/summary.csv": "ticket_id,status\nT-001,closed\nT-002,closed\n",
    "workspace/archive/2024/Q2/summary.csv": "ticket_id,status\nT-101,closed\nT-102,refunded\n",
    "workspace/archive/2024/Q3/notes.txt": "Q3 had 3 escalations. All resolved within SLA.\n",
    "workspace/logs/system/app.log": "2024-09-01 12:00:00 INFO System started\n2024-09-02 08:30:00 WARN Slow response detected\n",
    "workspace/reports/monthly/october_kpi.json": json.dumps({"tickets": 45, "resolved": 42, "escalated": 3}),
    "workspace/reports/monthly/november_kpi.json": json.dumps({"tickets": 38, "resolved": 35, "escalated": 3}),
    "workspace/escalations/.gitkeep": "",
    "workspace/incidents/.gitkeep": "",
    "workspace/responses/.gitkeep": "",
}

for path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE PROBLEM: A messy incoming complaint inbox CSV
# Each row is a complaint ticket with varying severity
complaints = [
    {
        "ticket_id": "T-2024-1201",
        "customer_name": "田中 健太",
        "platform": "ココナラ",
        "received_at": "2024-12-01 09:15:00",
        "message": "先日依頼したロゴデザインについて、配色が打ち合わせの内容と全然違います。修正をお願いしたいです。",
        "category": "修正依頼",
        "notes": "client seems polite but firm",
    },
    {
        "ticket_id": "T-2024-1202",
        "customer_name": "佐藤 美咲",
        "platform": "ランサーズ",
        "received_at": "2024-12-01 11:40:00",
        "message": "納品されたWebサイトのお問い合わせフォームが全く動作しません。約束した機能が使えない状態なので、全額返金を要求します。",
        "category": "返金要求",
        "notes": "confirmed: contact form broken on our end",
    },
    {
        "ticket_id": "T-2024-1203",
        "customer_name": "鈴木 大輔",
        "platform": "ココナラ",
        "received_at": "2024-12-01 14:05:00",
        "message": "サービスについて少し気になる点があったのですが、どのようなファイル形式で納品されますか？",
        "category": "質問",
        "notes": "general inquiry",
    },
    {
        "ticket_id": "T-2024-1204",
        "customer_name": "山本 花子",
        "platform": "クラウドワークス",
        "received_at": "2024-12-02 08:55:00",
        "message": "アカウントに警告が来ています。このまま放置するとアカウントが停止されると書いてあります。御社の納品物が原因ではないかと疑っています。消費者センターへの相談も検討中です。",
        "category": "アカウント警告・法的言及",
        "notes": "very serious - mentions legal action and consumer center",
    },
]

inbox_path = os.path.join(WORKSPACE, "workspace/client_inbox/complaints_2024-12-02.csv")
fieldnames = ["ticket_id", "customer_name", "platform", "received_at", "message", "category", "notes"]

with open(inbox_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in complaints:
        writer.writerow(row)

# Also add a "cause investigation" supplement file (simulating follow-up info available for T-2024-1201 and T-2024-1202)
cause_data = {
    "T-2024-1201": {
        "cause": "打ち合わせ時のカラーコードのメモに誤りがあり、異なる配色で制作してしまいました。",
        "fix": "正しいカラーコードで修正版を48時間以内に再納品いたします。",
        "prevention": "今後は打ち合わせ後に仕様確認書をお客様に送付し、承認をいただいてから制作を開始します。"
    },
    "T-2024-1202": {
        "cause": "フォームの送信先メールアドレスの設定が本番環境で反映されていませんでした。",
        "fix": "即座に設定を修正し、動作確認を完了しました。返金については人間の判断を仰ぎます。",
        "prevention": "本番環境へのデプロイ後、全機能の動作チェックリストを必ず実行します。"
    }
}

cause_path = os.path.join(WORKSPACE, "workspace/client_inbox/cause_investigation.json")
with open(cause_path, "w", encoding="utf-8") as f:
    json.dump(cause_data, f, ensure_ascii=False, indent=2)

print("Workspace generated successfully.")
print(f"Inbox CSV: {inbox_path}")
print(f"Cause investigation data: {cause_path}")