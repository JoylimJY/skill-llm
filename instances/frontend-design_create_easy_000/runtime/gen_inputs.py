#!/usr/bin/env python3
import os
import json

# Create a basic requirements file
with open('requirements.txt', 'w') as f:
    f.write('')

# Create a README with business context
with open('README.md', 'w') as f:
    f.write('''# Ember & Oak Coffee Roastery

A small-batch artisanal coffee roastery focused on quality and community.

## Brand Values
- Artisanal craftsmanship
- Small-batch roasting
- Community-focused
- Quality over quantity

## Contact
Email: hello@emberoak.coffee
Phone: (555) 123-BREW
Address: 42 Roaster Lane, Coffee District

<!-- MARKER_CONTENT_BUSINESS_INFO -->
''')

# Create a simple package.json for any potential node dependencies
package_json = {
    "name": "ember-oak-landing",
    "version": "1.0.0",
    "description": "Landing page for Ember & Oak Coffee Roastery",
    "scripts": {
        "start": "python3 -m http.server 8000"
    }
}

with open('package.json', 'w') as f:
    json.dump(package_json, f, indent=2)

print('Generated input files for Ember & Oak coffee roastery landing page')