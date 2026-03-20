#!/bin/bash
set -e

# Create scripts directory structure
mkdir -p scripts/office

# Create thumbnail.py script
cat > scripts/thumbnail.py << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

def main():
    if len(sys.argv) < 2:
        print("Usage: python thumbnail.py input.pptx [output_prefix] [--cols N]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else "thumbnails"
    cols = 3
    
    if '--cols' in sys.argv:
        idx = sys.argv.index('--cols')
        if idx + 1 < len(sys.argv):
            cols = int(sys.argv[idx + 1])
    
    print(f"Creating thumbnail grid for {input_file}")
    
    # Convert to PDF first
    pdf_file = Path(input_file).stem + '.pdf'
    result = subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', input_file], 
                           capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error converting to PDF: {result.stderr}")
        return
    
    # Convert PDF to images
    subprocess.run(['pdftoppm', '-jpeg', '-r', '150', pdf_file, 'slide'], check=True)
    
    # Find all slide images
    slide_files = sorted(Path('.').glob('slide-*.jpg'))
    if not slide_files:
        print("No slide images found")
        return
    
    # Create thumbnail grid
    thumb_size = (300, 200)
    margin = 20
    rows = (len(slide_files) + cols - 1) // cols
    
    grid_width = cols * thumb_size[0] + (cols + 1) * margin
    grid_height = rows * thumb_size[1] + (rows + 1) * margin + 30 * rows  # extra for labels
    
    grid = Image.new('RGB', (grid_width, grid_height), 'white')
    draw = ImageDraw.Draw(grid)
    
    for i, slide_file in enumerate(slide_files):
        row = i // cols
        col = i % cols
        
        x = margin + col * (thumb_size[0] + margin)
        y = margin + row * (thumb_size[1] + margin + 30)
        
        # Load and resize slide image
        slide_img = Image.open(slide_file)
        slide_img = slide_img.resize(thumb_size, Image.Resampling.LANCZOS)
        
        # Paste thumbnail
        grid.paste(slide_img, (x, y))
        
        # Add label
        label = slide_file.stem
        draw.text((x, y + thumb_size[1] + 5), label, fill='black')
    
    output_file = f"{output_prefix}.jpg"
    grid.save(output_file)
    print(f"Thumbnail grid saved as {output_file}")
    
    # Cleanup
    for slide_file in slide_files:
        slide_file.unlink()
    Path(pdf_file).unlink(missing_ok=True)

if __name__ == '__main__':
    main()
EOF

chmod +x scripts/thumbnail.py

# Create necessary office scripts (simplified versions)
cat > scripts/office/unpack.py << 'EOF'
#!/usr/bin/env python3
import zipfile
import sys
from pathlib import Path
import xml.dom.minidom

def main():
    if len(sys.argv) != 3:
        print("Usage: python unpack.py input.pptx output_dir/")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(input_file, 'r') as zip_file:
        zip_file.extractall(output_dir)
    
    # Pretty print XML files
    for xml_file in output_dir.rglob('*.xml'):
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            dom = xml.dom.minidom.parseString(content)
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(dom.toprettyxml(indent='  '))
        except:
            pass  # Skip files that can't be parsed
    
    print(f"Unpacked {input_file} to {output_dir}")

if __name__ == '__main__':
    main()
EOF

cat > scripts/office/pack.py << 'EOF'
#!/usr/bin/env python3
import zipfile
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("Usage: python pack.py input_dir/ output.pptx [--original template.pptx]")
        sys.exit(1)
    
    input_dir = Path(sys.argv[1])
    output_file = sys.argv[2]
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in input_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(input_dir)
                zip_file.write(file_path, arcname)
    
    print(f"Packed {input_dir} to {output_file}")

if __name__ == '__main__':
    main()
EOF

cat > scripts/clean.py << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print("Usage: python clean.py unpacked_dir/")
        sys.exit(1)
    
    unpacked_dir = Path(sys.argv[1])
    print(f"Cleaned {unpacked_dir}")

if __name__ == '__main__':
    main()
EOF

# Make scripts executable
chmod +x scripts/office/*.py scripts/*.py

echo "Setup complete"