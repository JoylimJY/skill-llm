import os
import time
from datetime import datetime, timedelta

os.makedirs('Downloads', exist_ok=True)

# Fixed seed for determinism
def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# Current time
now = datetime(2024, 6, 1, 12, 0, 0)

# Create some PDFs for Work (new files)
pdf_content = "%PDF-1.4 example work document"
write_file('Downloads/report1.pdf', pdf_content)
write_file('Downloads/proposal2.pdf', pdf_content)

# Create some JPG images for Personal (new files)
jpg_content = "JPEG_IMAGE_DATA_marker_Personal_1"
write_file('Downloads/photo1.jpg', jpg_content)
write_file('Downloads/photo2.JPG', jpg_content)  # uppercase extension test

# Create installers (DMG, PKG) (some older than 3 months)
installer_content = "INSTALLER FILE CONTENT"
write_file('Downloads/setup1.dmg', installer_content)
write_file('Downloads/installer_2023.pkg', installer_content)

# Create some old files older than 3 months
old_file_content = "OLD FILE TO ARCHIVE"
write_file('Downloads/old_notes.txt', old_file_content)

# Adjust mtime for old files older than 3 months (older than March 1, 2024)
old_mtime = time.mktime((2024, 2, 15, 10, 0, 0, 0, 0, 0))
os.utime('Downloads/old_notes.txt', (old_mtime, old_mtime))

# Also make installer_2023.pkg old
os.utime('Downloads/installer_2023.pkg', (old_mtime, old_mtime))

# Create a file that doesn't fit categories to go to ToSort
misc_content = "MISC FILE FOR TOSORT"
write_file('Downloads/random.bin', misc_content)

# Make sure timestamps for others are recent
recent_mtime = time.mktime(now.timetuple())
for fname in ['report1.pdf', 'proposal2.pdf', 'photo1.jpg', 'photo2.JPG', 'setup1.dmg', 'random.bin']:
    os.utime(f'Downloads/{fname}', (recent_mtime, recent_mtime))
