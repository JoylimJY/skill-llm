import os
import random

# Set deterministic seed
random.seed(42)

# Create a simple reference file about digital archaeology concepts
with open('digital_concepts.txt', 'w') as f:
    f.write("Digital Archaeology Concepts:\n")
    f.write("- Obsolete file formats: .fla, .sit, .sea\n")
    f.write("- Vintage interfaces: skeuomorphic design, CRT aesthetics\n")
    f.write("- Lost software: HyperCard, Director, early web browsers\n")
    f.write("- Digital decay: link rot, format migration, emulation\n")
    f.write("- Archaeology markers: pixel artifacts, compression noise\n")

print("Generated digital archaeology reference file.")