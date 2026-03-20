#!/bin/bash
# Download and install Anthropic brand fonts if available
wget -q https://fonts.google.com/download?family=Poppins -O poppins.zip 2>/dev/null || true
wget -q https://fonts.google.com/download?family=Lora -O lora.zip 2>/dev/null || true

if [ -f poppins.zip ]; then
    unzip -q poppins.zip -d /usr/share/fonts/truetype/ 2>/dev/null || true
fi

if [ -f lora.zip ]; then
    unzip -q lora.zip -d /usr/share/fonts/truetype/ 2>/dev/null || true
fi

fc-cache -f 2>/dev/null || true
echo "Font setup completed"