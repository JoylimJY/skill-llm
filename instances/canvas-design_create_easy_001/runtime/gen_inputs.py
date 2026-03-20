#!/usr/bin/env python3
import os

# Create a simple request file to simulate user input
with open('request.txt', 'w') as f:
    f.write('Create a minimalist poster for a coffee shop called Dawn Ritual')
    f.write('\nRequirements: clean, artistic, meditative morning coffee theme')
    f.write('\nMarker: COFFEE_POSTER_REQUEST_V1')

print('Generated input request file')