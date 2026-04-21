import os
import random
import shutil
import datetime
from pathlib import Path
from docx import Document
from PIL import Image

random.seed(42)

base_dir = Path('Documents')

# Clean previous runs
if base_dir.exists():
    shutil.rmtree(base_dir)

os.makedirs(base_dir)

# Helper functions
def create_text_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def create_docx(path, title):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph('This is a test DOCX file with marker: {}.'.format(title))
    doc.save(path)


def create_pdf(path, text):
    # We don't use real PDF to avoid bloat, create txt with .pdf extension as marker
    create_text_file(path, f'PDF marker content: {text}')


def create_csv(path, rows):
    with open(path, 'w') as f:
        for r in rows:
            f.write(','.join(r) + '\n')


def create_image(path, text):
    img = Image.new('RGB', (200, 100), color=(73, 109, 137))
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(img)
    d.text((10, 40), text, fill=(255, 255, 0))
    img.save(path)


def set_mtime(file_path, days_ago):
    mod_time = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).timestamp()
    os.utime(file_path, times=(mod_time, mod_time))


# Create a mix of files
WORK_DIR = base_dir / 'work_files'
PERSONAL_DIR = base_dir / 'personal_files'
MISC_DIR = base_dir / 'misc_files'

WORK_DIR.mkdir()
PERSONAL_DIR.mkdir()
MISC_DIR.mkdir()

# Work Reports PDFs and DOCX
for i in range(30):
    fn_pdf = WORK_DIR / f'work_report_{i}.pdf'
    fn_docx = WORK_DIR / f'meeting_notes_{i}.docx'
    create_pdf(fn_pdf, f'Work report number {i}')
    set_mtime(fn_pdf, days_ago=i*10 + 5)
    create_docx(fn_docx, f'Meeting notes {i}')
    set_mtime(fn_docx, days_ago=i*8 + 2)

# Work Projects folders with code files
for i in range(10):
    proj_dir = WORK_DIR / f'project_{i}'
    proj_dir.mkdir()
    # create python files
    for j in range(3):
        code_file = proj_dir / f'module_{j}.py'
        create_text_file(code_file, f'# Python code file for project {i} module {j}')
        set_mtime(code_file, days_ago=i*15+j*5)

# Personal Photos JPG and PNG
PERSONAL_PHOTOS = PERSONAL_DIR / 'photos'
PERSONAL_PHOTOS.mkdir()
for i in range(25):
    img_jpg = PERSONAL_PHOTOS / f'photo_{i}.jpg'
    create_image(img_jpg, f'Photo marker {i}')
    set_mtime(img_jpg, days_ago=i*7 + 1)
    img_png = PERSONAL_PHOTOS / f'photo_{i}_edited.png'
    create_image(img_png, f'Photo edited marker {i}')
    set_mtime(img_png, days_ago=i*10 + 3)

# Personal Financial XLSX and CSV
PERSONAL_FINANCE = PERSONAL_DIR / 'financials'
PERSONAL_FINANCE.mkdir()
for i in range(15):
    csv_file = PERSONAL_FINANCE / f'transactions_{i}.csv'
    create_csv(csv_file, [['Date','Amount','Desc'], ['2024-01-01', str(i*10), f'Transaction {i}']])
    set_mtime(csv_file, days_ago=i*12)

# Miscellaneous files: random txt
for i in range(20):
    misc_txt = MISC_DIR / f'random_note_{i}.txt'
    create_text_file(misc_txt, f'Random note content {i}')
    set_mtime(misc_txt, days_ago=i*20)

# Introduce deliberate duplicates (exact copies) across folders
# Take some existing files and duplicate with same content and dates
import filecmp

def copy_file(src, dst):
    shutil.copy2(src, dst)

existing_files = list(WORK_DIR.glob('*.pdf'))[:3]
for i, f in enumerate(existing_files):
    # Duplicate to PERSONAL_PHOTOS
    copy_file(f, PERSONAL_PHOTOS / f.name)
    # Duplicate to MISC_DIR
    copy_file(f, MISC_DIR / f.name)

existing_code_file = list((WORK_DIR / 'project_0').glob('*.py'))[0]
copy_file(existing_code_file, PERSONAL_DIR / 'duplicate_module.py')

# Create duplicates with same name but different content
fn1 = base_dir / 'dup_test_1.txt'
fn2 = base_dir / 'dup_test_1.txt'
create_text_file(fn1, "Duplicate file content A")
set_mtime(fn1, 10)

# Place a second copy with same name but different folder
dup_folder = base_dir / 'dup_folder'
dup_folder.mkdir()
fn2 = dup_folder / 'dup_test_1.txt'
create_text_file(fn2, "Duplicate file content A")
set_mtime(fn2, 10)

# Create duplicates list file for 'deleting' duplicates
duplicates_to_delete_path = base_dir / 'duplicates_to_delete.txt'
duplicates_to_delete_path.write_text(f"{PERSONAL_PHOTOS / existing_files[0].name}\n{MISC_DIR / existing_files[1].name}\n")

# Create marker original filenames that would be renamed
marker_file = base_dir / '2024-01-01-old_report_FINAL (1).pdf'
create_pdf(marker_file, 'A file marked for renaming')
set_mtime(marker_file, 365)

print('Input generation complete.')
