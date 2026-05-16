import os
import stat

# Create directory structure
workspace = "/workspace"
dirs = [
    "scripts",
    "logs",
    "reports",
    "tests/unit",
    "tests/integration",
    "docs/api",
    "docs/design",
    "config",
    "data/samples",
    "data/fixtures",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Create the actual guess_number.py script ---
# This is the real implementation as described by SKILL.md
# It supports GUESS_SEED env var for deterministic testing
guess_number_script = r'''#!/usr/bin/env python3
import sys
import os
import random
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_FILE = os.path.join(SCRIPT_DIR, "secret.txt")
STEPS_FILE = os.path.join(SCRIPT_DIR, "steps.txt")

def generate():
    seed_val = os.environ.get("GUESS_SEED")
    if seed_val is not None:
        random.seed(int(seed_val))
    digits = list("0123456789")
    random.shuffle(digits)
    secret = "".join(digits[:4])
    with open(SECRET_FILE, "w") as f:
        f.write(secret)
    with open(STEPS_FILE, "w") as f:
        f.write("0")
    print("我已想好一个四位数（各位数字互不相同），请开始猜测！")

def verify(guess):
    if not os.path.exists(SECRET_FILE):
        print("游戏尚未开始，请先开始游戏。")
        return

    # Input validation
    if len(guess) != 4:
        print("请输入4位数字，请重新输入")
        return

    if not guess.isdigit():
        print("只能输入数字，请重新输入")
        return

    if len(set(guess)) != 4:
        print("数字不能重复，请重新输入")
        return

    # Read steps
    with open(STEPS_FILE, "r") as f:
        steps = int(f.read().strip())
    steps += 1
    with open(STEPS_FILE, "w") as f:
        f.write(str(steps))

    # Read secret
    with open(SECRET_FILE, "r") as f:
        secret = f.read().strip()

    # Count correct positions
    k = sum(1 for i in range(4) if guess[i] == secret[i])

    if k == 4:
        print(f"反馈：4 个数字位置正确！恭喜你猜对了！总共用了 {steps} 步。")
        os.remove(SECRET_FILE)
        os.remove(STEPS_FILE)
    else:
        print(f"反馈：{k} 个数字位置正确")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--verify", type=str, default=None)
    args = parser.parse_args()

    if args.generate:
        generate()
    elif args.verify is not None:
        verify(args.verify)
    else:
        print("请指定 --generate 或 --verify <4位数字>")
'''

script_path = os.path.join(workspace, "scripts", "guess_number.py")
with open(script_path, "w") as f:
    f.write(guess_number_script)
os.chmod(script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# --- Distractor files ---

# logs/
with open(os.path.join(workspace, "logs", "server.log"), "w") as f:
    f.write("2024-01-15 10:23:11 INFO Server started\n2024-01-15 10:23:12 INFO Listening on port 8080\n")

with open(os.path.join(workspace, "logs", "error.log"), "w") as f:
    f.write("2024-01-15 10:25:00 ERROR Connection timeout\n")

# reports/ (empty, agent should create game_report.json here or anywhere)
with open(os.path.join(workspace, "reports", ".gitkeep"), "w") as f:
    f.write("")

# tests/unit/
with open(os.path.join(workspace, "tests", "unit", "test_input_validation.py"), "w") as f:
    f.write("# Placeholder unit tests for input validation\n# TODO: implement\n")

with open(os.path.join(workspace, "tests", "integration", "test_game_flow.py"), "w") as f:
    f.write("# Integration test scaffold\n# Expected: full game session from start to finish\n")

# docs/
with open(os.path.join(workspace, "docs", "api", "endpoints.md"), "w") as f:
    f.write("# API Endpoints\n\n- POST /game/start\n- POST /game/guess\n")

with open(os.path.join(workspace, "docs", "design", "architecture.md"), "w") as f:
    f.write("# Architecture\n\nThe game engine uses a two-phase approach.\n")

# config/
with open(os.path.join(workspace, "config", "game_config.json"), "w") as f:
    import json
    json.dump({"max_attempts": 20, "digit_count": 4, "allow_leading_zero": True}, f, indent=2)

# data/samples/
with open(os.path.join(workspace, "data", "samples", "sample_session.txt"), "w") as f:
    f.write("Sample guess: 1234 -> 1 correct\nSample guess: 5678 -> 0 correct\n")

with open(os.path.join(workspace, "data", "fixtures", "known_secrets.txt"), "w") as f:
    f.write("# These are NOT the actual secret numbers used in tests\n1234\n5678\n9012\n")

# A misleading file that looks like a report template but is incomplete
with open(os.path.join(workspace, "reports", "report_template.txt"), "w") as f:
    f.write("Session Report\n==============\nDate: ???\nResult: ???\nSteps: ???\n")

# scripts/utils.py (distractor)
with open(os.path.join(workspace, "scripts", "utils.py"), "w") as f:
    f.write("# Utility functions placeholder\ndef validate_digit_string(s):\n    pass\n")

print("Workspace initialized successfully.")
print("Note: With GUESS_SEED=42, the generated secret will be deterministic.")

# Compute what the secret will be with seed=42 for our reference
import random as _r
_r.seed(42)
digits = list("0123456789")
_r.shuffle(digits)
secret_preview = "".join(digits[:4])
print(f"[SETUP INFO] With GUESS_SEED=42, secret will be: {secret_preview}")