#!/usr/bin/env python3
import os
import subprocess
import tempfile
from pathlib import Path

def create_base_document():
    js_code = '''
const { Document, Packer, Paragraph, TextRun, HeadingLevel } = require('docx');
const fs = require('fs');

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Service Agreement")] }),
      new Paragraph({ children: [new TextRun("This agreement is entered into between the parties for professional services.")] }),
      new Paragraph({ children: [new TextRun("The term of this agreement shall be 12 months from the effective date.")] }),
      new Paragraph({ children: [new TextRun("Payment terms require net 30 days from invoice date.")] }),
      new Paragraph({ children: [new TextRun("Either party may terminate with 30 days written notice.")] }),
      new Paragraph({ children: [new TextRun("This contract is governed by California state law.")] }),
      new Paragraph({ children: [new TextRun("All disputes will be resolved through binding arbitration.")] })
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => fs.writeFileSync("base_contract.docx", buffer));
    '''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(js_code)
        js_file = f.name
    
    subprocess.run(['node', js_file], check=True)
    os.unlink(js_file)

def add_tracked_changes(input_file, output_file, author, changes):
    # Unpack document
    subprocess.run(['python', '/app/scripts/office/unpack.py', input_file, 'temp_unpacked'], check=True)
    
    # Read document.xml
    with open('temp_unpacked/word/document.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply changes based on author
    change_id = 1
    date = "2024-12-15T10:00:00Z"
    
    for old_text, new_text, change_type in changes:
        if change_type == 'replace':
            if old_text in content:
                # Find the text within w:t tags
                import re
                pattern = f'<w:t[^>]*>{re.escape(old_text)}</w:t>'
                if re.search(pattern, content):
                    replacement = f'''<w:del w:id="{change_id}" w:author="{author}" w:date="{date}">
                        <w:r><w:delText>{old_text}</w:delText></w:r>
                    </w:del>
                    <w:ins w:id="{change_id+1}" w:author="{author}" w:date="{date}">
                        <w:r><w:t>{new_text}</w:t></w:r>
                    </w:ins>'''
                    content = re.sub(pattern, replacement, content, count=1)
                    change_id += 2
        elif change_type == 'delete':
            if old_text in content:
                import re
                pattern = f'<w:t[^>]*>{re.escape(old_text)}</w:t>'
                if re.search(pattern, content):
                    replacement = f'''<w:del w:id="{change_id}" w:author="{author}" w:date="{date}">
                        <w:r><w:delText>{old_text}</w:delText></w:r>
                    </w:del>'''
                    content = re.sub(pattern, replacement, content, count=1)
                    change_id += 1
        elif change_type == 'insert':
            # Insert after old_text
            if old_text in content:
                import re
                pattern = f'(<w:t[^>]*>{re.escape(old_text)}</w:t>)'
                if re.search(pattern, content):
                    replacement = f'''\\1<w:ins w:id="{change_id}" w:author="{author}" w:date="{date}">
                        <w:r><w:t> {new_text}</w:t></w:r>
                    </w:ins>'''
                    content = re.sub(pattern, replacement, content, count=1)
                    change_id += 1
    
    # Write back
    with open('temp_unpacked/word/document.xml', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Pack document
    subprocess.run(['python', '/app/scripts/office/pack.py', 'temp_unpacked', output_file, '--original', input_file], check=True)
    
    # Clean up
    subprocess.run(['rm', '-rf', 'temp_unpacked'], check=True)

# Create base document
create_base_document()

# Sarah Chen's changes - grammar and clarity improvements
sarah_changes = [
    ('professional services', 'consulting services', 'replace'),
    ('12 months', '12 (twelve) months', 'replace'),
    ('net 30 days', 'net thirty (30) days', 'replace')
]
add_tracked_changes('base_contract.docx', 'contract_v1_sarah.docx', 'Sarah Chen', sarah_changes)

# Mike Rodriguez's changes - business terms
mike_changes = [
    ('30 days written notice', '60 days written notice', 'replace'),
    ('California state law', 'Delaware state law', 'replace')
]
add_tracked_changes('contract_v1_sarah.docx', 'contract_v2_mike.docx', 'Mike Rodriguez', mike_changes)

# Legal Team changes - additions and deletions
legal_changes = [
    ('binding arbitration', '', 'delete'),  # This deletion should be accepted
    ('Either party may terminate with', 'Additional termination fees may apply.', 'insert'),  # This insertion should be rejected
    ('governed by', 'subject to confidentiality clauses and governed by', 'insert')  # This insertion should be rejected
]
add_tracked_changes('contract_v2_mike.docx', 'contract_v3_legal.docx', 'Legal Team', legal_changes)

# temp_reviewer changes - should all be rejected
temp_changes = [
    ('Service Agreement', 'Temporary Service Agreement', 'replace'),
    ('effective date', 'start date', 'replace')
]
add_tracked_changes('contract_v3_legal.docx', 'contract_v4_temp.docx', 'temp_reviewer', temp_changes)

print("Generated contract documents with tracked changes from multiple reviewers")
