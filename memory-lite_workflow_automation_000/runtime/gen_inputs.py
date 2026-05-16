import os
import random
import string
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "docs/hardware/schematics",
    "docs/hardware/bom",
    "docs/software/drivers",
    "docs/software/protocols",
    "src/hal/gpio",
    "src/hal/uart",
    "src/rtos/tasks",
    "tests/unit",
    "tests/integration",
    "build/artifacts",
    "config/boards",
    "scripts",           # required by skill
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "docs/hardware/schematics/rev3_notes.txt": "Rev3 schematic: added decoupling caps on VCC rail.\n",
    "docs/hardware/bom/components.csv": "part_id,description,qty\nC1,100nF cap,10\nR1,10k resistor,5\n",
    "docs/software/drivers/uart_driver.c": "/* UART driver v2 */\nvoid uart_init(void) {}\n",
    "docs/software/protocols/i2c_spec.md": "# I2C Protocol\nSpeed: 400kHz, address: 0x3C\n",
    "src/hal/gpio/gpio.h": "#ifndef GPIO_H\n#define GPIO_H\nvoid gpio_set(int pin, int val);\n#endif\n",
    "src/hal/uart/uart.h": "#ifndef UART_H\n#define UART_H\nvoid uart_send(char *buf);\n#endif\n",
    "src/rtos/tasks/scheduler.c": "/* Preemptive scheduler */\nvoid scheduler_run(void) {}\n",
    "tests/unit/test_gpio.py": "def test_gpio_toggle():\n    assert True\n",
    "tests/integration/test_boot.sh": "#!/bin/bash\necho 'boot test passed'\n",
    "build/artifacts/firmware.bin": "FAKE_BINARY_BLOB_v1.2.3\n",
    "config/boards/stm32f4.yaml": "board: stm32f4\nflash: 1MB\nram: 192KB\n",
    "config/boards/esp32.yaml": "board: esp32\nflash: 4MB\nram: 520KB\n",
}
for rel_path, content in distractors.items():
    p = workspace / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── scripts/ — the three skill scripts (stubs that actually work) ────────────
# memory_add.py
memory_add = '''#!/usr/bin/env python3
"""memory_add.py — append notes to daily or long-term memory files."""
import argparse
import os
from datetime import date
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=["daily", "long"],
                        help="'daily' writes to memory/YYYY-MM-DD.md; 'long' writes to MEMORY.md")
    parser.add_argument("--text", required=True, help="Text to append")
    args = parser.parse_args()

    if args.kind == "daily":
        mem_dir = Path("memory")
        mem_dir.mkdir(exist_ok=True)
        target = mem_dir / f"{date.today().isoformat()}.md"
        with open(target, "a") as f:
            f.write(f"- {args.text}\\n")
        print(f"Appended daily note to {target}")
    else:
        target = Path("MEMORY.md")
        with open(target, "a") as f:
            f.write(f"- {args.text}\\n")
        print(f"Appended long-term note to {target}")

if __name__ == "__main__":
    main()
'''

# memory_grep.sh
memory_grep = '''#!/usr/bin/env bash
# memory_grep.sh — keyword search across all memory files
KEYWORD="$1"
if [ -z "$KEYWORD" ]; then
    echo "Usage: bash scripts/memory_grep.sh <keyword>" >&2
    exit 1
fi
echo "=== Searching memory files for: $KEYWORD ==="
found=0
for f in memory/*.md MEMORY.md; do
    [ -f "$f" ] || continue
    if grep -i "$KEYWORD" "$f"; then
        found=1
    fi
done
if [ "$found" -eq 0 ]; then
    echo "(no matches)"
fi
'''

# memory_summarize.py
memory_summarize = '''#!/usr/bin/env python3
"""memory_summarize.py — quick local heuristic summary of recent memory."""
import argparse
from datetime import date, timedelta
from pathlib import Path

def summarize(days: int) -> str:
    lines = ["# Memory Summary", ""]
    today = date.today()
    for i in range(days):
        d = today - timedelta(days=i)
        fpath = Path("memory") / f"{d.isoformat()}.md"
        if fpath.exists():
            lines.append(f"## {d.isoformat()}")
            content = fpath.read_text().strip()
            if content:
                lines.append(content)
            else:
                lines.append("(no entries)")
            lines.append("")
    # include long-term memory headings
    ltm = Path("MEMORY.md")
    if ltm.exists():
        lines.append("## Long-term notes")
        for line in ltm.read_text().splitlines():
            if line.startswith("- ") or line.startswith("#"):
                lines.append(line)
        lines.append("")
    return "\\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, required=True,
                        help="Number of recent days to include")
    args = parser.parse_args()
    print(summarize(args.days))

if __name__ == "__main__":
    main()
'''

(workspace / "scripts" / "memory_add.py").write_text(memory_add)
(workspace / "scripts" / "memory_grep.sh").write_text(memory_grep)
(workspace / "scripts" / "memory_summarize.py").write_text(memory_summarize)

print("Workspace scaffold complete.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")