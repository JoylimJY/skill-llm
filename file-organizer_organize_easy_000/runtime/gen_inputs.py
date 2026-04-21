import os

os.makedirs('Downloads', exist_ok=True)

# Create PDFs
with open('Downloads/report1.pdf', 'w') as f:
    f.write('PDF file report 1 - unique marker A1')
with open('Downloads/report2.pdf', 'w') as f:
    f.write('PDF file report 2 - unique marker A2')
# Duplicate PDF
with open('Downloads/copy_of_report1.pdf', 'w') as f:
    f.write('PDF file report 1 - unique marker A1')

# Create images
with open('Downloads/photo1.png', 'w') as f:
    f.write('PNG image photo1 - unique marker B1')
with open('Downloads/photo2.jpg', 'w') as f:
    f.write('JPG image photo2 - unique marker B2')
# Duplicate image
with open('Downloads/photo1_duplicate.png', 'w') as f:
    f.write('PNG image photo1 - unique marker B1')

# Create DMG installer files
with open('Downloads/installer1.dmg', 'w') as f:
    f.write('DMG Installer 1 - unique marker C1')
with open('Downloads/installer2.dmg', 'w') as f:
    f.write('DMG Installer 2 - unique marker C2')

# Create a random other file to remain untouched
with open('Downloads/random.txt', 'w') as f:
    f.write('Some random text file - unique marker D1')
