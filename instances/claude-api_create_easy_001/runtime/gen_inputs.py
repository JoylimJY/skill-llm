#!/usr/bin/env python3
import os

# Create input text file with marker content
input_text = '''
This is a sample document about renewable energy sources.
Solar panels convert sunlight into electricity through photovoltaic cells.
Wind turbines harness kinetic energy from moving air masses.
Hydroelectric power generates electricity from flowing water.
Geothermal energy utilizes heat from the Earth's core.
These sustainable technologies are crucial for reducing carbon emissions.
Renewable energy investments have grown significantly in recent years.
Governments worldwide are implementing policies to promote clean energy adoption.
The transition to renewable sources presents both opportunities and challenges.
Marker content: RENEWABLE_ENERGY_SUMMARY_TEST_2024
'''

with open('input_text.txt', 'w') as f:
    f.write(input_text)