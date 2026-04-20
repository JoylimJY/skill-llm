from pathlib import Path
import base64
import json

root = Path('.')

handshake_payload = {
    "protocol": "agent-lingua",
    "version": "0.4.0",
    "spec": "clawhub.ai/xiwan/agent-linguo",
    "capabilities": ["1", "7", "A"],
    "security": ["P", "B", "E"],
    "crypto": ["X25519+AES-GCM", "PSK+AES-GCM"],
    "pubkey": "MCowBQYDK2VwAyEADETERMINISTICMARKERKEY1234567890"
}
handshake_b64 = base64.b64encode(json.dumps(handshake_payload, separators=(",", ":")).encode()).decode()

message_payload = {"t":"agent report","c":"deterministic marker alpha-42"}
message_b64 = base64.b64encode(json.dumps(message_payload, separators=(",", ":")).encode()).decode()

files = {
    "inbox_1.txt": f"noise line\n👽09|$j:{handshake_b64}\n--👽lingua/0.4@agent-lingua\n",
    "inbox_2.txt": f"👽73|@1|$j:{message_b64}\n--👽lingua/0.4@agent-lingua\n",
    "notes.txt": "This workspace contains the marker DETERMISTIC-MARKER-ALPHA and the session may be s123456.\n",
}

for name, content in files.items():
    Path(name).write_text(content, encoding='utf-8')
