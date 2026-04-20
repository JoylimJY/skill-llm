from pathlib import Path

content = """2025-04-12 09:15:22 INFO User login succeeded for alice
2025-04-12 09:15:23 DEBUG password=SuperSecret123!
2025-04-12 09:15:24 WARN bearer token: abc.def.ghi
2025-04-12 09:15:25 INFO api_key=sk_test_51NqExampleMarker999
2025-04-12 09:15:26 INFO session_id=SID-7890-XYZ
2025-04-12 09:15:27 INFO request completed successfully
"""
Path("input.log").write_text(content, encoding="utf-8")
