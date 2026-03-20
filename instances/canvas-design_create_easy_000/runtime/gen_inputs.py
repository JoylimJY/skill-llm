#!/usr/bin/env python3
import os

# Create a simple text file with event details that could inspire the design
with open('event_brief.txt', 'w') as f:
    f.write('JAZZ_NIGHT_EVENT_MARKER_12345\n')
    f.write('Coffee & Jazz Evening\n')
    f.write('Every Thursday 7-10 PM\n')
    f.write('The Grind Coffee House\n')
    f.write('Live music, artisan coffee, cozy atmosphere\n')

print('Created event brief file')