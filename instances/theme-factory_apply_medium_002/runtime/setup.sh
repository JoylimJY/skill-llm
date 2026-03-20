#!/bin/bash

# Start virtual display for wkhtmltopdf
Xvfb :99 -screen 0 1024x768x24 &
sleep 2

# Install additional fonts
fc-cache -f -v