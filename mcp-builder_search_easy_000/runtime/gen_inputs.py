import os

# This task requires no input files created by the user.
# But we generate a fixed marker text file to verify the evaluation environment.

with open("MARKER.txt", "w", encoding="utf-8") as f:
    f.write("example_mcp evaluation marker file - deterministic content\n")

print("Input files generated.")
