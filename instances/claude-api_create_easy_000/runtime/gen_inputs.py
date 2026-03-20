#!/usr/bin/env python3
import os

# Create a mock .env file with test API key
with open('.env', 'w') as f:
    f.write('ANTHROPIC_API_KEY=test-key-12345\n')

# Create marker file for evaluation
with open('task_marker.txt', 'w') as f:
    f.write('TASK_MARKER: Create chat app with Claude API\n')
    f.write('Expected output: chat_log.txt with haiku request/response\n')

print('Input files generated successfully')