import os

# Create a simple requirements marker file
with open('brand_requirements.txt', 'w') as f:
    f.write('BRAND_MARKER_ANTHROPIC\n')
    f.write('Colors: Dark #141413, Light #faf9f5, Orange #d97757, Blue #6a9bcc, Green #788c5d\n')
    f.write('Fonts: Poppins for headings, Lora for body text\n')
    f.write('BRAND_MARKER_END\n')

print('Generated brand requirements file')