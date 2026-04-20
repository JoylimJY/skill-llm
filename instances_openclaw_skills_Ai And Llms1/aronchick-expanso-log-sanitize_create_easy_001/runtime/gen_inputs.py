import os
from pathlib import Path

content = """2025-04-12 10:00:00 INFO Starting job
2025-04-12 10:00:01 DEBUG user=alice password=Tr0ub4dor&3 action=login
2025-04-12 10:00:02 INFO token: sk_test_51N9xYabcdef1234567890XYZ requested
2025-04-12 10:00:03 WARN api_key=AKIAIOSFODNN7EXAMPLE retrying
2025-04-12 10:00:04 INFO request completed successfully
"""
Path("input.log").write_text(content, encoding="utf-8")
