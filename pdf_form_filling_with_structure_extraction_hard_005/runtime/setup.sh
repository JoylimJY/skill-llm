#!/bin/bash
mkdir -p /workspace/scripts
cat > /workspace/scripts/extract_form_structure.py << 'EOF'
import json
import sys
from pypdf import PdfReader

def extract_form_structure(pdf_path, output_json):
    reader = PdfReader(pdf_path)
    page = reader.pages[0]
    
    # Extract text with coordinates
    text_elements = []
    if hasattr(page, '/Contents'):
        try:
            from pdfplumber import open as pdfopen
            with pdfopen(pdf_path) as pdf:
                p = pdf.pages[0]
                chars = p.chars
                for char in chars:
                    text_elements.append({
                        'text': char['text'],
                        'x0': char['x0'],
                        'top': char['top'],
                        'x1': char['x1'],
                        'bottom': char['bottom']
                    })
        except:
            pass
    
    # Group characters into labels
    labels = []
    current_label = {'text': '', 'x0': 0, 'top': 0, 'x1': 0, 'bottom': 0}
    
    for elem in sorted(text_elements, key=lambda x: (x['top'], x['x0'])):
        if abs(elem['top'] - current_label['top']) < 5 and elem['x0'] - current_label['x1'] < 10:
            current_label['text'] += elem['text']
            current_label['x1'] = elem['x1']
        else:
            if current_label['text'].strip():
                labels.append(current_label)
            current_label = elem.copy()
            current_label['text'] = elem['text']
    
    if current_label['text'].strip():
        labels.append(current_label)
    
    # Detect checkboxes (small rectangles)
    checkboxes = []
    # Simplified: assume checkboxes are at known positions
    checkboxes.append({'x0': 145, 'top': 522, 'x1': 160, 'bottom': 537})
    checkboxes.append({'x0': 145, 'top': 502, 'x1': 160, 'bottom': 517})
    checkboxes.append({'x0': 145, 'top': 482, 'x1': 160, 'bottom': 497})
    
    structure = {
        'labels': labels,
        'checkboxes': checkboxes,
        'lines': []
    }
    
    with open(output_json, 'w') as f:
        json.dump(structure, f, indent=2)

if __name__ == '__main__':
    extract_form_structure(sys.argv[1], sys.argv[2])
EOF

cat > /workspace/scripts/fill_pdf_form_with_annotations.py << 'EOF'
import json
import sys
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

def fill_pdf_form(input_pdf, fields_json, output_pdf):
    with open(fields_json, 'r') as f:
        fields_data = json.load(f)
    
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    # Create overlay with filled text
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    for field in fields_data.get('form_fields', []):
        page_num = field['page_number'] - 1
        entry_box = field['entry_bounding_box']
        text = field['entry_text']['text']
        font_size = field['entry_text'].get('font_size', 10)
        
        # Convert PDF coordinates to canvas coordinates
        x = entry_box[0]
        y = letter[1] - entry_box[3]
        
        can.setFont('Helvetica', font_size)
        can.drawString(x + 2, y + 2, text)
    
    can.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    
    # Merge overlay with original
    for i, page in enumerate(reader.pages):
        if i < len(overlay.pages):
            page.merge_page(overlay.pages[i])
        writer.add_page(page)
    
    with open(output_pdf, 'wb') as f:
        writer.write(f)

if __name__ == '__main__':
    fill_pdf_form(sys.argv[1], sys.argv[2], sys.argv[3])
EOF

chmod +x /workspace/scripts/*.py
