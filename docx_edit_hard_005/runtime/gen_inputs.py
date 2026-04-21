#!/usr/bin/env python3
import os
from docx import Document
from docx.shared import Inches
from datetime import datetime

# Create a document with tracked changes from multiple authors
doc = Document()

# Add title
title = doc.add_paragraph()
title_run = title.add_run('Q4 2024 Sales Report')
title_run.bold = True
title_run.font.size = Inches(0.2)

# Add first paragraph with marker text for comment target
first_para = doc.add_paragraph('Our sales performance this quarter exceeded expectations with a 15% increase over Q3. The team successfully launched three new product lines and expanded into two additional markets.')

# Add some content paragraphs
doc.add_paragraph('Key achievements include:')
bullet1 = doc.add_paragraph('• Revenue growth of $2.3M')
bullet2 = doc.add_paragraph('• Customer acquisition increased by 25%')
bullet3 = doc.add_paragraph('• Product launch success rate of 90%')

# Add a conclusion paragraph
concl_para = doc.add_paragraph('Looking forward, we anticipate continued growth in Q1 2025 based on current pipeline data and market trends.')

# Save the base document first
doc.save('sales_report.docx')

# Now we need to manually create the tracked changes XML
# Since python-docx doesn't support creating tracked changes, we'll create a simple document
# and then use the office scripts to add tracked changes via XML manipulation

print('Base document created: sales_report.docx')
print('Document contains:')
print('- Title: Q4 2024 Sales Report')
print('- First paragraph with marker text for commenting')
print('- Bullet points with key achievements')
print('- Conclusion paragraph')
print('Note: Tracked changes will be added via XML manipulation in the task solution')