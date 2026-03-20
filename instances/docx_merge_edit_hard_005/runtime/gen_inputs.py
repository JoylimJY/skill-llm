import os
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import random

# Set deterministic seed
random.seed(42)

# Create report_draft.docx (base document)
doc1 = Document()
doc1.add_heading('Annual Performance Report 2024', 0)
doc1.add_paragraph('This report summarizes our company performance for fiscal year 2024.')

# Add some content with marker text for verification
section1 = doc1.add_heading('Financial Overview', level=1)
p1 = doc1.add_paragraph('Revenue for 2024 reached $50 million, representing a 15% increase from the previous year. ')
p1.add_run('MARKER_DRAFT_REVENUE_DATA').bold = True
p1.add_run(' The growth was driven primarily by expansion into new markets.')

section2 = doc1.add_heading('Operations Summary', level=1)
p2 = doc1.add_paragraph('Our operational efficiency improved significantly with the implementation of new processes. ')
p2.add_run('MARKER_DRAFT_OPERATIONS_TEXT').italic = True
p2.add_run(' Employee satisfaction scores increased by 12%.')

section3 = doc1.add_heading('Future Outlook', level=1)
doc1.add_paragraph('Looking ahead to 2025, we anticipate continued growth in all sectors. Key initiatives include digital transformation and sustainability programs.')

doc1.save('report_draft.docx')

# Create legal_review.docx with tracked changes simulation
doc2 = Document()
doc2.add_heading('Legal Review Comments', 0)
doc2.add_paragraph('The following items require attention:')

# Simulate legal review content
review_para1 = doc2.add_paragraph('Revenue disclosure: The $50 million figure needs clarification regarding ')
review_para1.add_run('MARKER_LEGAL_REVENUE_CHANGE').bold = True
review_para1.add_run(' accounting methods used. Suggest changing to "approximately $50 million" for accuracy.')

review_para2 = doc2.add_paragraph('Operations section: The efficiency claims require supporting documentation. ')
review_para2.add_run('MARKER_LEGAL_OPERATIONS_COMMENT').underline = True
review_para2.add_run(' Recommend adding footnote referencing internal audit report.')

review_para3 = doc2.add_paragraph('Risk disclosure: Document lacks required risk factors section. ')
review_para3.add_run('MARKER_LEGAL_RISK_ADDITION').bold = True
review_para3.add_run(' Must add before final publication per compliance requirements.')

doc2.save('legal_review.docx')

# Create executive_summary.docx
doc3 = Document()
doc3.add_heading('Executive Summary', 0)
summary_para = doc3.add_paragraph('This executive summary provides key highlights from our 2024 annual report. ')
summary_para.add_run('MARKER_EXECUTIVE_SUMMARY_KEY').bold = True
summary_para.add_run(' Our organization achieved record performance across multiple metrics.')

doc3.add_paragraph('Key achievements include:')
bullet_list = doc3.add_paragraph('• Revenue growth of 15% year-over-year', style='List Bullet')
doc3.add_paragraph('• Successful market expansion initiatives', style='List Bullet')
doc3.add_paragraph('• Enhanced operational efficiency measures', style='List Bullet')
doc3.add_paragraph('• Improved employee satisfaction metrics', style='List Bullet')

conclusion = doc3.add_paragraph('These results position us well for continued success in 2025. ')
conclusion.add_run('MARKER_EXECUTIVE_CONCLUSION').italic = True

doc3.save('executive_summary.docx')

print('Generated input files: report_draft.docx, legal_review.docx, executive_summary.docx')