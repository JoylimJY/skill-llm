#!/bin/bash
# Verify npm docx package is available
npm list -g docx || npm install -g docx
# Create scripts directory structure
mkdir -p scripts/office
# No additional setup needed