#!/bin/bash

# Create the office scripts directory structure
mkdir -p scripts/office

# Create the validate.py script
cat > scripts/office/validate.py << 'EOF'
#!/usr/bin/env python3
import sys
import zipfile
import xml.etree.ElementTree as ET

def validate_docx(filepath):
    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            # Check for required files
            required_files = [
                '[Content_Types].xml',
                'word/document.xml',
                'word/_rels/document.xml.rels'
            ]
            
            for req_file in required_files:
                if req_file not in zf.namelist():
                    print(f"Missing required file: {req_file}")
                    return False
            
            # Try to parse document.xml
            doc_content = zf.read('word/document.xml')
            ET.fromstring(doc_content)
            
        print("Document validation passed")
        return True
    except Exception as e:
        print(f"Validation failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate.py <docx_file>")
        sys.exit(1)
    
    success = validate_docx(sys.argv[1])
    sys.exit(0 if success else 1)
EOF

chmod +x scripts/office/validate.py