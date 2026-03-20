#!/bin/bash
# Download and install Poppins and Lora fonts for proper brand styling
mkdir -p /usr/share/fonts/truetype/custom
cd /usr/share/fonts/truetype/custom

# Note: In a real scenario, you would download the actual font files
# For this demo, we'll ensure the fallback fonts are available
fc-cache -fv