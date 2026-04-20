from pathlib import Path

# Deterministic marker input for evaluation
marker = "ROCKET_TASK_MARKER_V1"
Path("description.txt").write_text(
    "Create a low-poly rocket with a round nose cone, two side fins, and a cylindrical engine nozzle.\n"
    f"MARKER:{marker}\n",
    encoding="utf-8",
)
