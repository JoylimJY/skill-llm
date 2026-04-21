import os

# Create a simple canvas-fonts directory with font listings
os.makedirs('canvas-fonts', exist_ok=True)

# Create a font listing file
with open('canvas-fonts/available_fonts.txt', 'w') as f:
    f.write("Available Fonts:\n")
    f.write("- Liberation Sans\n")
    f.write("- Liberation Serif\n")
    f.write("- DejaVu Sans\n")
    f.write("- DejaVu Serif\n")
    f.write("- Noto Sans\n")
    f.write("- Noto Serif\n")

print("Input files generated successfully")