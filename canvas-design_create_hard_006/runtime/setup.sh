#!/bin/bash
# Update font cache
fc-cache -f -v
# Ensure all necessary directories exist
mkdir -p /tmp/canvas-fonts
echo 'Setup complete'