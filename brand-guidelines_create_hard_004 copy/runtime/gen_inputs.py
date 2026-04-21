import os

# Create a simple requirements file for reference
with open('requirements.txt', 'w') as f:
    f.write('python-pptx>=0.6.21\n')

# Create a brand reference document
with open('brand_reference.md', 'w') as f:
    f.write('# Anthropic Brand Reference\n\n')
    f.write('## Colors\n')
    f.write('- Dark: #141413\n')
    f.write('- Light: #faf9f5\n')
    f.write('- Orange: #d97757\n')
    f.write('- Blue: #6a9bcc\n')
    f.write('- Green: #788c5d\n\n')
    f.write('## Typography\n')
    f.write('- Headings: Poppins\n')
    f.write('- Body: Lora\n')

print('Generated input files successfully')