import os
import random
import time
from datetime import datetime, timedelta

random.seed(42)

folder = 'Downloads'
os.makedirs(folder, exist_ok=True)

# Create PDF, DOCX, TXT files
documents = [
    ('report1.pdf', 'PDF content report 1'),
    ('notes.docx', 'DOCX content notes'),
    ('todo.txt', 'TXT content todo list')
]

# Create image files JPG, PNG
images = [
    ('photo1.jpg', 'JPG image marker 1'),
    ('diagram.png', 'PNG graphic diagram')
]

# Installer files DMG, PKG
installers = [
    ('app.dmg', 'DMG installer file'),
    ('setup.pkg', 'PKG installer file')
]

# Other files to be archived (not matching above)
archives = [
    ('old_data.csv', 'Old CSV data to archive'),
    ('legacy.zip', 'Old ZIP archive'),
    ('readme.md', 'README markdown file')
]

# Create files
all_files = documents + images + installers + archives

now = time.time()
four_months_ago = now - (4 * 30 * 24 * 3600)  # approx

for i, (fname, content) in enumerate(all_files):
    path = os.path.join(folder, fname)
    with open(path, 'w') as f:
        f.write(content + f' [MARKER {fname}]')

    # Set modification time for archives older than 4 months, others recent
    if fname in [a[0] for a in archives]:
        mod_time = four_months_ago - (i * 1000)  # Just older than 4 months
    else:
        mod_time = now - (i * 1000)  # recent
    os.utime(path, (mod_time, mod_time))

# Create a conflicting filename in Documents to test rename handling
conflict_name = 'notes.docx'
conflict_path = os.path.join(folder, conflict_name)
with open(conflict_path + '.backup', 'w') as f:
    f.write('Backup conflicting file content [MARKER conflict]')

# Also create a 'notes.docx' inside Downloads directly again to test conflict
with open(conflict_path, 'w') as f:
    f.write('Original notes docx duplicate')

os.utime(conflict_path + '.backup', (now - 5000, now - 5000))
