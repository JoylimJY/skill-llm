#!/usr/bin/env python3

import os

# Create a simple reference file with company info
with open('company_info.txt', 'w') as f:
    f.write("TechCorp Financial Model Requirements\n")
    f.write("Base Year: 2024\n")
    f.write("Revenue: $50M\n")
    f.write("Growth Rate: 15%\n")
    f.write("EBITDA Margin: 25% (improving 100bps annually)\n")
    f.write("Tax Rate: 25%\n")
    f.write("WACC: 12%\n")
    f.write("Terminal Growth: 3%\n")
    f.write("Model Type: DCF Analysis\n")
    f.write("MARKER_CONTENT: DCF_MODEL_TECHCORP_2024\n")

print("Generated company_info.txt with DCF model requirements")