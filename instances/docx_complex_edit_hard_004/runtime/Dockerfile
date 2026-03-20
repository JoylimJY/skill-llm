FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    pandoc \
    libreoffice \
    poppler-utils \
    gcc \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

RUN npm install -g docx

WORKDIR /app

RUN mkdir -p /app/scripts/office

RUN cat > /app/scripts/office/unpack.py << 'EOF'
#!/usr/bin/env python3
import sys
import zipfile
import os

def unpack_docx(docx_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python unpack.py <docx_file> <output_dir>")
        sys.exit(1)
    unpack_docx(sys.argv[1], sys.argv[2])
EOF

RUN cat > /app/scripts/office/pack.py << 'EOF'
#!/usr/bin/env python3
import sys
import zipfile
import os

def pack_docx(input_dir, output_path, original_path=None):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, input_dir)
                zip_ref.write(file_path, arc_name)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pack.py <input_dir> <output_docx> [--original <original_file>]")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_path = sys.argv[2]
    original_path = None
    
    if len(sys.argv) > 4 and sys.argv[3] == '--original':
        original_path = sys.argv[4]
    
    pack_docx(input_dir, output_path, original_path)
EOF

RUN chmod +x /app/scripts/office/unpack.py /app/scripts/office/pack.py

RUN pip install --break-system-packages lxml beautifulsoup4 python-dateutil