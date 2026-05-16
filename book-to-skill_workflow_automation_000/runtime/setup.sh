#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying book file exists..."
if [ -f "/workspace/library/imported/2024/the_pomodoro_technique.txt" ]; then
    echo "Book file found. Word count: $(wc -w < /workspace/library/imported/2024/the_pomodoro_technique.txt) words"
else
    echo "ERROR: Book file not found!"
    exit 1
fi

echo "Setup complete."