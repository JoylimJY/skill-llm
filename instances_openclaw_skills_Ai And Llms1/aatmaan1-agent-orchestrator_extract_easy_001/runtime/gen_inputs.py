#!/usr/bin/env python3
# Deterministic input generator with known marker content
import os
import io

def main():
    random_seed = 12345  # fixed seed for determinism
    # Build a deterministic set of lines, some containing the marker
    lines = [
        "This is a sample line without marker.",
        "MARKER: line with marker at the start.",
        "Another line without the key word.",
        "Line with marker in the middle: MARKER",
        "End of data, no marker here.",
        "Multiple markers MARKER appear MARKER in this line.",
        "marker in lowercase should also match: marker",
        "Standalone line to ignore."
    ]

    # Create input.txt in current directory
    with open("input.txt", "w", encoding="utf-8") as f:
        for i, line in enumerate(lines, 1):
            f.write(line + ("\n" if not line.endswith("\n") else ""))

    # Also produce a marker report for easier debugging (optional, not required by evaluator)
    with open("marker_count.txt", "w", encoding="utf-8") as f:
        f.write(f"Total lines: {len(lines)}\nMarkers in line(s): {sum(1 for l in lines if 'MARKER' in l.upper())}\n")

if __name__ == "__main__":
    main()
