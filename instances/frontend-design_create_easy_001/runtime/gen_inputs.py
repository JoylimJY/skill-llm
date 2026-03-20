#!/usr/bin/env python3
import os
import json

# Create basic requirements file
with open('requirements.txt', 'w') as f:
    f.write('''Coffee Shop: Brew & Bean
Location: 123 Main Street, Downtown
Hours: Mon-Fri 7am-7pm, Sat-Sun 8am-6pm
Menu Items:
- Espresso - $3.50
- Cappuccino - $4.25
- Latte - $4.75
- Americano - $3.25
- Cold Brew - $4.00
- Pastries - $2.50-$5.00

Special: "DAILY_SPECIAL_MARKER_12345"
Contact: info@brewandbean.com
Phone: (555) 123-4567''')

print('Generated coffee shop requirements file')