#!/usr/bin/env python3
import os
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Create a simple contract document with markers
doc = Document()

# Add title
title = doc.add_paragraph()
title_run = title.add_run('SERVICE AGREEMENT')
title_run.bold = True
title_run.font.size = Pt(14)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Add company name section
company_para = doc.add_paragraph()
company_para.add_run('This agreement is entered into between Acme Corp and the Client.')

# Add payment terms section with marker
payment_heading = doc.add_paragraph()
payment_heading_run = payment_heading.add_run('Payment Terms')
payment_heading_run.bold = True

payment_para = doc.add_paragraph()
payment_para.add_run('Payment must be received within thirty (30) days of invoice date. Acme Corp reserves the right to charge late fees.')

# Add another reference to company name
footer_para = doc.add_paragraph()
footer_para.add_run('For questions, contact Acme Corp support team.')

# Save the document
doc.save('contract.docx')
print('Generated contract.docx')
