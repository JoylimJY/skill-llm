import os
import random
from datetime import datetime, timedelta
from PIL import Image

random.seed(42)

os.makedirs('Downloads', exist_ok=True)

# Helper to create text files with sample content
 def write_text_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# Helper to create dummy images
 def create_image(path, color, size=(100, 100)):
    img = Image.new('RGB', size, color=color)
    img.save(path)

# Create varied files inside Downloads
files_info = []
now = datetime(2024, 6, 1, 12, 0, 0)

# 1. Work documents (pdf, docx, txt)
work_docs = [
    ('project_proposal.pdf', b'%PDF-1.4 Dummy PDF Content'),
    ('meeting_notes.txt', 'Meeting notes for project kickoff...'),
    ('budget.xlsx', 'XLSX fake content placeholder'),
]

for fname, content in work_docs:
    fpath = os.path.join('Downloads', fname)
    if isinstance(content, bytes):
        with open(fpath, 'wb') as f:
            f.write(content)
    else:
        write_text_file(fpath, content)
    # Set modification date to now - 10 days
    mod_time = now - timedelta(days=10)
    os.utime(fpath, (mod_time.timestamp(), mod_time.timestamp()))
    files_info.append((fpath, mod_time))

# 2. Personal photos (jpg/png)
colors = ['red', 'green', 'blue']
photo_names = ['vacation1.jpg', 'birthday.png', 'sunset.jpg']
for i, name in enumerate(photo_names):
    path = os.path.join('Downloads', name)
    create_image(path, colors[i])
    mod_time = now - timedelta(days=30 + i*5)
    os.utime(path, (mod_time.timestamp(), mod_time.timestamp()))
    files_info.append((path, mod_time))

# 3. Installers (dmg, pkg)
installers = ['app1.dmg', 'tool.pkg']
for i, name in enumerate(installers):
    path = os.path.join('Downloads', name)
    # Just empty files
    with open(path, 'wb') as f:
        f.write(b'')
    mod_time = now - timedelta(days=100 + i*10)
    os.utime(path, (mod_time.timestamp(), mod_time.timestamp()))
    files_info.append((path, mod_time))

# 4. Old project zips
old_projects = ['old_project_v1.zip', 'old_project_v2.zip']
for i, name in enumerate(old_projects):
    path = os.path.join('Downloads', name)
    write_text_file(path, f'Archive content for {name}')
    mod_time = now - timedelta(days=250 + i*20)
    os.utime(path, (mod_time.timestamp(), mod_time.timestamp()))
    files_info.append((path, mod_time))

# 5. Random files
random_files = ['readme.txt', 'script.py', 'document-final-v2 (1).pdf']
for name in random_files:
    path = os.path.join('Downloads', name)
    write_text_file(path, f'Content of {name}')
    mod_time = now - timedelta(days=random.randint(1, 400))
    os.utime(path, (mod_time.timestamp(), mod_time.timestamp()))
    files_info.append((path, mod_time))

# 6. Create duplicates - exact copy of some files in subfolders
os.makedirs(os.path.join('Downloads', 'dup_folder'), exist_ok=True)
duplicate_sources = ['project_proposal.pdf', 'vacation1.jpg', 'old_project_v1.zip']
for fname in duplicate_sources:
    src_path = os.path.join('Downloads', fname)
    dest_path = os.path.join('Downloads', 'dup_folder', fname)
    with open(src_path, 'rb') as fsrc, open(dest_path, 'wb') as fdst:
        fdst.write(fsrc.read())
    # Set same mod time
    mod_time = now - timedelta(days=10)
    os.utime(dest_path, (mod_time.timestamp(), mod_time.timestamp()))

# 7. Another duplicate with different mod time
src_path = os.path.join('Downloads', 'meeting_notes.txt')
dest_path = os.path.join('Downloads', 'meeting_notes_copy.txt')
with open(src_path, 'rb') as fsrc, open(dest_path, 'wb') as fdst:
    fdst.write(fsrc.read())
mod_time = now - timedelta(days=5)
os.utime(dest_path, (mod_time.timestamp(), mod_time.timestamp()))

# Write a manifest of generated files with mod times
with open('Downloads/.manifest.txt', 'w') as f:
    for path, mod_time in files_info:
        f.write(f'{path}	{mod_time.isoformat()}\n')

