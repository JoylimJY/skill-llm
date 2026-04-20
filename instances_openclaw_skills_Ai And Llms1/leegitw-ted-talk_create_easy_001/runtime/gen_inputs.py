# No input files needed for this task — the prompt itself is the input
import os
with open('context.txt', 'w') as f:
    f.write('MARKER_INSIGHT: error messages are a user interface\n')
    f.write('MARKER_EXAMPLE: operation failed vs database connection timeout after 30s retried 3 times\n')
    f.write('MARKER_IMPACT: 3 hours of debugging time lost\n')
print('context.txt written')
