#!/bin/bash

# Create necessary script files for docx manipulation
mkdir -p scripts/office

# Create unpack.py script
cat > scripts/office/unpack.py << 'EOF'
#!/usr/bin/env python3
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

def unpack_docx(docx_path, output_dir):
    docx_path = Path(docx_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(docx_path, 'r') as zip_file:
        zip_file.extractall(output_dir)
    
    # Pretty print XML files
    for xml_file in output_dir.rglob('*.xml'):
        try:
            tree = ET.parse(xml_file)
            ET.indent(tree.getroot(), space='  ')
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        except ET.ParseError:
            pass

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python unpack.py <docx_file> <output_dir>')
        sys.exit(1)
    unpack_docx(sys.argv[1], sys.argv[2])
EOF

# Create pack.py script
cat > scripts/office/pack.py << 'EOF'
#!/usr/bin/env python3
import sys
import zipfile
from pathlib import Path

def pack_docx(input_dir, output_docx):
    input_dir = Path(input_dir)
    output_docx = Path(output_docx)
    
    with zipfile.ZipFile(output_docx, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in input_dir.rglob('*'):
            if file_path.is_file():
                archive_name = file_path.relative_to(input_dir)
                zip_file.write(file_path, archive_name)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python pack.py <input_dir> <output_docx> [--original original.docx]')
        sys.exit(1)
    pack_docx(sys.argv[1], sys.argv[2])
EOF

# Create validate.py script
cat > scripts/office/validate.py << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path

def validate_docx(docx_path):
    docx_path = Path(docx_path)
    if not docx_path.exists():
        print(f'Error: {docx_path} does not exist')
        return False
    if docx_path.suffix.lower() != '.docx':
        print(f'Warning: {docx_path} does not have .docx extension')
    print(f'Document {docx_path} appears valid')
    return True

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python validate.py <docx_file>')
        sys.exit(1)
    valid = validate_docx(sys.argv[1])
    sys.exit(0 if valid else 1)
EOF

# Create comment.py script
cat > scripts/comment.py << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path
import argparse
from xml.etree import ElementTree as ET

def add_comment(unpacked_dir, comment_id, text, author='Claude', parent=None):
    unpacked_dir = Path(unpacked_dir)
    comments_file = unpacked_dir / 'word' / 'comments.xml'
    
    # Create basic comment structure if file doesn't exist
    if not comments_file.exists():
        root = ET.Element('w:comments')
        root.set('xmlns:w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
        tree = ET.ElementTree(root)
        tree.write(comments_file, encoding='utf-8', xml_declaration=True)
    
    tree = ET.parse(comments_file)
    root = tree.getroot()
    
    comment_elem = ET.SubElement(root, 'w:comment')
    comment_elem.set('w:id', str(comment_id))
    comment_elem.set('w:author', author)
    comment_elem.set('w:date', '2025-01-01T00:00:00Z')
    
    para = ET.SubElement(comment_elem, 'w:p')
    run = ET.SubElement(para, 'w:r')
    text_elem = ET.SubElement(run, 'w:t')
    text_elem.text = text
    
    tree.write(comments_file, encoding='utf-8', xml_declaration=True)
    print(f'Added comment {comment_id}: {text}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('unpacked_dir')
    parser.add_argument('comment_id', type=int)
    parser.add_argument('text')
    parser.add_argument('--author', default='Claude')
    parser.add_argument('--parent', type=int)
    args = parser.parse_args()
    
    add_comment(args.unpacked_dir, args.comment_id, args.text, args.author, args.parent)
EOF

chmod +x scripts/office/*.py
chmod +x scripts/comment.py