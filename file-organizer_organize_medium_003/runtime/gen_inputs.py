import os
import random
import shutil
from datetime import datetime, timedelta
from PIL import Image

random.seed(42)

# Create Downloads folder structure
os.makedirs("Downloads", exist_ok=True)

# Helper to create a text file with marker content
def create_text_file(path, content):
    with open(path, "w") as f:
        f.write(content)

# Helper to create minimal pdf-like text file (mock)
def create_pdf_mock(path, text):
    create_text_file(path, f"%PDF-1.4\n{text}\n%%EOF")

# Create PDFs
pdfs = [
    ("work-proposal.pdf", "Proposal for Q2 Project Work"),
    ("report-final (1).pdf", "Final report download artifact"),
    ("meeting-notes.pdf", "Meeting notes for project discussion"),
    ("old-report.pdf", "Old financial report")
]

for fname, content in pdfs:
    create_pdf_mock(os.path.join("Downloads", fname), content)

# Create images (JPEG/PNG) with marker text
image_fnames = ["vacation01.jpg", "birthday.png", "profile (copy).jpg", "old_photo.png"]

for fname in image_fnames:
    img_path = os.path.join("Downloads", fname)
    img = Image.new('RGB', (100, 100), color = (73, 109, 137))
    img.save(img_path)

# Create installers (DMG, PKG) as empty files with marker
installers = ["app1.dmg", "installer.pkg", "setup (1).dmg"]
for fname in installers:
    path = os.path.join("Downloads", fname)
    create_text_file(path, f"Installer file {fname}")

# Create miscellaneous files
misc_files = ["readme.txt", "todo.txt", "notes copy.txt"]
for fname in misc_files:
    create_text_file(os.path.join("Downloads", fname), f"This is miscellaneous file: {fname}")

# Set modification dates
now = datetime.now()

# Assign last modified dates: some older than 90 days (3 months)
dates = [now - timedelta(days=d) for d in [10, 5, 100, 200, 30, 400, 365, 7, 2, 120, 15, 3, 400, 95, 60]]

all_files = os.listdir("Downloads")
for i, fname in enumerate(sorted(all_files)):
    path = os.path.join("Downloads", fname)
    mod_time = dates[i % len(dates)].timestamp()
    os.utime(path, (mod_time, mod_time))

# Create a duplicate file (exact content) to test duplicate detection
shutil.copyfile(os.path.join("Downloads", 'work-proposal.pdf'), os.path.join("Downloads", "work-proposal-copy.pdf"))

# Create duplicate by name but different content
create_pdf_mock(os.path.join("Downloads", "meeting-notes (copy).pdf"), "Meeting notes different content")

# Finished creating inputs
