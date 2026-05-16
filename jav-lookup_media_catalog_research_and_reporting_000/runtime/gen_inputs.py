import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested distractor structure
dirs = [
    "archive/2023/q1",
    "archive/2023/q2",
    "archive/2024/q1",
    "catalog/raw",
    "catalog/processed",
    "exports/csv",
    "exports/json",
    "reports/monthly",
    "reports/weekly",
    "config/env",
    "tools/scripts",
    "tools/templates",
    "logs/access",
    "logs/error",
    "temp/staging",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "archive/2023/q1/batch_results_old.csv": "code,title,year\nABF-001,Old Film,2023\nSTART-001,Another Film,2023\n",
    "archive/2023/q2/summary.txt": "Q2 2023 summary report. Total titles processed: 47. Revenue impact: N/A.\n",
    "archive/2024/q1/pending_review.txt": "ABF-328 - pending\nMIDA-563 - pending\nSTART-510 - pending\n",
    "catalog/raw/codes_dump.txt": "Raw dump - do not use directly\nJUR-067\nSSIS-999\nDAD-001\n",
    "catalog/processed/README_ignore.txt": "This folder contains processed outputs. Do not edit.\n",
    "exports/csv/template.csv": "num,code,cast,studio,plot,magnet\n1,,,,\n2,,,,\n",
    "exports/json/schema.json": json.dumps({"type": "object", "properties": {"code": {"type": "string"}, "cast": {"type": "string"}}}),
    "reports/monthly/oct_stub.txt": "October report placeholder.\n",
    "reports/weekly/week42.txt": "Week 42: 12 new titles added.\n",
    "config/env/lookup.conf": "BASE_URL=http://localhost:7788\nTIMEOUT=30\nMAX_RETRIES=3\n",
    "tools/scripts/batch_query_old.sh": "#!/bin/bash\n# DEPRECATED - do not use\necho 'This script is deprecated'\n",
    "tools/templates/output_template.md": "# Template\n| # | Code | Cast | Studio | Plot |\n|---|------|------|--------|------|\n",
    "logs/access/2024-10-01.log": "GET /search?q=ABF-328 200 OK\nGET /search?q=START-510 200 OK\n",
    "logs/error/2024-10-01.log": "ERROR: Connection timeout for MIDA-563\nERROR: Not found: PRED-999\n",
    "temp/staging/partial_output.md": "| 1 | ABF-328 | ??? | ??? | incomplete data |\n",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE ACTUAL TASK INPUT: a messy, realistic request file
task_input = """番號查詢請求
=============

以下是需要查詢的番號清單，請幫我整理成完整表格。

需要查詢主演、片商、一句話劇情，以及磁力鏈接（需要中文字幕版 -c）。

番號列表（部分已知主演）：
主演：ABF-328 → 涼森玲夢
主演：JUR-067 → 久遠美緒
主演：MIDA-563 → 不知道（請幫我查）
主演：START-510 → 已知是葵つかさ（Aoi Tsukasa）
主演：SSIS-592 → 不知道

備注：
- 有 -c 中字版的請在備注欄標明
- 沒有特殊版本的請標明"暫無特殊版本"
- 磁力格式要完整，包含 dn 參數
"""

with open(os.path.join(workspace, "query_request.txt"), "w", encoding="utf-8") as f:
    f.write(task_input)

# Mock server data file (the agent should NOT read this directly - it's for the mock server)
mock_data = {
    "ABF-328": {
        "cast": "涼森玲夢",
        "cast_ja": "涼森れむ",
        "studio": "Prestige",
        "plot_zh": "涼森玲夢飾演一名溫柔的家教老師，在課後輔導中逐漸與學生發展出禁忌的師生戀情，最終突破道德界限。",
        "plot_ja": "家庭教師として働く涼森れむが、放課後の個別指導で生徒との禁断の関係へと発展していく物語。",
        "magnets": [
            {
                "hash": "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2",
                "filename": "ABF-328.mp4",
                "size_mb": 4200,
                "tags": []
            },
            {
                "hash": "B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3",
                "filename": "ABF-328-C.mp4",
                "size_mb": 4800,
                "tags": ["-c"]
            }
        ]
    },
    "JUR-067": {
        "cast": "久遠美緒",
        "cast_ja": "久遠みお",
        "studio": "Madonna",
        "plot_zh": "久遠美緒飾演丈夫外派期間獨守空閨的人妻，被鄰居男子長期糾纏，最終陷入無法自拔的婚外情。",
        "plot_ja": "夫の出張中に隣人男性に迫られ続け、禁断の関係に落ちていく人妻の物語。",
        "magnets": [
            {
                "hash": "C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4",
                "filename": "JUR-067.mp4",
                "size_mb": 3900,
                "tags": []
            }
        ]
    },
    "MIDA-563": {
        "cast": "三上悠亞",
        "cast_ja": "三上悠亜",
        "studio": "MOODYZ",
        "plot_zh": "三上悠亞扮演因工作壓力而尋求刺激的職場女性，與上司在出差途中發生激烈的秘密戀情，回國後面臨兩難抉擇。",
        "plot_ja": "出張先で上司との秘密の恋愛関係に発展した職場女性の葛藤を描く作品。",
        "magnets": [
            {
                "hash": "D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5",
                "filename": "MIDA-563.mp4",
                "size_mb": 5100,
                "tags": []
            },
            {
                "hash": "E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6",
                "filename": "MIDA-563-C.mp4",
                "size_mb": 5600,
                "tags": ["-c"]
            },
            {
                "hash": "F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1",
                "filename": "MIDA-563-UC.mp4",
                "size_mb": 6200,
                "tags": ["-u", "-c", "-uc"]
            }
        ]
    },
    "START-510": {
        "cast": "葵つかさ",
        "cast_ja": "葵つかさ",
        "studio": "SOD Create",
        "plot_zh": "葵つかさ飾演一位嚴厲的女上司，在公司旅遊期間展現出截然不同的溫柔面貌，與下屬度過了一段難忘的秘密時光。",
        "plot_ja": "職場での厳格な姿とは打って変わって、社員旅行中に部下と特別な時間を過ごす女上司の物語。",
        "magnets": [
            {
                "hash": "1A2B3C4D5E6F1A2B3C4D5E6F1A2B3C4D5E6F1A2B",
                "filename": "START-510.mp4",
                "size_mb": 4400,
                "tags": []
            }
        ]
    },
    "SSIS-592": {
        "cast": "八木奈々",
        "cast_ja": "八木奈々",
        "studio": "S1 No.1 Style",
        "plot_zh": "八木奈々扮演剛轉學到新學校的清純女生，面對多名男同學的追求，在青澀的校園生活中體驗了各種初次的心跳時刻。",
        "plot_ja": "転校生として新しい学校に来た清純な少女が、複数の男子から求愛され、初めての経験を重ねる青春物語。",
        "magnets": [
            {
                "hash": "2B3C4D5E6F1A2B3C4D5E6F1A2B3C4D5E6F1A2B3C",
                "filename": "SSIS-592.mp4",
                "size_mb": 4700,
                "tags": []
            },
            {
                "hash": "3C4D5E6F1A2B3C4D5E6F1A2B3C4D5E6F1A2B3C4D",
                "filename": "SSIS-592-C.mp4",
                "size_mb": 5200,
                "tags": ["-c"]
            }
        ]
    }
}

with open(os.path.join(workspace, "config/env/mock_db.json"), "w", encoding="utf-8") as f:
    json.dump(mock_data, f, ensure_ascii=False, indent=2)

# Mock server script
mock_server_code = '''#!/usr/bin/env python3
"""
Mock JAVDB-like server for JAV lookup testing.
Simulates javdb.com search and detail page endpoints.
"""
import json
import re
from flask import Flask, jsonify, request
from pathlib import Path

app = Flask(__name__)

DB_PATH = Path("/workspace/config/env/mock_db.json")
with open(DB_PATH, encoding="utf-8") as f:
    DB = json.load(f)

def get_video_id(code):
    """Generate a fake video ID from code."""
    mapping = {
        "ABF-328": "vABF328x",
        "JUR-067": "qAb836",
        "MIDA-563": "vMIDA563",
        "START-510": "vSTART510",
        "SSIS-592": "vSSIS592",
    }
    return mapping.get(code.upper(), None)

@app.route("/search")
def search():
    q = request.args.get("q", "").strip().upper()
    f = request.args.get("f", "all")
    
    if q in DB:
        vid = get_video_id(q)
        return jsonify({
            "query": q,
            "results": [
                {
                    "code": q,
                    "title": f"{q} - {DB[q][\'cast\']}",
                    "url": f"/v/{vid}",
                    "cast": DB[q]["cast"]
                }
            ]
        })
    return jsonify({"query": q, "results": []})

@app.route("/v/<vid>")
def detail(vid):
    # reverse lookup
    reverse_map = {
        "vABF328x": "ABF-328",
        "qAb836": "JUR-067",
        "vMIDA563": "MIDA-563",
        "vSTART510": "START-510",
        "vSSIS592": "SSIS-592",
    }
    code = reverse_map.get(vid)
    if not code or code not in DB:
        return jsonify({"error": "not found"}), 404
    
    entry = DB[code]
    magnets = []
    for m in entry["magnets"]:
        magnets.append({
            "magnet": f"magnet:?xt=urn:btih:{m[\'hash\']}&dn={m[\'filename\']}",
            "filename": m["filename"],
            "size_mb": m["size_mb"],
            "tags": m["tags"]
        })
    
    return jsonify({
        "code": code,
        "cast": entry["cast"],
        "cast_ja": entry["cast_ja"],
        "studio": entry["studio"],
        "plot_zh": entry["plot_zh"],
        "plot_ja": entry["plot_ja"],
        "magnets": magnets
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7788, debug=False)
'''

with open(os.path.join(workspace, "tools/scripts/mock_javdb_server.py"), "w", encoding="utf-8") as f:
    f.write(mock_server_code)

print("Workspace initialized successfully.")
print(f"Files created: {len(distractors) + 3} files")
print("Task input: /workspace/query_request.txt")
print("Mock server: /workspace/tools/scripts/mock_javdb_server.py")