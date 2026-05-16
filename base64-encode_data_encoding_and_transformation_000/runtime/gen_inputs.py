import os
import random
import json

random.seed(42)

WORKSPACE = "/workspace"

# --- Create a realistic, messy directory structure ---
dirs = [
    "archive/legacy/v1/raw",
    "archive/legacy/v1/processed",
    "archive/legacy/v2/raw",
    "archive/legacy/v2/processed",
    "pipeline/ingestion",
    "pipeline/transform",
    "pipeline/output",
    "config/env",
    "config/schema",
    "logs/2023",
    "logs/2024",
    "docs/internal",
    "scratch",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files (realistic, misleading) ---

# 1. A fake config that looks like it might encode something
with open(os.path.join(WORKSPACE, "config/env/pipeline.conf"), "w") as f:
    f.write("[encoding]\ntype=utf-8\ntransport=json\nlegacy_compat=true\n")

# 2. A JSON schema with field names that look relevant
with open(os.path.join(WORKSPACE, "config/schema/payload_schema.json"), "w") as f:
    json.dump({
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "encoding": {"type": "string", "enum": ["base64", "raw"]},
            "source": {"type": "string"}
        }
    }, f, indent=2)

# 3. A fake processed file from v1 with base64-like noise
with open(os.path.join(WORKSPACE, "archive/legacy/v1/processed/record_001.b64"), "w") as f:
    f.write("SGVsbG8gV29ybGQ=\n")  # Hello World — distractor

# 4. A fake log
with open(os.path.join(WORKSPACE, "logs/2024/ingestion.log"), "w") as f:
    f.write("2024-01-15 10:23:11 INFO Ingested 412 records\n")
    f.write("2024-01-15 10:23:45 WARN Encoding mismatch on record 77\n")
    f.write("2024-01-15 10:24:01 ERROR Failed to decode payload: invalid sequence\n")

# 5. A transform script stub (distractor)
with open(os.path.join(WORKSPACE, "pipeline/transform/normalize.py"), "w") as f:
    f.write("# Legacy normalization pipeline\n# TODO: update encoding logic\ndef normalize(s):\n    return s.strip()\n")

# 6. Ingestion metadata distractor
with open(os.path.join(WORKSPACE, "pipeline/ingestion/meta.json"), "w") as f:
    json.dump({"source": "legacy-cms-v1", "record_count": 412, "status": "partial"}, f, indent=2)

# 7. A raw record that uses HTML entities but is wrong (agent must NOT copy this)
with open(os.path.join(WORKSPACE, "archive/legacy/v2/raw/snippet_raw.txt"), "w") as f:
    f.write("&lt;title&gt;Legacy Article &amp; Notes&lt;/title&gt; &apos;quoted&apos;\n")

# 8. A scratch file with a seemingly encoded string (red herring)
with open(os.path.join(WORKSPACE, "scratch/test_payload.txt"), "w") as f:
    f.write("bmFtZT1Kb2huJTIwRG9l\n")  # different base64

# 9. Old processed v2 distractor
with open(os.path.join(WORKSPACE, "archive/legacy/v2/processed/record_002.json"), "w") as f:
    json.dump({"id": 2, "content": "SGkgdGhlcmU=", "status": "ok"}, f)

# 10. Docs distractor
with open(os.path.join(WORKSPACE, "docs/internal/migration_notes.md"), "w") as f:
    f.write("# Migration Notes\n\nAll v1 records must be re-encoded before API submission.\n"
            "The transport format requires safe string packaging.\n"
            "HTML special characters must be neutralized before encoding.\n")

# 11. Another log distractor
with open(os.path.join(WORKSPACE, "logs/2023/errors.log"), "w") as f:
    f.write("2023-11-01 CRITICAL Payload corruption in batch 9\n")

# --- THE ACTUAL PROBLEM INPUT ---
# A URL percent-encoded string from the legacy CMS that the agent must process.
# Decoded, this is: <Article> "Héros & Champions" — It's 'legendary'!
# The string contains: <, >, ", &, ', non-ASCII (é), and a space-like encoding.
# URL-encoded (encodeURIComponent semantics, spaces as %20):
url_encoded_payload = "%3CArticle%3E%20%22H%C3%A9ros%20%26%20Champions%22%20%E2%80%94%20It%27s%20%27legendary%27!"

with open(os.path.join(WORKSPACE, "pipeline/ingestion/incoming_payload.txt"), "w") as f:
    f.write(url_encoded_payload + "\n")

print("Workspace generated successfully.")
print(f"Payload written to: pipeline/ingestion/incoming_payload.txt")
print(f"Content: {url_encoded_payload}")

# Verify correctness of what decoded should be:
from urllib.parse import unquote
decoded = unquote(url_encoded_payload)
print(f"Decoded: {decoded}")