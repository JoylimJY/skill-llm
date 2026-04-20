from pathlib import Path
import random

random.seed(1337)

files = {
    "app.log": """2025-04-18 10:15:01 INFO Starting service
2025-04-18 10:15:02 INFO user=alice password=Summer2025! login succeeded
2025-04-18 10:15:03 WARN upstream response slow
2025-04-18 10:15:04 DEBUG api_token=tok_live_ABC123xyz890DEF456 call_id=17
2025-04-18 10:15:05 INFO request_id=req-1001 completed
""",
    "auth.log": """2025-04-18T10:16:11Z INFO session_id=SID-9f8e7d6c5b4a user=bob authenticated
2025-04-18T10:16:12Z INFO bearer token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.payload
2025-04-18T10:16:13Z ERROR invalid password supplied for user=bob
2025-04-18T10:16:14Z INFO logout complete
""",
    "audit.txt": """AUDIT START
client=web portal=main session=ZXCV-1122-ABCD-9988
note: customer complained about reset link
secret_key: sk_test_51JkL9xExampleSecretValue0001
AUDIT END
""",
}

for name, content in files.items():
    Path(name).write_text(content, encoding="utf-8")

# marker file for verification
Path(".marker").write_text("SENSITIVE_MARKERS_PRESENT\n", encoding="utf-8")
