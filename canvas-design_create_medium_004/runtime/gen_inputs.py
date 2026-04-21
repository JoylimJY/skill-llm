import os
import json

# Create a simple reference file for mathematical beauty concepts
math_concepts = {
    "golden_ratio": 1.618,
    "fibonacci_sequence": [1, 1, 2, 3, 5, 8, 13, 21, 34, 55],
    "prime_numbers": [2, 3, 5, 7, 11, 13, 17, 19, 23, 29],
    "geometric_forms": ["circle", "triangle", "square", "pentagon", "hexagon"]
}

with open('math_reference.json', 'w') as f:
    json.dump(math_concepts, f, indent=2)

# Create a simple text file with mathematical quotes
quotes = [
    "Mathematics is the music of reason - James Joseph Sylvester",
    "Pure mathematics is the poetry of logical ideas - Albert Einstein", 
    "In mathematics, the art of asking questions is more valuable than solving problems - Georg Cantor"
]

with open('inspiration.txt', 'w') as f:
    for quote in quotes:
        f.write(quote + '\n')

print("Input files generated successfully")